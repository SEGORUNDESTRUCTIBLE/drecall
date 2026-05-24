import json

from core.adaptive_pipeline import AdaptivePipeline
from core.canonical_schema import CanonicalRevisionPayload
from core.content_classifier import ContentClassifier
from core.domain_detector import DomainDetector
from core.metadata_extractor import MetadataExtractor
from core.template_selector import TemplateSelector
from notion.notion_schema_mapper import NotionSchemaMapper
from notion.workspace_inspector import WorkspaceInspector
from core.schemas import ProviderResponse


class DummyProvider:
    def generate(self, prompt: str, system_prompt: str = "") -> ProviderResponse:
        payload = {
            "title": "Shock overview",
            "content": "Shock is a state of circulatory failure leading to tissue hypoperfusion.",
            "core_concept": "Tissue hypoperfusion due to inadequate perfusion pressure.",
            "one_liner": "Shock is circulatory failure that causes poor tissue perfusion.",
            "exam_pearl": "Always differentiate hypovolemic shock from cardiogenic shock by jugular venous pressure.",
            "memory_hook": "Shock sucks the pressure out of tissues.",
            "trap": "Do not confuse distributive shock with hypovolemic shock.",
            "retest_question": "Which shock type has warm extremities?",
            "tags": ["critical care", "shock"],
        }
        return ProviderResponse(
            provider="mock",
            model="mock-model",
            text=json.dumps(payload),
            latency_ms=12.0,
            metadata={"mock": True},
        )


class DummyNotionClient:
    class Databases:
        @staticmethod
        def retrieve(database_id: str):
            return {
                "id": database_id,
                "title": [{"plain_text": "Revision DB"}],
                "properties": {
                    "Title": {"type": "title"},
                    "Content": {"type": "rich_text"},
                },
            }

    databases = Databases()

    @staticmethod
    def search(filter=None):
        return {"results": []}


def test_domain_detector_returns_mcq():
    result = DomainDetector().detect(
        "Which of the following is the most likely diagnosis? A. X B. Y C. Z D. W"
    )
    assert result.content_type == "mcq"
    assert result.confidence > 0.8


def test_content_classifier_concept_intent():
    result = ContentClassifier().classify(
        "Explain the pathophysiology of diabetic ketoacidosis.", domain="medical", content_type="concept"
    )
    assert result.intent == "concept_explanation"
    assert result.template_hint == "concept"


def test_template_selector_loads_medical_templates():
    selector = TemplateSelector()
    assert "mcq" in selector.templates
    choice = selector.select("medical", "ecg", "ecg_interpretation")
    assert choice.template_name == "ecg"
    assert choice.definition.image_requirements is True


def test_canonical_schema_builds_from_provider_output():
    payload = {
        "title": "Hypertension",
        "content": "Hypertension is sustained elevation of blood pressure.",
        "core_concept": "Persistent high arterial pressure harms organs.",
    }
    canonical = CanonicalRevisionPayload.from_provider_output(payload, template_name="concept")
    assert canonical.title == "Hypertension"
    assert canonical.core_concept.startswith("Persistent high arterial pressure")
    assert canonical.template_type == "concept"


def test_metadata_extractor_infers_schedule_and_tags():
    canonical = CanonicalRevisionPayload(
        title="Hypertension",
        content="Hypertension is sustained elevation of blood pressure.",
        core_concept="Persistent high arterial pressure harms organs.",
    )
    result = MetadataExtractor().extract(
        canonical.model_dump(mode="json"),
        template_name="concept",
        domain="medical",
        subtype="cardiology",
    )
    assert result.revision_metadata["source_template"] == "concept"
    assert "medical" in result.inferred_tags
    assert "cardiology" in result.inferred_tags


def test_notion_schema_mapper_detects_missing_fields():
    properties = {
        "Title": {"type": "title"},
        "Content": {"type": "rich_text"},
    }
    report = NotionSchemaMapper().inspect(properties, ["title", "content", "core_concept"])  # type: ignore[arg-type]
    assert report.mapping["title"] == "Title"
    assert report.mapping["content"] == "Content"
    assert "core_concept" in report.missing
    assert report.score < 1.0


def test_workspace_inspector_can_handle_empty_search():
    inspector = WorkspaceInspector(client=DummyNotionClient())
    best = inspector.choose_best_database([], ["title", "content"])
    assert best is None


def test_adaptive_pipeline_process_text_without_notion():
    pipeline = AdaptivePipeline(provider=DummyProvider(), notion_client=DummyNotionClient(), notion_sink=None)
    result = pipeline.process_text("Define shock and its classification.", source="unit_test")
    assert result.canonical_payload.title
    assert result.metadata_extraction.revision_metadata["source_template"]
    assert result.workspace_inspection is None
    assert result.notion_result is None
