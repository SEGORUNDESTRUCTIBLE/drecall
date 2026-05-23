"""Medical-specific mapping logic for structured recall items."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .recall_mapper import RecallMapper
from .schema_registry import TemplateSchema


class MedicalMapper(RecallMapper):
    def __init__(self, schema: Optional[TemplateSchema] = None) -> None:
        super().__init__(schema=schema)

    def map(self, provider_data: Dict[str, Any], source: Optional[str] = None, template_type: str = "medical"):
        if not isinstance(provider_data, dict):
            raise ValueError("Medical mapper requires provider output as a JSON object.")

        title = self._extract_text(provider_data, ["title", "name", "headline", "question", "core_concept", "diagnosis"], fallback=None)
        if not title:
            title = self._extract_text(provider_data, ["topic", "subject_line", "prompt"], fallback="Medical recall item")

        provider_data = {**provider_data, "title": title}
        recall_item = super().map(provider_data, source=source, template_type=template_type)

        if not recall_item.content:
            recall_item = recall_item.model_copy(update={"content": self._build_medical_content(provider_data)})

        if recall_item.subject and recall_item.system and recall_item.error_type:
            recall_item.metadata.setdefault("mapped_fields", {}).update(
                {
                    "subject": recall_item.subject,
                    "system": recall_item.system,
                    "error_type": recall_item.error_type,
                    "pattern_type": recall_item.pattern_type,
                    "difficulty": recall_item.difficulty,
                }
            )

        return recall_item

    def _build_medical_content(self, data: Dict[str, Any]) -> str:
        sections = []
        for field_name in [
            "content",
            "summary",
            "explanation",
            "one_liner_revision",
            "exam_pearl",
            "why_confusing",
            "clinical_pearl",
            "pathophysiology",
        ]:
            value = data.get(field_name)
            if isinstance(value, str) and value.strip():
                sections.append(self.normalizer.normalize_text(value))

        for field_name in ["subject", "system", "error_type", "pattern_type", "difficulty"]:
            value = data.get(field_name)
            if isinstance(value, str) and value.strip():
                sections.append(f"{field_name.replace('_', ' ').title()}: {value.strip()}")

        return "\n\n".join(sections) if sections else ""
