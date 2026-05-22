"""Notion API client wrapper for dRecall.

Provides a lightweight, safe wrapper around the Notion Python SDK with
environment-based configuration, retries, and centralized request handling.
"""

import logging
import time
from typing import Any, Callable, Optional

from config import get_settings

logger = logging.getLogger(__name__)


class NotionClientWrapper:
    """Wrapper around the official Notion client.

    - Lazy imports the SDK to avoid hard dependency during unit tests.
    - Loads `NOTION_API_KEY` from environment if not provided.
    - Provides `_call` helper for retry/backoff and consistent error handling.
    """

    def __init__(self, api_key: Optional[str] = None, retries: int = 3, backoff: float = 1.0):
        self.api_key = api_key or get_settings().notion_api_key
        self.retries = retries
        self.backoff = backoff
        self._client = None

    @property
    def client(self):
        if self._client is None:
            try:
                from notion_client import Client
                if not self.api_key:
                    raise ValueError("NOTION_API_KEY not set in environment or passed to NotionClientWrapper")
                self._client = Client(auth=self.api_key)
                logger.debug("Initialized Notion Client")
            except ImportError as e:
                logger.error("notion-client package not installed")
                raise ImportError("notion-client is required: pip install notion-client") from e
        return self._client

    def _call(self, fn: Callable[..., Any], *args, **kwargs) -> Any:
        last_exc = None
        for attempt in range(1, max(1, self.retries) + 1):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                last_exc = e
                wait = self.backoff * (2 ** (attempt - 1))
                logger.warning(f"Notion API call failed (attempt {attempt}/{self.retries}): {e}; retrying in {wait}s")
                time.sleep(wait)
        logger.error("All Notion retries failed")
        raise last_exc

    # Convenience wrappers for common operations
    def create_database(self, **kwargs):
        return self._call(self.client.databases.create, **kwargs)

    def create_page(self, **kwargs):
        return self._call(self.client.pages.create, **kwargs)

    def update_page(self, **kwargs):
        return self._call(self.client.pages.update, **kwargs)

    def append_blocks(self, **kwargs):
        return self._call(self.client.blocks.children.append, **kwargs)

    def retrieve_page(self, **kwargs):
        return self._call(self.client.pages.retrieve, **kwargs)

    def query_database(self, **kwargs):
        return self._call(self.client.databases.query, **kwargs)

    def search(self, **kwargs):
        return self._call(self.client.search, **kwargs)

    def request(self, method: str, path: str, **kwargs):
        """Perform a low-level request via the underlying client.

        Useful for newer Notion endpoints (data sources) not yet modelled
        in older SDK versions. `path` should be the full API path after
        the /v1 prefix, e.g. 'data_sources/{id}/pages'.
        """
        try:
            return self._call(self.client.request, method, path, **kwargs)
        except AttributeError:
            # Older SDKs may not expose `request`; raise a clear error
            raise RuntimeError("Underlying Notion client does not support low-level request dispatch")

    def archive_page(self, page_id: str):
        """Archive a Notion page created during live test validation."""
        try:
            return self._call(self.client.pages.update, page_id=page_id, archived=True)
        except AttributeError:
            return self.request("PATCH", f"pages/{page_id}", json={"archived": True})
"""Notion API client wrapper.

Provides abstraction over the official Notion client with
retry logic, error handling, and convenience methods.
"""

from typing import Any, Dict, Optional


class NotionClient:
    """Wrapper around Notion API client.
    
    Provides convenient methods for interacting with Notion,
    including error handling, retry logic, and rate limiting.
    """
    
    def __init__(self, api_key: str, timeout: int = 30) -> None:
        """Initialize Notion client.
        
        Args:
            api_key: Notion integration token.
            timeout: Request timeout in seconds.
        """
        self.api_key = api_key
        self.timeout = timeout
        self._client = None
    
    @property
    def client(self):
        """Lazily initialize and return Notion client.
        
        Returns:
            Notion client instance.
        """
        if self._client is None:
            try:
                from notion_client import Client
                self._client = Client(auth=self.api_key)
            except ImportError:
                raise ImportError(
                    "notion-client package is required for NotionClient"
                )
        return self._client
    
    def get_database(self, database_id: str) -> Dict[str, Any]:
        """Get database information.
        
        Args:
            database_id: Notion database ID.
            
        Returns:
            Database information dictionary.
        """
        # TODO: Implement database retrieval
        # - Call notion client to get database
        # - Handle errors and rate limiting
        # - Return database info
        raise NotImplementedError("Database retrieval not yet implemented")
    
    def create_page(
        self,
        database_id: str,
        properties: Dict[str, Any],
        children: Optional[list] = None,
    ) -> Dict[str, Any]:
        """Create a new page in a database.
        
        Args:
            database_id: Notion database ID.
            properties: Page properties/metadata.
            children: Optional content blocks.
            
        Returns:
            Created page information.
        """
        # TODO: Implement page creation
        # - Build page payload
        # - Call notion client
        # - Handle errors
        # - Return created page info
        raise NotImplementedError("Page creation not yet implemented")
    
    def update_page(
        self,
        page_id: str,
        properties: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update an existing page.
        
        Args:
            page_id: Notion page ID.
            properties: Updated properties.
            
        Returns:
            Updated page information.
        """
        # TODO: Implement page update
        # - Build update payload
        # - Call notion client
        # - Handle errors
        # - Return updated page info
        raise NotImplementedError("Page update not yet implemented")
    
    def query_database(
        self,
        database_id: str,
        filter_: Optional[Dict[str, Any]] = None,
        sorts: Optional[list] = None,
    ) -> list:
        """Query a Notion database.
        
        Args:
            database_id: Notion database ID.
            filter_: Query filter condition.
            sorts: Sort specifications.
            
        Returns:
            List of matching pages.
        """
        # TODO: Implement database query
        # - Build query parameters
        # - Call notion client
        # - Handle pagination
        # - Return results
        raise NotImplementedError("Database query not yet implemented")
