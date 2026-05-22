#!/usr/bin/env python3
"""Dry-run ingestion pipeline tests for dRecall.

This test suite validates the ingestion pipeline without external APIs or Notion.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List

# Ensure repo root is on sys.path when running this file directly.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.ingestion_engine import IngestionEngine
from core.schemas import RecallItem


def print_header(title: str) -> None:
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def test_full_dry_run_ingestion() -> None:
    print_header("TEST 1: Full Dry-Run Ingestion Flow")

    engine = IngestionEngine(template_type="structured_learning")
    item = engine.ingest_text(
        text="Hypertension is a chronic condition characterized by elevated blood pressure.",
        title="Hypertension Overview",
        tags=["Health", "  Review "],
        source="lecture_notes",
    )

    print(f"Created RecallItem: {item}")
    print(f"  title={item.title}")
    print(f"  content={item.content}")
    print(f"  tags={item.tags}")
    print(f"  metadata keys={list(item.metadata.keys())}")

    assert isinstance(item, RecallItem)
    assert item.title == "Hypertension Overview"
    assert "hypertension" in item.content.lower()
    assert item.tags == ["health", "review"]
    assert "provider_output" in item.metadata
    assert isinstance(item.metadata["provider_output"], dict)

    print("✓ Full ingestion dry-run passed")


def test_file_ingestion() -> None:
    print_header("TEST 2: File Ingestion Flow")

    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = Path(temp_dir) / "study_notes.txt"
        file_path.write_text("Chronic kidney disease is characterized by progressive loss of renal function.")

        engine = IngestionEngine(template_type="structured_learning")
        item = engine.ingest_file(str(file_path), source="file_import")

        assert isinstance(item, RecallItem)
        assert item.title == "Study Notes"
        assert item.source == "file_import"
        assert item.metadata["provider_output"]

    print("✓ File ingestion dry-run passed")


def test_mock_provider_integration() -> None:
    print_header("TEST 3: Mock Provider Integration")

    class CustomMockProvider:
        def generate(self, prompt: str, system_prompt: str = "") -> str:
            return '{"generated":"ok","notes":["sample"]}'

    engine = IngestionEngine(template_type="flashcards", provider=CustomMockProvider())
    item = engine.ingest_text(
        text="Photosynthesis converts light energy into chemical energy.",
        title="Photosynthesis",
    )

    assert item.metadata["provider_output"]["generated"] == "ok"
    assert item.metadata["provider_output"]["notes"] == ["sample"]

    print("✓ Mock provider integration passed")


def test_json_parsing_error() -> None:
    print_header("TEST 4: Malformed JSON Handling")

    class BrokenResponseProvider:
        def generate(self, prompt: str, system_prompt: str = "") -> str:
            return "{ invalid json }"

    engine = IngestionEngine(template_type="structured_learning", provider=BrokenResponseProvider())

    try:
        engine.ingest_text(text="A test note.", title="JSON Failure")
        raise AssertionError("Expected ValueError for malformed JSON response")
    except ValueError as exc:
        assert "Provider response validation failed" in str(exc)
        print(f"✓ Malformed JSON correctly raised ValueError: {exc}")


def test_missing_field_handling() -> None:
    print_header("TEST 5: Missing Structured Payload Handling")

    class EmptyResponseProvider:
        def generate(self, prompt: str, system_prompt: str = "") -> str:
            return "{}"

    engine = IngestionEngine(template_type="mistake_tracking", provider=EmptyResponseProvider())

    try:
        engine.ingest_text(text="A short note for testing.", title="Empty Response")
        raise AssertionError("Expected ValueError for empty provider payload")
    except ValueError as exc:
        assert "Provider response validation failed" in str(exc)
        print(f"✓ Empty JSON payload correctly raised ValueError: {exc}")


def test_invalid_text_handling() -> None:
    print_header("TEST 6: Invalid Input Handling")

    engine = IngestionEngine(template_type="structured_learning")
    try:
        engine.ingest_text(text="   ", title="Invalid")
        raise AssertionError("Expected ValueError for empty text input")
    except ValueError as exc:
        assert "non-empty string" in str(exc)
        print(f"✓ Empty text input correctly raised ValueError: {exc}")


def test_batch_ingestion() -> None:
    print_header("TEST 7: Batch Ingestion")

    engine = IngestionEngine(template_type="structured_learning")
    items: List[Dict[str, Any]] = [
        {"text": "Note one for batch ingestion.", "title": "Batch One"},
        {"text": "Note two for batch ingestion.", "title": "Batch Two"},
    ]

    results = engine.ingest_batch(items)
    assert len(results) == 2
    assert all(isinstance(item, RecallItem) for item in results)

    print("✓ Batch ingestion passed")


def main() -> int:
    test_full_dry_run_ingestion()
    test_file_ingestion()
    test_mock_provider_integration()
    test_json_parsing_error()
    test_missing_field_handling()
    test_invalid_text_handling()
    test_batch_ingestion()

    print_header("ALL INGESTION PIPELINE CHECKS COMPLETED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
