"""Schema planner for adaptive Notion persistence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class SchemaPlan:
    canonical_fields: List[str]
    required_properties: Dict[str, str]
    suggested_properties: Dict[str, str]
    property_defaults: Dict[str, Any]
    safe_to_create: bool
    rationale: Optional[str] = None


class SchemaPlanner:
    """Plans canonical schema and property creation for Notion databases."""

    def plan(self, payload: Dict[str, Any], existing_schema: Optional[Dict[str, Any]] = None) -> SchemaPlan:
        """Produce a plan for mapping payload fields into Notion schema."""
        if not isinstance(payload, dict):
            raise ValueError("Payload must be a dictionary")

        canonical_fields = [
            "title",
            "content",
            "question",
            "options",
            "answer",
            "explanation",
            "memory_hook",
            "tags",
            "topic",
            "exam",
            "pyq_tags",
            "next_review_at",
            "review_state",
        ]

        required_properties = {field: "rich_text" for field in canonical_fields if field != "title"}
        required_properties["title"] = "title"

        return SchemaPlan(
            canonical_fields=canonical_fields,
            required_properties=required_properties,
            suggested_properties={field: required_properties[field] for field in canonical_fields},
            property_defaults={"review_state": "new", "strength_score": 50},
            safe_to_create=True,
            rationale="default medical revision schema",
        )
