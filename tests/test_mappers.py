#!/usr/bin/env python3
"""Tests for the structured RecallItem mapping engine.""" 

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.mappers import TemplateRegistry
from core.mappers.medical_mapper import MedicalMapper
from core.mappers.recall_mapper import RecallMapper
from core.schemas import RecallItem


def test_template_registry_returns_expected_mapper() -> None:
    mapper = TemplateRegistry.get_mapper("medical")
    assert isinstance(mapper, MedicalMapper)
    assert mapper.schema.name == "medical"


def test_recall_mapper_creates_canonical_recall_item() -> None:
    mapper = RecallMapper(schema=TemplateRegistry.get_schema("custom"))
    payload: Dict[str, Any] = {
        "title": "Test Item",
        "summary": "This is a sample item generated from structured provider output.",
        "tags": ["Test", "Example"],
        "subject": "Pathology",
        "system": "CNS",
        "error_type": "Conceptual",
        "pattern_type": "Radiology",
        "difficulty": "high",
        "recall_priority": "urgent",
        "revision": {"review_date": "2026-01-01"},
    }

    item = mapper.map(payload, source="unit_test", template_type="custom")

    assert isinstance(item, RecallItem)
    assert item.title == "Test Item"
    assert "sample item" in item.content
    assert item.tags == ["example", "test"]
    assert item.subject == "Pathology"
    assert item.system == "CNS"
    assert item.error_type == "Conceptual"
    assert item.pattern_type == "Radiology"
    assert item.difficulty == "high"
    assert item.recall_priority == "urgent"
    assert item.revision_metadata["review_date"] == "2026-01-01"
    assert item.duplicate_fingerprint is not None
    assert item.metadata["provider_output"] == payload


def test_medical_mapper_enforces_required_fields() -> None:
    mapper = MedicalMapper(schema=TemplateRegistry.get_schema("medical"))
    incomplete_payload = {
        "title": "Medical Concept",
        "content": "A patient with an important concept.",
        "subject": "Medicine",
    }

    try:
        mapper.map(incomplete_payload, source="unit_test", template_type="medical")
        raise AssertionError("Expected ValueError for missing medical fields")
    except ValueError as exc:
        assert "Provider output missing required fields" in str(exc)
