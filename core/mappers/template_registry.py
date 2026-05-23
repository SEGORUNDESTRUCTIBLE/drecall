"""Template registry for mapping engine selection."""

from __future__ import annotations

from typing import Dict

from .schema_registry import SchemaRegistry, TemplateSchema
from .recall_mapper import RecallMapper


class TemplateRegistry:
    """Registry that resolves template names to mapper and schema information."""

    _template_map: Dict[str, str] = {
        "medical": "medical",
        "coding": "coding",
        "productivity": "productivity",
        "language": "language",
        "flashcards": "flashcards",
        "custom": "custom",
    }

    @classmethod
    def get_schema(cls, template_type: str) -> TemplateSchema:
        return SchemaRegistry.get_schema(cls._template_map.get(template_type, "custom"))

    @classmethod
    def get_mapper(cls, template_type: str) -> RecallMapper:
        schema = cls.get_schema(template_type)
        if schema.name == "medical":
            from .medical_mapper import MedicalMapper

            return MedicalMapper(schema=schema)

        return RecallMapper(schema=schema)

    @classmethod
    def available_templates(cls) -> Dict[str, str]:
        return dict(cls._template_map)
