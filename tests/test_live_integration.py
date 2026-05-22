import os
from datetime import datetime, timezone

import pytest

from config import get_settings, reset_settings
from core.ingestion_engine import IngestionEngine
from core.schemas import RecallItem
from notion.notion_client import NotionClientWrapper
from notion.notion_sink import NotionSink, DuplicatePersistenceError
from providers.groq_provider import GroqProvider
from providers.gemini_provider import GeminiProvider


def get_providers():
    providers = []
    if os.environ.get("GROQ_API_KEY"):
        providers.append(("groq", GroqProvider()))
    if os.environ.get("GEMINI_API_KEY"):
        providers.append(("gemini", GeminiProvider()))
    if not providers:
        # Add a dummy so pytest parameterize doesn't fail if empty, we will skip inside the test
        providers.append(("none", None))
    return providers


@pytest.mark.parametrize("provider_name,provider", get_providers())
def test_full_pipeline_live_integration(provider_name, provider):
    """Validates true end-to-end runtime behavior using sandbox credentials."""
    if not os.environ.get("NOTION_API_KEY"):
        pytest.skip("NOTION_API_KEY not set")
    if not os.environ.get("NOTION_DATASOURCE_ID"):
        pytest.skip("NOTION_DATASOURCE_ID not set for sandbox testing")
    if provider is None:
        pytest.skip("No live provider API keys configured")

    # This test should ideally be skipped in standard CI automatically if keys are absent.
    # The checks above ensure we skip safely otherwise.

    reset_settings()
    settings = get_settings()

    # Setup Ingestion Engine
    engine = IngestionEngine(template_type="structured_learning", provider=provider)

    # Prepare unique data for this test run
    unique_suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    test_title = f"dRecall E2E Integration {provider_name} {unique_suffix}"
    test_text = "Photosynthesis is the process used by plants, algae and certain bacteria to harness energy from sunlight and turn it into chemical energy."

    # 1. Validate provider runtime generation and structured RecallItem creation
    item = engine.ingest_text(
        text=test_text,
        title=test_title,
        tags=["live-test", "e2e"],
        source="integration-sandbox",
    )
    assert isinstance(item, RecallItem)
    assert item.title == test_title
    assert "photosynthesis" in str(item.content).lower()

    # Setup Notion Sink
    client = NotionClientWrapper()
    datasource_id = settings.notion_datasource_id
    notion_sink = NotionSink(
        client=client,
        datasource_map={datasource_id: {}},
        backoff_factor=1.0,
    )

    item_dict = item.to_dict()
    item_dict["datasource_id"] = datasource_id
    dedup_key = f"title:{test_title}"
    item_dict["dedup_key"] = dedup_key

    page_id = None
    try:
        # 2. Validate NotionSink persistence
        persist_res = notion_sink.create(item_dict)
        page_id = persist_res.id
        assert page_id is not None
        assert isinstance(page_id, str)

        # 3. Validate Duplicate Checks
        # Attempting to create it again with the same dedup_key should trigger a DuplicatePersistenceError
        with pytest.raises(DuplicatePersistenceError):
            notion_sink.create(item_dict)

        # 4. Validate Retrieval Verification
        retrieved_page = notion_sink.retrieve_page(page_id)
        assert retrieved_page is not None
        assert retrieved_page.get("id") == page_id

    finally:
        # 5. Cleanup / archive support for generated test pages
        if page_id:
            try:
                # We always try to cleanup in live integration tests to avoid cluttering the sandbox
                notion_sink.client.archive_page(page_id)
                print(f"Archived E2E test page: {page_id}")
            except Exception as exc:
                print(f"WARNING: Cleanup failed for E2E test page {page_id}: {exc}")
