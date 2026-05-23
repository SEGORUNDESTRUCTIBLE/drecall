from core.ingestion_engine import IngestionEngine
from core.schemas import RecallItem


class FencedProvider:
    def generate(self, prompt: str, expect_json: bool = False):
        # Return fenced JSON to simulate provider returning markdown
        return 'Here is the response:\n```json\n{\"title\": \"Fence\", \"content\": \"From provider\"}\n```'


def test_ingest_with_fenced_provider():
    engine = IngestionEngine(provider=FencedProvider(), template_type="structured_learning")
    item = engine.ingest_text("Raw notes about X.", title="Test Title")
    assert isinstance(item, RecallItem)
    assert item.title
    assert item.content
    # The provider output should be present in metadata
    assert "provider_output" in item.metadata
