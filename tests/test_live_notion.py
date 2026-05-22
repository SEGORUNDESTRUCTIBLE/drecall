import os
from datetime import datetime, timezone

import pytest

from config import get_settings, reset_settings
from core.schemas import RecallItem
from notion.notion_ingest import NotionIngest


def test_drecall_live_integration_notion_datasource():
    if not os.environ.get("NOTION_API_KEY"):
        pytest.skip("NOTION_API_KEY not set")
    if not os.environ.get("NOTION_DATASOURCE_ID"):
        pytest.skip("NOTION_DATASOURCE_ID not set for datasource architecture")

    reset_settings()
    settings = get_settings()

    assert settings.notion_api_key, "NOTION_API_KEY must be configured"
    assert settings.notion_datasource_id, "NOTION_DATASOURCE_ID must be configured"

    unique_suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    item = RecallItem(
        title=f"dRecall Live Integration Test {unique_suffix}",
        content="This is a sandbox validation page for datasource ingestion testing.",
        source="live-test",
        template_type="testing",
        tags=["live", "notion", "datasource"],
        metadata={"test_run": unique_suffix},
    )

    ingestor = NotionIngest(client=None)
    assert ingestor.datasource_mode is True
    assert ingestor.target_id == settings.notion_datasource_id

    result = ingestor.ingest_item(item, overwrite_duplicates=False)

    assert isinstance(result, dict), "Notion ingest should return a response dictionary"
    assert result.get("id"), "Live Notion datasource upload must return a valid page id"

    page_id = result["id"]
    print(f"dRecall Live Integration Test created page id: {page_id}")
    assert isinstance(page_id, str) and page_id.strip(), "Returned page id must be a non-empty string"

    if os.environ.get("NOTION_LIVE_TEST_CLEANUP", "false").lower() in {"1", "true", "yes"}:
        try:
            ingestor.client.archive_page(page_id)
            print(f"Archived sandbox test page: {page_id}")
        except Exception as exc:
            print(f"WARNING: cleanup failed for page {page_id}: {exc}")
