"""Adaptive ingestion orchestrator for autonomous medical revision."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from .canonical_schema import CanonicalRevisionPayload
from .content_classifier import ContentClassifier, ContentClassificationResult
from .domain_detector import DomainDetectionResult, DomainDetector
from .metadata_extractor import MetadataExtractor, MetadataExtractionResult
from .template_selector import TemplateChoice, TemplateDefinition, TemplateSelector
from .schemas import ProviderResponse
from .validators import Validator
from notion.notion_sink import NotionSink
from notion.workspace_inspector import WorkspaceInspectionResult, WorkspaceInspector
from core.contracts.provider_contracts import ProviderAdapter

logger = logging.getLogger("drecall.adaptive_pipeline")


@dataclass(frozen=True)
class AdaptivePipelineResult:
    detection: DomainDetectionResult
    classification: ContentClassificationResult
    template_choice: TemplateChoice
    canonical_payload: CanonicalRevisionPayload
    metadata_extraction: MetadataExtractionResult
    workspace_inspection: Optional[WorkspaceInspectionResult]
    notion_result: Optional[Dict[str, Any]]
    provider_response: Optional[ProviderResponse]


class AdaptivePipeline:
    """Orchestrates end-to-end structured ingestion from raw medical text."""

    def __init__(
        self,
        provider: ProviderAdapter,
        notion_client: Optional[Any] = None,
        notion_sink: Optional[NotionSink] = None,
        candidate_database_ids: Optional[List[str]] = None,
        validator: Optional[Validator] = None,
    ) -> None:
        self.domain_detector = DomainDetector()
        self.content_classifier = ContentClassifier()
        self.template_selector = TemplateSelector()
        self.metadata_extractor = MetadataExtractor()
        self.workspace_inspector = WorkspaceInspector(notion_client) if notion_client is not None else None
        self.provider = provider
        self.notion_sink = notion_sink
        self.candidate_database_ids = candidate_database_ids or []
        self.validator = validator or Validator()

    def process_text(
        self,
        text: str,
        source: Optional[str] = None,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> AdaptivePipelineResult:
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Text must be a non-empty string")

        detection = self.domain_detector.detect(text, metadata=metadata or {})
        classification = self.content_classifier.classify(
            text,
            domain=detection.domain,
            content_type=detection.content_type,
        )
        template_choice = self.template_selector.select(
            detection.domain,
            detection.content_type,
            classification.intent,
            metadata,
        )

        prompt = self._build_prompt(text, detection, classification, template_choice.definition)
        provider_response = self._generate(prompt)
        parsed = self._parse_provider_output(provider_response)

        canonical_payload = CanonicalRevisionPayload.from_provider_output(
            parsed,
            template_name=template_choice.template_name,
            title=title,
        )

        if source:
            canonical_payload.source = source

        if not canonical_payload.title or not canonical_payload.content:
            raise ValueError("Canonical payload must include title and content")

        is_valid, error_message = self.validator.validate_content(canonical_payload.content)
        if not is_valid:
            raise ValueError(error_message or "Content validation failed")

        metadata_extraction = self.metadata_extractor.extract(
            canonical_payload.model_dump(mode="json"),
            template_name=template_choice.template_name,
            domain=detection.domain,
            subtype=detection.subtype,
        )

        workspace_inspection = None
        notion_result = None
        if self.workspace_inspector is not None:
            workspace_inspection = self.workspace_inspector.choose_best_database(
                self.candidate_database_ids,
                list(CanonicalRevisionPayload.model_fields.keys()),
            )

        if self.notion_sink is not None and workspace_inspection is not None:
            if workspace_inspection.mapping_report.missing:
                self._create_missing_properties(
                    workspace_inspection.candidate_id,
                    workspace_inspection.mapping_report,
                )
            item_dict = canonical_payload.model_dump(mode="json")
            item_dict["datasource_id"] = workspace_inspection.candidate_id
            item_dict["revision_metadata"] = metadata_extraction.revision_metadata
            item_dict["tags"] = sorted(set(item_dict.get("tags", []) + metadata_extraction.inferred_tags))
            notion_result = self.notion_sink.create(item_dict)

        return AdaptivePipelineResult(
            detection=detection,
            classification=classification,
            template_choice=template_choice,
            canonical_payload=canonical_payload,
            metadata_extraction=metadata_extraction,
            workspace_inspection=workspace_inspection,
            notion_result=notion_result,
            provider_response=provider_response if isinstance(provider_response, ProviderResponse) else None,
        )

    def _generate(self, prompt: str) -> Any:
        try:
            response = self.provider.generate(prompt)
        except Exception as exc:
            logger.error("Provider generation failed: %s", exc)
            raise
        return response

    def _parse_provider_output(self, provider_response: Any) -> Dict[str, Any]:
        raw_text = None
        if isinstance(provider_response, ProviderResponse):
            raw_text = provider_response.text
        elif isinstance(provider_response, dict):
            return provider_response
        elif isinstance(provider_response, str):
            raw_text = provider_response
        else:
            raw_text = str(provider_response)

        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise ValueError("Provider response must be valid JSON") from exc

        if isinstance(parsed, list) and parsed:
            parsed = parsed[0]

        if not isinstance(parsed, dict):
            raise ValueError("Provider response JSON must resolve to an object")

        return parsed

    def _build_prompt(
        self,
        text: str,
        detection: DomainDetectionResult,
        classification: ContentClassificationResult,
        definition: TemplateDefinition,
    ) -> str:
        required_fields = ", ".join(definition.required_fields)
        sections = "\n".join(f"- {section}" for section in definition.revision_sections)
        return (
            f"You are an expert medical revision assistant for NEET-PG preparation.\n"
            f"Classify the input and generate a concise structured revision item using the '{definition.name}' template.\n"
            f"Use the sections below exactly as field names in JSON output:\n{sections}\n\n"
            f"Input text:\n{text.strip()}\n\n"
            "Output requirements:\n"
            "- Return ONLY valid JSON.\n"
            "- Use exact field names.\n"
            "- Include all required fields if information is available.\n"
            "- Provide empty strings or empty arrays when a field cannot be inferred.\n"
            f"- Required fields: {required_fields}.\n"
            "- Do not include markdown, code fences, or explanations.\n"
            "JSON output:" 
        )

    def _create_missing_properties(self, database_id: str, report: Any) -> None:
        if self.notion_sink is None or self.notion_sink.client is None:
            return

        updates: Dict[str, Any] = {}
        for field, prop_type in report.suggested_creations.items():
            property_name = self._pretty_name(field)
            if property_name in updates:
                continue
            updates[property_name] = self._build_property_definition(prop_type)

        if not updates:
            return

        try:
            self.notion_sink.client.databases.update(database_id=database_id, properties=updates)
            logger.info("Created missing Notion properties for %s: %s", database_id, list(updates.keys()))
        except Exception as exc:
            logger.warning("Could not create missing properties for %s: %s", database_id, exc)

    def _pretty_name(self, field_name: str) -> str:
        return " ".join(word.capitalize() for word in field_name.split("_"))

    def _build_property_definition(self, prop_type: str) -> Dict[str, Any]:
        if prop_type == "title":
            return {"title": {}}
        if prop_type == "rich_text":
            return {"rich_text": {}}
        if prop_type == "checkbox":
            return {"checkbox": {}}
        if prop_type == "select":
            return {"select": {"options": []}}
        if prop_type == "multi_select":
            return {"multi_select": {"options": []}}
        if prop_type == "date":
            return {"date": {}}
        return {"rich_text": {}}
