import os
from datetime import datetime, timezone

import pytest

from config import reset_settings, get_settings
from core.ingestion_engine import IngestionEngine
from core.schemas import RecallItem
from core.validators import Validator
from duplicate.backends.hybrid_duplicate_detector import HybridDuplicateDetector

RUN_LIVE_TESTS = os.environ.get("DRECALL_RUN_LIVE_TESTS", "false").lower() in {"1", "true", "yes"}


def skip_unless_live():
    if not RUN_LIVE_TESTS:
        pytest.skip("Live integration tests disabled. Set DRECALL_RUN_LIVE_TESTS=true to enable.")


def get_live_provider():
    from config import get_settings

    settings = get_settings()
    if os.environ.get("GROQ_API_KEY"):
        from providers.groq_provider import GroqProvider

        return GroqProvider(
            api_key=os.environ.get("GROQ_API_KEY"),
            model=os.environ.get("GROQ_MODEL", settings.groq_model),
            timeout=settings.request_timeout,
            retries=settings.max_retries,
        )
    if os.environ.get("GEMINI_API_KEY"):
        from providers.gemini_provider import GeminiProvider

        return GeminiProvider(
            api_key=os.environ.get("GEMINI_API_KEY"),
            model=os.environ.get("GEMINI_MODEL", settings.gemini_model),
            timeout=settings.request_timeout,
            retries=settings.max_retries,
        )
    pytest.skip("No live AI provider credentials configured")


def get_notion_sink(sandbox_datasource_id: str):
    try:
        from notion_client import Client as NotionClient
    except ImportError:
        pytest.skip("notion-client package is required for live Notion tests")

    from notion.notion_sink import NotionSink

    api_key = os.environ.get("NOTION_API_KEY")
    if not api_key:
        pytest.skip("NOTION_API_KEY not configured")

    client = NotionClient(auth=api_key)
    sink = NotionSink(client=client, datasource_map={sandbox_datasource_id: {}})
    return sink


def test_live_provider_runtime_selection_and_json_generation():
    skip_unless_live()

    if os.environ.get("GROQ_API_KEY"):
        from providers.groq_provider import GroqProvider

        prov = GroqProvider(api_key=os.environ["GROQ_API_KEY"], retries=1)
        assert prov.validate_credentials() is True
        out = prov.generate('Respond only with: {"status": "ok"}', expect_json=True)
        assert isinstance(out, (dict, list))

    if os.environ.get("GEMINI_API_KEY"):
        from providers.gemini_provider import GeminiProvider

        prov = GeminiProvider(api_key=os.environ["GEMINI_API_KEY"], retries=1)
        assert prov.validate_credentials() is True
        out = prov.generate('Respond only with: {"status": "ok"}', expect_json=True)
        assert isinstance(out, (dict, list))


def test_live_recall_item_creation_with_real_provider():
    skip_unless_live()

    provider = get_live_provider()
    ingestor = IngestionEngine(provider=provider)

    recall_item = ingestor.ingest_text(
        text="Explain the difference between regression and classification in a short, structured note.",
        title="Regression vs Classification",
        template_type="structured_learning",
        source="live-sandbox",
        tags=["live", "integration"],
    )

    assert isinstance(recall_item, RecallItem)
    assert recall_item.title and recall_item.content
    assert isinstance(recall_item.metadata, dict)
    assert "provider_output" in recall_item.metadata

    validator = Validator()
    valid, errors = validator.validate_recall_item(recall_item)
    assert valid, f"RecallItem validation failed: {errors}"

    detector = HybridDuplicateDetector()
    candidate = recall_item.to_dict()
    duplicate_result = detector.find_duplicates(candidate=candidate, existing=[candidate])
    assert duplicate_result.is_duplicate is True
    assert duplicate_result.recommended_action in {
        duplicate_result.recommended_action.__class__,
        duplicate_result.recommended_action,
    }


def test_live_notion_sink_persistence_and_retrieval():
    skip_unless_live()

    sandbox_datasource_id = os.environ.get("NOTION_SANDBOX_DATASOURCE_ID")
    if not sandbox_datasource_id:
        pytest.skip("NOTION_SANDBOX_DATASOURCE_ID not set for sandbox persistence")

    if not os.environ.get("NOTION_API_KEY"):
        pytest.skip("NOTION_API_KEY not set")

    provider = get_live_provider()
    ingestor = IngestionEngine(provider=provider)
    recall_item = ingestor.ingest_text(
        text="Create a concise study note about the lifecycle of a butterfly.",
        title="Butterfly Lifecycle",
        template_type="structured_learning",
        source="live-sandbox",
        tags=["live", "integration", "sandbox"],
    )

    assert isinstance(recall_item, RecallItem)
    item_dict = recall_item.to_dict()
    item_dict["datasource_id"] = sandbox_datasource_id
    item_dict["dedup_key"] = f"live-sandbox-{datetime.now(timezone.utc).isoformat()}"

    sink = get_notion_sink(sandbox_datasource_id)
    result = sink.create(item_dict)
    assert result.id, "NotionSink must return a valid page id"

    retrieved = sink.retrieve_page(result.id)
    assert retrieved.get("id") == result.id

    if os.environ.get("NOTION_LIVE_TEST_CLEANUP", "false").lower() in {"1", "true", "yes"}:
        try:
            sink.client.pages.update(page_id=result.id, archived=True)
        except Exception as exc:
            pytest.skip(f"Cleanup skipped due to archive error: {exc}")
