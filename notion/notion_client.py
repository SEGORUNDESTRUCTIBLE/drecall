"""Notion API client wrapper for dRecall.

Provides a lightweight, safe wrapper around the Notion Python SDK with
environment-based configuration, retries, and centralized request handling.
"""

import logging
import os
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
        token = api_key if api_key is not None else get_settings().notion_api_key
        if not token or not str(token).strip():
            raise ValueError("Missing Notion API key")
        self.api_key = str(token).strip()
        self.retries = retries
        self.backoff = backoff
        self._client = None

    @property
    def client(self):
        if self._client is None:
            try:
                from notion_client import Client
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

    def retrieve_database(self, database_id: str) -> Any:
        return self._call(self.client.databases.retrieve, database_id=database_id)

    def query_database(self, **kwargs):
        try:
            return self._call(self.client.databases.query, **kwargs)
        except AttributeError:
            database_id = kwargs.pop("database_id", None)
            if not database_id:
                raise
            return self.request("POST", "databases/query", json={"database_id": database_id, **kwargs})

    def query_data_source(self, data_source_id: str, **kwargs) -> Any:
        return self._call(self.client.data_sources.query, data_source_id=data_source_id, **kwargs)

    def search(self, **kwargs):
        return self._call(self.client.search, **kwargs)

    def request(self, method: str, path: str, **kwargs):
        """Perform a low-level request via the underlying client.

        Useful for newer Notion endpoints (data sources) not yet modelled
        in older SDK versions. `path` should be the full API path after
        the /v1 prefix, e.g. 'data_sources/{id}/pages'.
        """
        body = kwargs.pop("json", kwargs.pop("body", None))
        query = kwargs.pop("query", None)
        form_data = kwargs.pop("form_data", None)
        try:
            return self._call(self.client.request, path, method, query=query, body=body, form_data=form_data)
        except AttributeError:
            # Older SDKs may not expose `request`; raise a clear error
            raise RuntimeError("Underlying Notion client does not support low-level request dispatch")

    def archive_page(self, page_id: str):
        """Archive a Notion page created during live test validation."""
        try:
            return self._call(self.client.pages.update, page_id=page_id, archived=True)
        except AttributeError:
            return self.request("PATCH", f"pages/{page_id}", json={"archived": True})


def detect_notion_mode(obj: Any) -> bool:
    """Detect whether a Notion API object represents a data source."""
    return isinstance(obj, dict) and obj.get("object") == "data_source"
