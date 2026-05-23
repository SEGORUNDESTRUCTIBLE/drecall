"""Bootstrap runtime memory from persisted sources and local snapshots."""

from __future__ import annotations

import json
import logging
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from config.settings import get_settings
from core.runtime.state_manager import RuntimeState
from core.schemas import RecallItem

logger = logging.getLogger("drecall.runtime_loader")


class RuntimeLoader:
    """Loader for persistent memory state and Notion-backed runtime bootstrap."""

    def __init__(
        self,
        persistence_sink: Optional[Any] = None,
        notion_fetcher: Optional[Any] = None,
        snapshot_path: Optional[Path] = None,
        memory_limit: int = 2000,
    ) -> None:
        self.persistence_sink = persistence_sink
        self.notion_fetcher = notion_fetcher
        self.settings = get_settings()
        self.snapshot_path = Path(snapshot_path or self.settings.temp_dir / "runtime_snapshot.json")
        self.memory_limit = memory_limit
        self.snapshot_path.parent.mkdir(parents=True, exist_ok=True)

    def load_runtime(
        self,
        load_from_notion: bool = True,
        force_refresh: bool = False,
    ) -> RuntimeState:
        snapshot_items = []
        loaded_from_snapshot = False
        if self.snapshot_path.exists() and not force_refresh:
            snapshot_items = self._load_snapshot()
            loaded_from_snapshot = bool(snapshot_items)

        notion_items = []
        loaded_from_notion = False
        if load_from_notion and self._notion_enabled():
            try:
                notion_items = self._load_from_notion()
                loaded_from_notion = bool(notion_items)
            except Exception as exc:
                logger.warning("Notion sync failed during startup: %s", exc)
                loaded_from_notion = False

        items = self._merge_items(snapshot_items, notion_items)
        if self.memory_limit and len(items) > self.memory_limit:
            items = sorted(items, key=lambda item: item.updated_at, reverse=True)[: self.memory_limit]

        state = RuntimeState.from_items(
            items,
            sync_metadata={
                "loaded_from_snapshot": loaded_from_snapshot,
                "loaded_from_notion": loaded_from_notion,
                "snapshot_path": str(self.snapshot_path),
                "last_sync_at": datetime.now(timezone.utc).isoformat(),
                "sync_status": "loaded",
            },
        )

        try:
            self._save_snapshot(state)
        except Exception as exc:
            logger.warning("Failed to persist runtime snapshot on startup: %s", exc)

        return state

    def _load_snapshot(self) -> List[RecallItem]:
        try:
            raw = json.loads(self.snapshot_path.read_text(encoding="utf-8"))
            items = raw.get("items") if isinstance(raw, dict) else raw
            if not isinstance(items, list):
                raise ValueError("Snapshot payload malformed")
            recall_items: List[RecallItem] = []
            for entry in items:
                if isinstance(entry, dict):
                    recall_items.append(RecallItem.model_validate(entry))
            logger.info("Loaded %d items from runtime snapshot %s", len(recall_items), self.snapshot_path)
            return recall_items
        except Exception as exc:
            backup_path = self.snapshot_path.with_suffix(self.snapshot_path.suffix + ".corrupt")
            try:
                shutil.move(str(self.snapshot_path), str(backup_path))
                logger.warning("Corrupted runtime snapshot moved to %s", backup_path)
            except Exception:
                logger.warning("Failed to move corrupted snapshot file")
            logger.warning("Failed to load runtime snapshot: %s", exc)
            return []

    def _load_from_notion(self) -> List[RecallItem]:
        fetcher = self.notion_fetcher or self._create_notion_fetcher()
        if fetcher is None:
            raise RuntimeError("Notion fetcher unavailable")

        pages: List[Dict[str, Any]] = []
        cursor: Optional[str] = None
        attempt = 1
        while True:
            try:
                response = fetcher.fetch_pages(limit=50, start_cursor=cursor)
            except Exception as exc:
                if attempt >= self.settings.max_retries:
                    raise
                wait = 0.5 * attempt
                logger.warning("Notion page fetch failed on attempt %d: %s", attempt, exc)
                time.sleep(wait)
                attempt += 1
                continue

            if not isinstance(response, dict):
                response = {"results": response}

            results = response.get("results", [])
            pages.extend(results)
            if response.get("has_more") and response.get("next_cursor"):
                cursor = response.get("next_cursor")
                continue
            break

        recall_items: List[RecallItem] = []
        for page in pages:
            item = self._page_to_recall_item(page)
            if item is not None:
                recall_items.append(item)
        logger.info("Loaded %d items from Notion persistence", len(recall_items))
        return recall_items

    def _merge_items(self, snapshot_items: List[RecallItem], notion_items: List[RecallItem]) -> List[RecallItem]:
        merged: Dict[str, RecallItem] = {}
        for item in snapshot_items:
            if item.id:
                merged[item.id] = item
            else:
                merged[f"snapshot-{len(merged)}"] = item

        for item in notion_items:
            if item.id:
                previous = merged.get(item.id)
                if previous:
                    merged[item.id] = self._merge_recall_items(previous, item)
                else:
                    merged[item.id] = item
            else:
                merged[f"notion-{len(merged)}"] = item

        return list(merged.values())

    def _merge_recall_items(self, original: RecallItem, updated: RecallItem) -> RecallItem:
        data = original.model_dump(mode="json")
        data.update({k: v for k, v in updated.model_dump(mode="json").items() if v not in (None, [], {}, "")})
        try:
            return RecallItem.model_validate(data)
        except Exception:
            return updated

    def _page_to_recall_item(self, page: Dict[str, Any]) -> Optional[RecallItem]:
        properties = page.get("properties", {}) if isinstance(page, dict) else {}
        normalized: Dict[str, Any] = {}

        for prop_name, prop_value in properties.items():
            key = self._normalize_label(prop_name)
            normalized[key] = self._parse_property(prop_value)

        item_data: Dict[str, Any] = {
            "id": page.get("id"),
            "title": normalized.get("title") or normalized.get("name") or "Untitled",
            "content": normalized.get("content") or normalized.get("notes") or normalized.get("body") or "",
            "source": normalized.get("source"),
            "tags": normalized.get("tags") or [],
            "subject": normalized.get("subject"),
            "system": normalized.get("system"),
            "error_type": normalized.get("error_type"),
            "pattern_type": normalized.get("pattern_type"),
            "difficulty": normalized.get("difficulty"),
            "recall_priority": normalized.get("recall_priority"),
            "revision_metadata": normalized.get("revision_metadata") or {},
            "duplicate_fingerprint": normalized.get("duplicate_fingerprint"),
            "embedding_metadata": normalized.get("embedding_metadata") or {},
            "metadata": normalized.get("metadata") or {},
            "created_at": page.get("created_time"),
            "updated_at": page.get("last_edited_time"),
            "notion_page_id": page.get("id"),
        }

        if self.settings.notion_datasource_id:
            item_data.setdefault("datasource_id", self.settings.notion_datasource_id)
        elif self.settings.notion_database_id:
            item_data.setdefault("datasource_id", self.settings.notion_database_id)

        try:
            return RecallItem.model_validate(item_data)
        except Exception as exc:
            logger.warning("Unable to validate persisted Notion item %s: %s", item_data.get("id"), exc)
            return None

    def _parse_property(self, prop_value: Any) -> Any:
        if not isinstance(prop_value, dict):
            return prop_value
        prop_type = prop_value.get("type")
        if prop_type == "title":
            return self._join_plain_text(prop_value.get("title", []))
        if prop_type == "rich_text":
            return self._try_parse_json(self._join_plain_text(prop_value.get("rich_text", [])))
        if prop_type == "multi_select":
            return [entry.get("name") for entry in prop_value.get("multi_select", []) if entry.get("name")]
        if prop_type == "select":
            selected = prop_value.get("select")
            return selected.get("name") if selected else None
        if prop_type == "checkbox":
            return bool(prop_value.get("checkbox"))
        if prop_type == "number":
            return prop_value.get("number")
        if prop_type == "date":
            return prop_value.get("date", {}).get("start")
        if prop_type == "people":
            return [person.get("name") for person in prop_value.get("people", []) if person.get("name")]
        if prop_type == "url":
            return prop_value.get("url")
        if prop_type == "email":
            return prop_value.get("email")
        if prop_type == "phone_number":
            return prop_value.get("phone_number")
        if prop_type in {"created_time", "last_edited_time"}:
            return prop_value.get(prop_type)

        text_value = self._join_plain_text(prop_value.get(prop_type, [])) if isinstance(prop_value.get(prop_type), list) else None
        return self._try_parse_json(text_value) if text_value is not None else prop_value

    @staticmethod
    def _join_plain_text(elements: List[dict]) -> str:
        return "".join(str(segment.get("plain_text", "")) for segment in elements)

    @staticmethod
    def _try_parse_json(value: Optional[str]) -> Any:
        if not isinstance(value, str):
            return value
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value

    @staticmethod
    def _normalize_label(value: str) -> str:
        return value.strip().lower().replace(" ", "_")

    def _create_notion_fetcher(self) -> Optional[Any]:
        if self.notion_fetcher is not None:
            return self.notion_fetcher
        try:
            from notion.notion_fetcher import NotionFetcher

            return NotionFetcher()
        except Exception as exc:
            logger.warning("Unable to initialize NotionFetcher: %s", exc)
            return None

    def _notion_enabled(self) -> bool:
        return bool(self.notion_fetcher or self.settings.enable_notion)

    def _atomic_write(self, path: Path, payload: Dict[str, Any]) -> None:
        temp_path = path.with_suffix(path.suffix + ".tmp")
        temp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        temp_path.replace(path)

    def _save_snapshot(self, state: RuntimeState) -> None:
        payload = state.to_snapshot()
        payload["sync_metadata"]["last_saved_at"] = datetime.now(timezone.utc).isoformat()
        self._atomic_write(self.snapshot_path, payload)
