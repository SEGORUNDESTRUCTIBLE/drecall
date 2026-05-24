"""Helper utilities to validate and inspect Notion persistence configuration.

Provides safe, read-only inspection of Notion databases and a small
test-persistence helper to validate end-to-end persistence without
silently mutating user databases.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

from config.settings import get_settings
from notion.datasource_registry import resolve_datasource_alias

logger = logging.getLogger("drecall.notion_manager")


class NotionEnvStatus:
    def __init__(self, enabled: bool, token_present: bool, database_id: Optional[str], datasource_id: Optional[str]):
        self.enabled = enabled
        self.token_present = token_present
        self.database_id = database_id
        self.datasource_id = datasource_id


class NotionManager:
    @staticmethod
    def detect_env() -> NotionEnvStatus:
        env = os.environ
        settings = get_settings()

        enabled = str(env.get("ENABLE_NOTION", "false")).lower() in ("1", "true", "yes", "on")
        enabled = enabled or bool(settings.enable_notion)

        token_present = bool(env.get("NOTION_TOKEN") or env.get("NOTION_API_KEY"))
        token_present = token_present or bool(settings.notion_api_key)

        database_id = env.get("NOTION_DATABASE_ID") or settings.notion_database_id or None
        datasource_id = env.get("NOTION_DATASOURCE_ID") or settings.notion_datasource_id or None

        return NotionEnvStatus(enabled=enabled, token_present=token_present, database_id=database_id, datasource_id=datasource_id)

    @staticmethod
    def init_client() -> Optional[Any]:
        try:
            from notion_client import Client as NotionClient
        except Exception:
            logger.warning("notion-client package not available. Install notion-client to enable persistence")
            return None
        token = os.environ.get("NOTION_TOKEN") or os.environ.get("NOTION_API_KEY")
        if not token:
            logger.warning("Notion token is not configured in environment")
            return None
        try:
            client = NotionClient(auth=token)
            # quick test: list capabilities via retrieving a user or simple call
            return client
        except Exception as exc:
            logger.warning("Failed to initialize Notion client: %s", exc)
            return None

    @staticmethod
    def describe_configuration(datasource_map: Optional[Dict[str, Any]] = None) -> str:
        """Return a short diagnostic summary of Notion-related configuration."""
        settings = get_settings()
        datasource_map = datasource_map or {}

        lines = []
        lines.append("Notion startup configuration:")
        lines.append(f"  persistence_enabled={settings.enable_notion}")
        lines.append(f"  notion_api_key_present={bool(settings.notion_api_key)}")
        lines.append(f"  notion_database_id={settings.notion_database_id}")
        lines.append(f"  notion_datasource_id={settings.notion_datasource_id}")

        if datasource_map:
            lines.append("  datasources:")
            for alias in sorted(datasource_map.keys()):
                try:
                    resolved = resolve_datasource_alias(alias, datasource_map=datasource_map)
                    lines.append(
                        f"    - {alias}: database_id={resolved.get('database_id') or 'None'} "
                        f"data_source_id={resolved.get('data_source_id') or 'None'}"
                    )
                except Exception as exc:
                    lines.append(f"    - {alias}: UNRESOLVED ({exc})")
        else:
            lines.append("  datasources: none configured")
            try:
                resolved_default = resolve_datasource_alias("notion_default", datasource_map=datasource_map)
                lines.append(
                    f"  notion_default (env): database_id={resolved_default.get('database_id') or 'None'} "
                    f"data_source_id={resolved_default.get('data_source_id') or 'None'}"
                )
            except Exception as exc:
                lines.append(f"  notion_default (env): UNRESOLVED ({exc})")

        summary = "\n".join(lines)
        return summary

    @staticmethod
    @staticmethod
    def _get_title_property_name(properties: Dict[str, Any]) -> str:
        for prop_name, prop_def in (properties or {}).items():
            if prop_def.get("type") == "title":
                return prop_name
        return "Title"

    @staticmethod
    def _resolve_database_data_source(client: Any, database_id: str) -> Dict[str, Any]:
        try:
            db = client.databases.retrieve(database_id=database_id)
            for data_source in db.get("data_sources", []) or []:
                ds_id = data_source.get("id")
                if ds_id:
                    ds_obj = client.data_sources.retrieve(data_source_id=ds_id)
                    return {
                        "data_source_id": ds_id,
                        "properties": ds_obj.get("properties", {}) or {},
                    }
        except Exception:
            logger.exception("Failed to resolve data source for database %s", database_id)
        return {}

    @staticmethod
    def validate_database_access(client: Any, database_id: str) -> Dict[str, Any]:
        """Validate that the integration can access the database and return simple schema info.

        Returns a dict with keys: exists(bool), title(str), properties(dict), accessible(bool), error(optional)
        """
        if client is None:
            return {"exists": False, "accessible": False, "error": "no_client"}

        try:
            db = client.databases.retrieve(database_id=database_id)
            title = None
            try:
                title = " ".join([t.get("plain_text", "") for t in db.get("title", [])])
            except Exception:
                title = str(db.get("id"))
            props = db.get("properties", {}) or {}
            data_source_id = None
            if not props:
                data_source_info = NotionManager._resolve_database_data_source(client, database_id)
                props = data_source_info.get("properties", {}) or {}
                data_source_id = data_source_info.get("data_source_id")
            return {
                "exists": True,
                "accessible": True,
                "title": title,
                "properties": props,
                "data_source_id": data_source_id,
            }
        except Exception as exc:
            logger.warning("Database access validation failed: %s", exc)
            return {"exists": False, "accessible": False, "error": str(exc)}

    @staticmethod
    def validate_datasource_access(client: Any, data_source_id: str) -> Dict[str, Any]:
        """Validate a Notion data source id and derive the related database schema."""
        if client is None:
            return {"exists": False, "accessible": False, "error": "no_client"}

        try:
            ds = client.data_sources.retrieve(data_source_id=data_source_id)
            title = None
            try:
                title = " ".join([t.get("plain_text", "") for t in ds.get("title", [])])
            except Exception:
                title = str(ds.get("id"))
            props = ds.get("properties", {}) or {}
            database_id = None
            parent = ds.get("parent", {}) or {}
            if parent.get("type") == "database_id":
                database_id = parent.get("database_id")
            return {
                "exists": True,
                "accessible": True,
                "title": title,
                "properties": props,
                "database_id": database_id,
            }
        except Exception as exc:
            logger.warning("Datasource access validation failed: %s", exc)
            return {"exists": False, "accessible": False, "error": str(exc)}

    @staticmethod
    def is_sandbox_name(name: Optional[str]) -> bool:
        if not name:
            return False
        lowered = name.lower()
        return "test" in lowered or "sandbox" in lowered or "dev" in lowered

    @staticmethod
    def inspect_schema(properties: Dict[str, Any]) -> Dict[str, Any]:
        """Return a compact compatibility report for mapping canonical fields to database properties."""
        canonical = [
            "title",
            "content",
            "tags",
            "subject",
            "system",
            "revision_metadata",
            "duplicate_fingerprint",
            "recall_priority",
        ]
        found = {k: None for k in canonical}
        for prop_name, prop_def in (properties or {}).items():
            pn = prop_name.lower()
            for c in canonical:
                if c in pn or (c == "title" and prop_def.get("type") == "title"):
                    found[c] = prop_name
        missing = [k for k, v in found.items() if v is None]
        return {"mapping": found, "missing": missing, "property_count": len(properties or {})}

    @staticmethod
    def safe_create_test_page(client: Any, database_id: str, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a test page in the given Notion database; caller must confirm sandbox.

        Returns created page dict or None.
        """
        if client is None:
            return None
        try:
            db = client.databases.retrieve(database_id=database_id)
            properties = db.get("properties", {}) or {}
            if not properties:
                ds_info = NotionManager._resolve_database_data_source(client, database_id)
                properties = ds_info.get("properties", {}) or {}
            title_field = NotionManager._get_title_property_name(properties)
            parent = {"database_id": database_id}
            props = {title_field: {"title": [{"text": {"content": item.get("title", "dRecall Test")}}]}}
            children = [{"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": item.get("content", "test")}}]}}]
            resp = client.pages.create(parent=parent, properties=props, children=children)
            return resp
        except Exception as exc:
            logger.warning("Test page creation failed: %s", exc)
            return None
