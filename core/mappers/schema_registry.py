"""Schema registry for template-aware RecallItem mapping.

This registry defines canonical template expectations, required fields, and
validation metadata for each supported template category.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class TemplateSchema:
    name: str
    required_fields: List[str]
    optional_fields: List[str]
    canonical_fields: List[str]
    enum_fields: Dict[str, List[str]] = field(default_factory=dict)
    content_fallback_fields: List[str] = field(default_factory=lambda: ["content"])


class SchemaRegistry:
    """Registry for template schemas and canonical field definitions."""

    _schemas: Dict[str, TemplateSchema] = {}

    @classmethod
    def register_schema(cls, schema: TemplateSchema) -> None:
        cls._schemas[schema.name] = schema

    @classmethod
    def get_schema(cls, template_name: str) -> TemplateSchema:
        return cls._schemas.get(template_name, cls._schemas["custom"])

    @classmethod
    def get_all_templates(cls) -> List[str]:
        return sorted(cls._schemas.keys())


# Shared canonical fields for all templates.
COMMON_FIELDS = [
    "title",
    "content",
    "tags",
    "subject",
    "system",
    "error_type",
    "pattern_type",
    "difficulty",
    "source",
    "recall_priority",
    "revision_metadata",
    "duplicate_fingerprint",
    "embedding_metadata",
]


SchemaRegistry.register_schema(
    TemplateSchema(
        name="custom",
        required_fields=["title", "content"],
        optional_fields=["tags", "source", "difficulty", "recall_priority", "revision_metadata", "duplicate_fingerprint", "embedding_metadata"],
        canonical_fields=COMMON_FIELDS,
        content_fallback_fields=["content", "summary", "notes", "explanation"],
    )
)

SchemaRegistry.register_schema(
    TemplateSchema(
        name="coding",
        required_fields=["title", "content"],
        optional_fields=["tags", "source", "difficulty", "recall_priority", "revision_metadata", "duplicate_fingerprint", "embedding_metadata"],
        canonical_fields=COMMON_FIELDS,
        content_fallback_fields=["content", "summary", "notes", "explanation"],
    )
)

SchemaRegistry.register_schema(
    TemplateSchema(
        name="productivity",
        required_fields=["title", "content"],
        optional_fields=["tags", "source", "difficulty", "recall_priority", "revision_metadata", "duplicate_fingerprint", "embedding_metadata"],
        canonical_fields=COMMON_FIELDS,
        content_fallback_fields=["content", "summary", "notes", "explanation"],
    )
)

SchemaRegistry.register_schema(
    TemplateSchema(
        name="language",
        required_fields=["title", "content"],
        optional_fields=["tags", "source", "difficulty", "recall_priority", "revision_metadata", "duplicate_fingerprint", "embedding_metadata"],
        canonical_fields=COMMON_FIELDS,
        content_fallback_fields=["content", "summary", "notes", "explanation"],
    )
)

SchemaRegistry.register_schema(
    TemplateSchema(
        name="flashcards",
        required_fields=["title", "content"],
        optional_fields=["tags", "source", "difficulty", "recall_priority", "revision_metadata", "duplicate_fingerprint", "embedding_metadata"],
        canonical_fields=COMMON_FIELDS,
        content_fallback_fields=["content", "summary", "notes", "explanation"],
    )
)

SchemaRegistry.register_schema(
    TemplateSchema(
        name="medical",
        required_fields=["title", "content", "subject", "system", "error_type"],
        optional_fields=["tags", "pattern_type", "difficulty", "source", "recall_priority", "revision_metadata", "duplicate_fingerprint", "embedding_metadata"],
        canonical_fields=COMMON_FIELDS,
        enum_fields={
            "difficulty": ["low", "medium", "high"],
            "recall_priority": ["low", "medium", "high", "urgent"],
            "subject": [
                "Anatomy",
                "Physiology",
                "Biochemistry",
                "Pathology",
                "Pharmacology",
                "Microbiology",
                "Forensic Medicine",
                "Community Medicine (PSM)",
                "Ophthalmology",
                "Otorhinolaryngology (ENT)",
                "Medicine",
                "Surgery",
                "Obstetrics & Gynecology",
                "Pediatrics",
                "Orthopedics",
                "Dermatology",
                "Psychiatry",
                "Anesthesiology",
                "Radiology",
            ],
            "system": [
                "CVS",
                "CNS",
                "RS",
                "GIT",
                "Renal",
                "Endocrine",
                "Hematology",
                "MSK",
                "Derm",
                "Ophthal",
                "ENT",
                "Neuro",
                "Repro",
                "Eye",
                "Cardiovascular",
                "Respiratory",
                "Neurology",
                "Skin",
            ],
            "error_type": [
                "Misread question / stem",
                "Overlooked keyword (except/most/least/NOT)",
                "Confused similar concepts",
                "Incorrect elimination strategy",
                "Calculation / unit error",
                "Did not recall fact/formula",
                "Applied wrong rule/threshold (cutoff values)",
                "Image/graph interpretation error",
                "Time pressure / rushed guess",
                "Image Confusion",
                "Conceptual",
                "Silly Mistake",
                "Recall Failure",
                "Integration Failure",
                "Guessing",
                "Revision Gap",
            ],
            "pattern_type": [
                "ECG",
                "Fundus",
                "Histopathology",
                "Radiology",
                "Dermatology",
                "Gross Specimen",
                "Clinical Spotter",
            ],
        },
    )
)
