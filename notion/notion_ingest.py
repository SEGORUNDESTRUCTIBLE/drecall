"""Ingest RecallItem instances into Notion pages.

Handles property mapping, duplicate checks, block building, and safe uploads.
"""

import logging
from typing import Optional, Dict, Any

from config import get_settings
from core.schemas import RecallItem
from .notion_client import NotionClientWrapper
from .block_builder import build_blocks

logger = logging.getLogger(__name__)


class NotionIngest:
    def __init__(self, client: Optional[NotionClientWrapper] = None, database_id: Optional[str] = None, datasource_id: Optional[str] = None):
        self.client = client or NotionClientWrapper()
        active_settings = get_settings()

        resolved_datasource = datasource_id or active_settings.notion_datasource_id
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

    def _default_database_id(self) -> Optional[str]:
        return get_settings().notion_database_id

    def _map_properties(self, item: RecallItem) -> Dict[str, Any]:
        props = {
            "Title": {"title": [{"type": "text", "text": {"content": item.title}}]},
            "Tags": {"multi_select": [{"name": t} for t in item.tags]},
            "Source": {"rich_text": [{"type": "text", "text": {"content": item.source or ''}}]},
            "Template": {"select": {"name": item.template_type}},
            "Processed": {"checkbox": item.processed},
            "Enhanced": {"checkbox": item.enhanced},
            "Created At": {"date": {"start": item.created_at.isoformat()}},
            "Updated At": {"date": {"start": item.updated_at.isoformat()}},
            "Metadata": {"rich_text": [{"type": "text", "text": {"content": str(item.metadata)}}]},
        }
        return props

    def ingest_item(self, item: RecallItem, overwrite_duplicates: bool = False) -> Dict[str, Any]:
        if not self.target_id:
            raise ValueError("No Notion database/datasource ID configured for ingestion")

        # Basic validation
        if not item.title or not item.content:
            raise ValueError("RecallItem must have title and content")

        # Duplicate check: search by title in database
        existing = self._find_by_title(item.title)
        if existing and not overwrite_duplicates:
            logger.info(f"Duplicate found for title {item.title}, returning existing page")
            return existing

        # Build properties and create page
        properties = self._map_properties(item)
        # Build parent structure depending on datasource mode
        if self.datasource_mode:
            parent = {"type": "data_source", "data_source_id": self.target_id}
            body = {"parent": parent, "properties": properties}
            # Prefer high-level page creation if supported, else use low-level request
            try:
                page = self.client.create_page(**body)
            except Exception:
                # Attempt low-level endpoint
                path = f"data_sources/{self.target_id}/pages"
                page = self.client.request("POST", path, json=body)
        else:
            body = {"parent": {"database_id": self.target_id}, "properties": properties}
            page = self.client.create_page(**body)

        # Build and append blocks for content
        blocks = build_blocks(item.content)
        if blocks:
            try:
                # SDK expects block_id or page_id depending on endpoint
                self.client.append_blocks(block_id=page["id"], children=blocks)
            except Exception:
                try:
                    # low-level append for datasources
                    path = f"pages/{page['id']}/children"
                    self.client.request("PATCH", path, json={"children": blocks})
                except Exception:
                    logger.exception("Failed to append blocks to Notion page")

        # Update item with notion page id
        return page

    def _find_by_title(self, title: str) -> Optional[Dict[str, Any]]:
        # Query either database or datasource for pages with matching title
        try:
            if self.datasource_mode:
                path = f"data_sources/{self.target_id}/query"
                res = self.client.request("POST", path, json={"filter": {"property": "Title", "title": {"equals": title}}})
            else:
                res = self.client.query_database(database_id=self.target_id, filter={"property": "Title", "title": {"equals": title}})
            results = res.get("results", [])
            if results:
                return results[0]
        except Exception:
            logger.debug("Failed to query for duplicates (datasource/db)")
        return None
"""Notion data ingestion.

Handles importing recall items into Notion databases.
"""

from typing import Any, List, Optional

from core.schemas import RecallItem


class NotionIngester:
    """Ingester for uploading recall items to Notion.
    
    Handles converting RecallItems to Notion pages and
    uploading them to configured databases.
    """
    
    def __init__(self, notion_client: Any) -> None:
        """Initialize Notion ingester.
        
        Args:
            notion_client: NotionClient instance.
        """
        self.client = notion_client
    
    def ingest_item(
        self,
        item: RecallItem,
        database_id: str,
    ) -> str:
        """Ingest a recall item into Notion.
        
        Args:
            item: RecallItem to ingest.
            database_id: Target Notion database ID.
            
        Returns:
            ID of created Notion page.
        """
        # TODO: Implement item ingestion
        # - Convert RecallItem to Notion properties
        # - Create page in database
        # - Handle attachments/blocks
        # - Store page ID in item
        # - Return page ID
        raise NotImplementedError("Item ingestion not yet implemented")
    
    def ingest_batch(
        self,
        items: List[RecallItem],
        database_id: str,
    ) -> List[str]:
        """Ingest multiple recall items in batch.
        
        Args:
            items: List of RecallItems to ingest.
            database_id: Target Notion database ID.
            
        Returns:
            List of created Notion page IDs.
        """
        # TODO: Implement batch ingestion
        # - Process each item
        # - Handle rate limiting
        # - Track success/failures
        # - Return list of page IDs
        raise NotImplementedError("Batch ingestion not yet implemented")
    
    def sync_item(
        self,
        item: RecallItem,
        notion_page_id: str,
    ) -> bool:
        """Sync a recall item with an existing Notion page.
        
        Args:
            item: Updated RecallItem.
            notion_page_id: ID of Notion page to update.
            
        Returns:
            True if sync successful.
        """
        # TODO: Implement item sync
        # - Convert RecallItem to Notion properties
        # - Update page in Notion
        # - Handle conflicts
        # - Return success status
        raise NotImplementedError("Item sync not yet implemented")
