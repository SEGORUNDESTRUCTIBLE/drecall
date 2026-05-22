"""Utilities for fetching Notion pages and metadata for duplicate detection."""

import logging
from typing import Optional, Dict, Any, List

from config import get_settings
from .notion_client import NotionClientWrapper

logger = logging.getLogger(__name__)


class NotionFetcher:
    def __init__(self, client: Optional[NotionClientWrapper] = None, database_id: Optional[str] = None):
        self.client = client or NotionClientWrapper()
        active_settings = get_settings()

        resolved_datasource = active_settings.notion_datasource_id
        resolved_database = database_id or active_settings.notion_database_id

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

    def fetch_pages(self, limit: int = 50) -> List[Dict[str, Any]]:
        if not self.target_id:
            raise ValueError("No database/datasource id configured for fetching pages")
        try:
            if self.datasource_mode:
                path = f"data_sources/{self.target_id}/query"
                res = self.client.request("POST", path, json={"page_size": limit})
            else:
                res = self.client.query_database(database_id=self.target_id, page_size=limit)
            return res.get("results", [])
        except Exception:
            logger.exception("Failed to fetch pages from Notion")
            return []

    def fetch_page(self, page_id: str) -> Optional[Dict[str, Any]]:
        try:
            return self.client.retrieve_page(page_id=page_id)
        except Exception:
            logger.exception("Failed to retrieve Notion page")
            return None
