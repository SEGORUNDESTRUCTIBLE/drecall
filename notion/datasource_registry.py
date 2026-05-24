"""Datasource registry and resolver for Notion datasource aliases.

Provides a small utility to resolve logical aliases (e.g. "notion_default")
to actual Notion `database_id` or `data_source_id` UUIDs using the
configured `datasource_map`, environment-backed settings, or simple UUID
validation. This avoids passing internal aliases directly to the Notion API.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional
import uuid

from config.settings import settings as app_settings

logger = logging.getLogger("drecall.datasource_registry")


def _is_uuid(val: Optional[str]) -> bool:
    if not val or not isinstance(val, str):
        return False
    try:
        uuid.UUID(val)
        return True
    except Exception:
        return False


def resolve_datasource_alias(
    alias_or_id: str,
    datasource_map: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Dict[str, Optional[str]]:
    """Resolve an alias or id to a mapping with keys `database_id` and `data_source_id`.

    Resolution order:
    1. If alias_or_id exists in datasource_map and contains valid ids, return them.
    2. If alias_or_id is itself a valid UUID, treat it as a database_id and return it.
    3. If alias_or_id is a recognised default alias ("default", "notion_default"),
       fall back to values supplied via `config.settings` (NOTION_DATABASE_ID or NOTION_DATASOURCE_ID).
    4. Otherwise raise ValueError indicating unresolved alias.
    """
    datasource_map = datasource_map or {}

    # 1) explicit mapping
    # Accept explicit mapping entries even when the contained IDs are not strict UUIDs
    # (tests and some environments may use logical IDs). If a mapping exists, return it.
    mapping = datasource_map.get(alias_or_id)
    if mapping is not None:
        db = mapping.get("database_id")
        ds = mapping.get("data_source_id")
        # If mapping explicitly specifies values (even non-UUID), prefer them.
        if db or ds:
            return {"database_id": db, "data_source_id": ds}
        # If mapping is present but empty, treat the alias itself as the database id
        return {"database_id": alias_or_id, "data_source_id": None}

    # 2) if it's a UUID, assume it's a database id
    if _is_uuid(alias_or_id):
        return {"database_id": alias_or_id, "data_source_id": None}

    # 3) check settings for default aliases
    if alias_or_id in ("default", "notion_default"):
        if _is_uuid(app_settings.notion_database_id):
            return {"database_id": app_settings.notion_database_id, "data_source_id": None}
        if _is_uuid(app_settings.notion_datasource_id):
            return {"database_id": None, "data_source_id": app_settings.notion_datasource_id}

    # unresolved
    raise ValueError(f"Unresolved Notion datasource alias or id: {alias_or_id}")


def summarize_registry(datasource_map: Optional[Dict[str, Dict[str, Any]]] = None) -> str:
    """Return a short human-readable summary of resolved datasources for diagnostics."""
    lines = []
    datasource_map = datasource_map or {}
    if not datasource_map:
        lines.append("No datasources configured in datasource_map.")
    for alias, mapping in datasource_map.items():
        try:
            resolved = resolve_datasource_alias(alias, datasource_map=datasource_map)
            lines.append(f"{alias}: RESOLVED -> database_id={resolved.get('database_id') or resolved.get('data_source_id')}")
        except Exception as exc:
            lines.append(f"{alias}: UNRESOLVED ({exc})")

    # include environment-backed default
    try:
        default_res = resolve_datasource_alias("notion_default", datasource_map=datasource_map)
        lines.append(f"notion_default (env): {default_res.get('database_id') or default_res.get('data_source_id')}")
    except Exception:
        lines.append("notion_default (env): UNRESOLVED")

    return "\n".join(lines)
