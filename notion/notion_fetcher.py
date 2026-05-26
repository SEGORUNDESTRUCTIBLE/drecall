"""Utilities for fetching Notion pages and metadata for duplicate detection."""

import logging
from typing import Optional, Dict, Any, List

from config import get_settings
from .notion_client import NotionClientWrapper


def _normalize_id(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    candidate = str(value).strip()
    return candidate if candidate else None

logger = logging.getLogger(__name__)


class NotionFetcher:
    def __init__(self, client: Optional[NotionClientWrapper] = None, database_id: Optional[str] = None):
        self.client = client or NotionClientWrapper()
        active_settings = get_settings()

        resolved_datasource = _normalize_id(active_settings.notion_datasource_id)
        resolved_database = _normalize_id(database_id or active_settings.notion_database_id)

        if resolved_datasource:
            self.target_id = resolved_datasource
            self.datasource_mode = True
            if resolved_database:
                logger.info("Using NOTION_DATASOURCE_ID because datasource config is present")
        else:
            self.target_id = resolved_database
            self.datasource_mode = False
            if resolved_database:
                logger.warning("Legacy NOTION_DATABASE_ID detected; consider migrating to NOTION_DATASOURCE_ID")

    def fetch_pages(self, limit: int = 50, start_cursor: Optional[str] = None) -> Dict[str, Any]:
        if not self.target_id:
            raise ValueError("No database/datasource id configured for fetching pages")
        try:
            if self.datasource_mode:
                params = {"page_size": limit}
                if start_cursor:
                    params["start_cursor"] = start_cursor
                res = self.client.query_data_source(data_source_id=self.target_id, **params)
            else:
                params = {"database_id": self.target_id, "page_size": limit}
                if start_cursor:
                    params["start_cursor"] = start_cursor
                try:
                    res = self.client.query_database(**params)
                except Exception as exc:
                    logger.warning("Database query failed, attempting datasource fallback: %s", exc)
                    data_source_id = self._resolve_data_source_id()
                    if not data_source_id:
                        raise
                    params = {"page_size": limit}
                    if start_cursor:
                        params["start_cursor"] = start_cursor
                    res = self.client.query_data_source(data_source_id=data_source_id, **params)
            return res
        except Exception:
            logger.exception("Failed to fetch pages from Notion")
            return {"results": []}

    def _resolve_data_source_id(self) -> Optional[str]:
        try:
            db = self.client.retrieve_database(database_id=self.target_id)
            for data_source in db.get("data_sources", []) or []:
                ds_id = data_source.get("id")
                if ds_id:
                    return ds_id
        except Exception:
            logger.exception("Failed to resolve data source id for database %s", self.target_id)
        return None

    def fetch_page(self, page_id: str) -> Optional[Dict[str, Any]]:
        try:
            return self.client.retrieve_page(page_id=page_id)
        except Exception:
            logger.exception("Failed to retrieve Notion page")
            return None
