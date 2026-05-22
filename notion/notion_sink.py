"""Notion persistence sink adapter implementing PersistenceSink contract.

This module provides a production-oriented but lightweight `NotionSink`
implementation that is intentionally decoupled from ingestion and provider
layers. It focuses on stable contracts, datasource-awareness, schema-safe
property mapping, block-building abstraction, and a simple retry model.

The implementation is synchronous and dependency-injectable (client,
mapper, validator). It is designed to be usable by queue workers and to be
replaced by async variants later.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from core.contracts.persistence_contracts import (
    PersistenceResult,
    PersistenceSink,
    PersistenceTransientError,
    PersistencePermanentError,
)


class NotionSinkError(PersistencePermanentError):
    pass


class NotionTransientError(PersistenceTransientError):
    pass


class DuplicatePersistenceError(PersistencePermanentError):
    pass


class SchemaMismatchError(PersistencePermanentError):
    pass


@dataclass
class DefaultPropertyMapper:
    """Map a canonical item dict into Notion `properties` payload.

    Datasource-aware: accepts an optional `mapping` where keys are datasource ids
    and values are mapping dicts. Each mapping dict maps canonical keys to a
    Notion property descriptor (simple abstraction used by this sink).
    """

    mapping: Dict[str, Dict[str, Any]] = None

    def map_properties(self, item: Dict[str, Any], datasource_id: Optional[str] = None) -> Dict[str, Any]:
        # choose mapping for datasource or fallback to default
        ds_map = (self.mapping or {}).get(datasource_id, {})

        properties: Dict[str, Any] = {}

        # Title handling: map `title` key to Notion title field
        title = item.get("title") or item.get("name") or ""
        properties[ds_map.get("title", "Title")] = {
            "title": [{"text": {"content": str(title)[:1900]}}]
        }

        # generic mapping for other keys: store as rich_text/select/multi_select
        for key, value in item.items():
            if key in ("title", "name", "datasource_id"):
                continue

            prop_name = ds_map.get("fields", {}).get(key, key)

            if isinstance(value, bool):
                properties[prop_name] = {"checkbox": bool(value)}
            elif isinstance(value, (int, float)):
                properties[prop_name] = {"number": value}
            elif isinstance(value, list):
                properties[prop_name] = {"multi_select": [{"name": str(v)} for v in value]}
            else:
                properties[prop_name] = {"rich_text": [{"text": {"content": str(value)[:1900]}}]}

        return properties


class DefaultBlockBuilder:
    """Build a simple Notion blocks list from a canonical payload."""

    def build_blocks(self, item: Dict[str, Any]) -> List[Dict[str, Any]]:
        blocks: List[Dict[str, Any]] = []
        content = item.get("content") or item.get("body")
        if content:
            # split into paragraphs
            for paragraph in str(content).split("\n\n"):
                blocks.append({"object": "block", "type": "paragraph", "paragraph": {"text": [{"type": "text", "text": {"content": paragraph[:2000]}}]}})

        # additional optional sections
        note = item.get("ai_note")
        if note:
            blocks.append({"object": "block", "type": "quote", "quote": {"text": [{"type": "text", "text": {"content": str(note)[:2000]}}]}})

        return blocks


class SimpleSchemaValidator:
    """Validate that minimal required keys exist and basic types match.

    Datasource-aware: accepts schema dicts keyed by datasource id. Each schema
    supports `required` list and optional `types` mapping.
    """

    def __init__(self, schemas: Optional[Dict[str, Dict[str, Any]]] = None) -> None:
        self.schemas = schemas or {}

    def validate(self, item: Dict[str, Any], datasource_id: Optional[str] = None) -> None:
        schema = self.schemas.get(datasource_id)
        if not schema:
            return

        required = schema.get("required", [])
        missing = [k for k in required if k not in item or item.get(k) in (None, "")]
        if missing:
            raise SchemaMismatchError(f"Missing required keys for datasource {datasource_id}: {missing}")

        types = schema.get("types", {})
        for key, expected in types.items():
            if key not in item:
                continue
            val = item[key]
            if expected == "str" and not isinstance(val, str):
                raise SchemaMismatchError(f"Field {key} expected str")


class NotionSink(PersistenceSink):
    """Persistence sink that writes canonical items to Notion.

    Constructor arguments are dependency-injected to avoid tight coupling
    and to support mocking in unit tests.
    """

    def __init__(
        self,
        client: Any = None,
        datasource_map: Optional[Dict[str, Dict[str, Any]]] = None,
        property_mapper: Optional[DefaultPropertyMapper] = None,
        block_builder: Optional[DefaultBlockBuilder] = None,
        schema_validator: Optional[SimpleSchemaValidator] = None,
        max_retries: int = 3,
        backoff_factor: float = 0.5,
    ) -> None:
        self.client = client
        self.datasource_map = datasource_map or {}
        self.property_mapper = property_mapper or DefaultPropertyMapper(mapping=self.datasource_map)
        self.block_builder = block_builder or DefaultBlockBuilder()
        self.schema_validator = schema_validator or SimpleSchemaValidator(schemas={})
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

    def _get_datasource_id(self, item: Dict[str, Any]) -> Optional[str]:
        # explicit datasource override in item, else use provided default mapping if single key
        ds = item.get("datasource_id") or item.get("source")
        if ds:
            return ds
        if len(self.datasource_map) == 1:
            return next(iter(self.datasource_map.keys()))
        return None

    def _retryable_call(self, func):
        last_exc = None
        for attempt in range(1, self.max_retries + 1):
            try:
                return func()
            except Exception as exc:
                last_exc = exc
                # heuristics: treat ConnectionError/TimeoutError as transient
                transient = isinstance(exc, (ConnectionError, TimeoutError)) or "rate limit" in str(exc).lower()
                if attempt == self.max_retries or not transient:
                    break
                sleep_time = self.backoff_factor * (2 ** (attempt - 1))
                time.sleep(sleep_time)

        # map final exception
        if isinstance(last_exc, (ConnectionError, TimeoutError)) or (last_exc and "rate limit" in str(last_exc).lower()):
            raise NotionTransientError(str(last_exc))
        raise NotionSinkError(str(last_exc))

    def create(self, item: Dict[str, Any]) -> PersistenceResult:
        # datasource awareness
        datasource_id = self._get_datasource_id(item)
        if datasource_id is None:
            raise PersistencePermanentError("No datasource_id provided and no default configured")

        # schema validation
        self.schema_validator.validate(item, datasource_id=datasource_id)

        # idempotency: use dedup_key if provided
        dedup_key = item.get("dedup_key") or f"title:{item.get('title','')}"

        if self.exists(dedup_key):
            raise DuplicatePersistenceError(f"Item with dedup_key {dedup_key} already exists")

        properties = self.property_mapper.map_properties(item, datasource_id=datasource_id)
        blocks = self.block_builder.build_blocks(item)

        parent = {"data_source_id": datasource_id}

        def _call():
            if not self.client:
                raise NotionSinkError("Notion client not configured")
            return self.client.pages.create(parent=parent, properties=properties, children=blocks)

        response = self._retryable_call(_call)

        page_id = str(response.get("id"))
        metadata = {"url": response.get("url"), "raw_response": response}

        return PersistenceResult(id=page_id, metadata=metadata)

    def update(self, item_id: str, patch: Dict[str, Any]) -> PersistenceResult:
        def _call():
            if not self.client:
                raise NotionSinkError("Notion client not configured")
            return self.client.pages.update(page_id=item_id, properties=patch)

        response = self._retryable_call(_call)
        return PersistenceResult(id=str(response.get("id")), metadata={"raw_response": response})

    def exists(self, dedup_key: str) -> bool:
        # Best-effort existence using client.search if available
        if not self.client:
            return False

        try:
            res = self.client.search(query=dedup_key)
            # interface: return dict with "results"
            results = res.get("results") if isinstance(res, dict) else []
            return bool(results)
        except Exception:
            # don't fail pipeline on search; conservative False
            return False

    def query_similar(self, text: str, limit: int = 10):
        if not self.client:
            return []

        try:
            res = self.client.search(query=text)
            return res.get("results", [])[:limit]
        except Exception:
            return []

    # convenience retrieval
    def retrieve_page(self, page_id: str) -> Dict[str, Any]:
        def _call():
            if not self.client:
                raise NotionSinkError("Notion client not configured")
            return self.client.pages.retrieve(page_id=page_id)

        return self._retryable_call(_call)
