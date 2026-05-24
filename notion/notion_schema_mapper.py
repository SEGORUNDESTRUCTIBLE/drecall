"""Schema mapper for Notion persistence and adaptive field alignment."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


COMPATIBLE_NOTION_TYPES: Dict[str, List[str]] = {
    "title": ["title"],
    "content": ["rich_text", "text"],
    "core_concept": ["rich_text", "text"],
    "memory_hook": ["rich_text", "text"],
    "trap": ["rich_text", "text"],
    "retest_question": ["rich_text", "text"],
    "exam_pearl": ["rich_text", "text"],
    "one_liner": ["rich_text", "text"],
    "image_required": ["checkbox"],
    "pyq": ["checkbox", "select"],
    "weak_topic": ["checkbox"],
    "tags": ["multi_select", "select"],
    "subject": ["select", "rich_text", "text"],
    "subtopic": ["select", "rich_text", "text"],
    "revision_metadata": ["rich_text", "text"],
}

ALIAS_MAP: Dict[str, List[str]] = {
    "title": ["title", "name", "heading"],
    "content": ["content", "notes", "description", "case"],
    "core_concept": ["core concept", "concept", "key point", "main point"],
    "memory_hook": ["memory hook", "mnemonic", "memory"],
    "trap": ["trap", "pitfall", "mistake"],
    "retest_question": ["retest", "question", "practice question", "quiz"],
    "exam_pearl": ["exam pearl", "pearl", "clinical pearl"],
    "one_liner": ["one-liner", "one liner", "summary"],
    "image_required": ["image", "visual", "scan"],
    "tags": ["tags", "labels", "categories"],
    "subject": ["subject", "discipline", "topic"],
    "subtopic": ["subtopic", "chapter", "section"],
    "weak_topic": ["weak topic", "weakness", "difficult"],
}

PROPERTY_TYPE_HINTS: Dict[str, str] = {
    "title": "title",
    "content": "rich_text",
    "core_concept": "rich_text",
    "memory_hook": "rich_text",
    "trap": "rich_text",
    "retest_question": "rich_text",
    "exam_pearl": "rich_text",
    "one_liner": "rich_text",
    "image_required": "checkbox",
    "pyq": "checkbox",
    "weak_topic": "checkbox",
    "tags": "multi_select",
    "subject": "select",
    "subtopic": "select",
    "revision_metadata": "rich_text",
}


@dataclass(frozen=True)
class SchemaMappingReport:
    mapping: Dict[str, str]
    missing: List[str]
    type_conflicts: Dict[str, str]
    suggested_creations: Dict[str, str]
    score: float
    rationale: Optional[str] = None


class NotionSchemaMapper:
    """Maps canonical revision fields to existing Notion database schema."""

    def inspect(self, properties: Dict[str, Any], canonical_fields: List[str]) -> SchemaMappingReport:
        """Inspect a Notion schema and produce a compatibility report."""
        mapping: Dict[str, str] = {}
        missing: List[str] = []
        type_conflicts: Dict[str, str] = {}
        suggested_creations: Dict[str, str] = {}

        normalized_props = {
            prop_name.lower(): (prop_name, prop_config.get("type"))
            for prop_name, prop_config in (properties or {}).items()
        }

        for field in canonical_fields:
            alias_list = ALIAS_MAP.get(field, [field])
            found = False
            for alias in alias_list:
                for normalized_name, (prop_name, prop_type) in normalized_props.items():
                    if alias in normalized_name:
                        field_type = PROPERTY_TYPE_HINTS.get(field, "rich_text")
                        if prop_type not in COMPATIBLE_NOTION_TYPES.get(field, [prop_type]):
                            type_conflicts[field] = f"{prop_name}:{prop_type}"
                        mapping[field] = prop_name
                        found = True
                        break
                if found:
                    break
            if not found:
                missing.append(field)
                suggested_creations[field] = PROPERTY_TYPE_HINTS.get(field, "rich_text")

        score = 1.0 - (len(missing) / max(len(canonical_fields), 1))
        if score < 0:
            score = 0.0

        return SchemaMappingReport(
            mapping=mapping,
            missing=missing,
            type_conflicts=type_conflicts,
            suggested_creations=suggested_creations,
            score=score,
            rationale="automatic semantic field alignment",
        )

    def plan_updates(self, report: SchemaMappingReport) -> Dict[str, Any]:
        """Return a plan for schema updates based on the inspection report."""
        return {field: property_type for field, property_type in report.suggested_creations.items()}

    @staticmethod
    def is_field_compatible(field: str, notion_type: str) -> bool:
        return notion_type in COMPATIBLE_NOTION_TYPES.get(field, ["rich_text"])
