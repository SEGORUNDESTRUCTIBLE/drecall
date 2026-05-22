#!/usr/bin/env python3
"""RecallItem schema validation tests for drecall.

These tests validate production-style Pydantic behavior for the RecallItem
schema, including creation, defaults, serialization, deserialization, and
error handling.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from pydantic import ValidationError

# Ensure repo root is on sys.path when running this file directly.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.schemas import RecallItem


def print_header(title: str) -> None:
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def test_valid_recall_item_creation() -> None:
    print_header("TEST 1: Valid RecallItem Creation")

    item = RecallItem(
        title="Memory Schema Test",
        content="This is a recall item used to validate the schema.",
        source="unittest",
        template_type="coding",
        tags=["test", "recall"],
        metadata={"priority": "high", "category": "validation"},
    )

    print(f"Created RecallItem: {item}")
    print(f"  title={item.title}")
    print(f"  content={item.content}")
    print(f"  source={item.source}")
    print(f"  template_type={item.template_type}")
    print(f"  tags={item.tags}")
    print(f"  metadata={item.metadata}")

    assert item.title == "Memory Schema Test"
    assert item.content.startswith("This is a recall item")
    assert item.source == "unittest"
    assert item.template_type == "coding"
    assert item.tags == ["test", "recall"]
    assert item.metadata["priority"] == "high"
    assert item.metadata["category"] == "validation"
    assert item.created_at <= datetime.now(timezone.utc)
    assert item.updated_at <= datetime.now(timezone.utc)

    print("✓ Valid RecallItem created and fields validated")


def test_missing_required_fields() -> None:
    print_header("TEST 2: Missing Required Fields")

    try:
        RecallItem(content="Missing title field")
        raise AssertionError("Expected ValidationError for missing title")
    except ValidationError as exc:
        errors = exc.errors()
        assert any(error["loc"] == ("title",) for error in errors), (
            "ValidationError should report missing title"
        )
        print(f"✓ Missing title correctly raised ValidationError: {errors}")

    try:
        RecallItem(title="Missing content")
        raise AssertionError("Expected ValidationError for missing content")
    except ValidationError as exc:
        errors = exc.errors()
        assert any(error["loc"] == ("content",) for error in errors), (
            "ValidationError should report missing content"
        )
        print(f"✓ Missing content correctly raised ValidationError: {errors}")

    print("✓ Required-field validation behavior confirmed")


def test_default_values() -> None:
    print_header("TEST 3: Default Values")

    item = RecallItem(title="Default values", content="Check defaults")

    print(f"RecallItem defaults: template_type={item.template_type}, tags={item.tags}")
    print(f"  processed={item.processed}, enhanced={item.enhanced}")
    print(f"  source={item.source}, notion_page_id={item.notion_page_id}")
    print(f"  metadata={item.metadata}")

    assert item.id is None
    assert item.source is None
    assert item.template_type == "custom"
    assert item.tags == []
    assert item.processed is False
    assert item.enhanced is False
    assert item.notion_page_id is None
    assert item.metadata == {}
    assert isinstance(item.created_at, datetime)
    assert isinstance(item.updated_at, datetime)
    assert item.updated_at >= item.created_at

    print("✓ Default values are applied correctly")


def test_serialization_deserialization() -> None:
    print_header("TEST 4: Serialization and Deserialization")

    item = RecallItem(
        title="Serialization Test",
        content="Verify JSON round-trip.",
        tags=["json"],
        metadata={"stage": "serialization"},
    )

    dumped = item.model_dump(mode="json")
    json_text = item.model_dump_json()

    print(f"Serialized dict keys: {list(dumped.keys())}")
    print(f"Serialized JSON length: {len(json_text)}")

    roundtrip_from_dict = RecallItem.model_validate(dumped)
    roundtrip_from_json = RecallItem.model_validate_json(json_text)

    assert roundtrip_from_dict.title == item.title
    assert roundtrip_from_dict.content == item.content
    assert roundtrip_from_dict.tags == item.tags
    assert roundtrip_from_dict.metadata == item.metadata

    assert roundtrip_from_json.title == item.title
    assert roundtrip_from_json.content == item.content
    assert roundtrip_from_json.tags == item.tags
    assert roundtrip_from_json.metadata == item.metadata

    print("✓ Serialization and deserialization round-trips succeeded")


def test_invalid_field_types() -> None:
    print_header("TEST 5: Invalid Field Types")

    try:
        RecallItem(
            title="Invalid types",
            content="This should fail",
            tags=123,
            created_at="not-a-timestamp",
        )
        raise AssertionError("Expected ValidationError for invalid field types")
    except ValidationError as exc:
        errors = exc.errors()
        locs = {error["loc"][0] for error in errors}
        assert "tags" in locs or "created_at" in locs
        assert any(
            "tags" == error["loc"][0] for error in errors
        ) or any(
            "created_at" == error["loc"][0] for error in errors
        )
        print(f"✓ Invalid field types raised ValidationError: {errors}")

    print("✓ Invalid type validation behavior is correct")


def test_pydantic_validation_behavior() -> None:
    print_header("TEST 6: Pydantic Validation Behavior")

    raw_payload: Dict[str, Any] = {
        "title": "Payload Validation",
        "content": "Pydantic should coerce valid values and reject invalid ones.",
        "tags": ["payload"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    item = RecallItem.model_validate(raw_payload)
    assert item.title == raw_payload["title"]
    assert item.tags == ["payload"]

    try:
        RecallItem.model_validate({"title": None, "content": 123})
        raise AssertionError("Expected ValidationError for invalid raw payload")
    except ValidationError as exc:
        errors = exc.errors()
        assert any(error["loc"] == ("title",) for error in errors)
        assert any(error["loc"] == ("content",) for error in errors)
        print(f"✓ Raw payload validation raised ValidationError: {errors}")

    print("✓ Pydantic validation behavior confirmed for external payloads")


def main() -> int:
    test_valid_recall_item_creation()
    test_missing_required_fields()
    test_default_values()
    test_serialization_deserialization()
    test_invalid_field_types()
    test_pydantic_validation_behavior()

    print_header("ALL RecallItem SCHEMA VALIDATION CHECKS COMPLETED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
