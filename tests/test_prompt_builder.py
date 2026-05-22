#!/usr/bin/env python3
"""Prompt builder tests for drecall.

Validates template loading, rendering, schema metadata, missing placeholders,
invalid templates, and malformed template files.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict

# Ensure repo root is on sys.path when running this file directly.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.prompt_builder import (
    PromptBuilder,
    TemplateLoader,
    TemplateNotFoundError,
    TemplateRenderError,
    TemplateSchemaError,
)
from core.schemas import RecallItem


def print_header(title: str) -> None:
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def test_template_loading() -> None:
    print_header("TEST 1: Template Loading")

    loader = TemplateLoader()
    categories = loader.get_categories()

    assert "structured_learning" in categories, "structured_learning category should be available"
    assert "mistake_tracking" in categories, "mistake_tracking category should be available"
    assert "flashcards" in categories, "flashcards category should be available"

    template = loader.load("structured_learning")

    print(f"Loaded template from: {template.template_path}")
    print(f"Template text begins with: {template.prompt_text.splitlines()[0]}")
    print(f"Schema keys: {list(template.schema.keys())}")

    assert template.category == "structured_learning"
    assert template.schema["template_name"] == "Structured Learning"
    assert template.schema["output_format"] == "json"
    assert isinstance(template.schema["supported_input_types"], list)
    assert "revision_support" in template.schema

    print("✓ Template loading passed")


def test_prompt_rendering() -> None:
    print_header("TEST 2: Prompt Rendering")

    builder = PromptBuilder("structured_learning")
    item = RecallItem(
        title="Hypertension Notes",
        content="Patient presents with elevated blood pressure and headache.",
        source="ocr_scan",
    )
    prompt = builder.build_prompt(
        item,
        instruction="Transform the notes into a structured learning JSON object.",
    )

    print(f"Rendered prompt sample:\n{prompt[:320]}...")
    assert "Hypertension Notes" in prompt
    assert "Raw Content" in prompt
    assert "Transform the notes into a structured learning JSON object." in prompt
    assert "{{" not in prompt and "}}" not in prompt
    assert "structured learning" in prompt.lower()

    print("✓ Prompt rendering passed")


def test_variable_injection() -> None:
    print_header("TEST 3: Variable Injection")

    builder = PromptBuilder("mistake_tracking")
    item = RecallItem(
        title="Anatomy Note",
        content="The artery carries blood to the heart.",
        source="class_notes",
    )
    prompt = builder.build_prompt(
        item,
        instruction="Identify mistakes in the note and suggest corrections.",
        extra_note="Focus on factual accuracy.",
    )

    assert "Anatomy Note" in prompt
    assert "class_notes" in prompt
    assert "Focus on factual accuracy." in prompt
    assert prompt.count("{{") == 0

    print("✓ Variable injection passed")


def test_missing_placeholders() -> None:
    print_header("TEST 4: Missing Placeholder Validation")

    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        category_dir = root / "broken"
        category_dir.mkdir(parents=True)
        (category_dir / "prompt.txt").write_text("This prompt expects {{missing_variable}}.")
        (category_dir / "schema.json").write_text(
            json.dumps({
                "template_name": "Broken Placeholder",
                "description": "Template used to validate missing placeholder handling.",
                "supported_input_types": ["text"],
                "output_format": "json",
                "tags": ["broken", "placeholder"],
                "revision_support": False,
                "required": ["missing_variable"],
            })
        )

        loader = TemplateLoader(templates_root=root)
        template = loader.load("broken")

        try:
            template.render({"instruction": "Test"})
            raise AssertionError("Expected TemplateRenderError when variables are missing")
        except TemplateRenderError as exc:
            assert "missing_variable" in str(exc)
            print(f"✓ Missing placeholder raised TemplateRenderError: {exc}")

    print("✓ Missing placeholder validation passed")


def test_invalid_templates() -> None:
    print_header("TEST 5: Invalid Template Category")

    loader = TemplateLoader()
    try:
        loader.load("nonexistent")
        raise AssertionError("Expected TemplateNotFoundError for invalid template category")
    except TemplateNotFoundError as exc:
        print(f"✓ Invalid template category raised TemplateNotFoundError: {exc}")

    print("✓ Invalid template handling passed")


def test_malformed_template_files() -> None:
    print_header("TEST 6: Malformed Template Files")

    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        category_dir = root / "broken-json"
        category_dir.mkdir(parents=True)
        (category_dir / "prompt.txt").write_text("Approved prompt with {{instruction}}.")
        (category_dir / "schema.json").write_text("{ invalid json }")

        loader = TemplateLoader(templates_root=root)
        try:
            loader.load("broken-json")
            raise AssertionError("Expected TemplateSchemaError for malformed template schema")
        except TemplateSchemaError as exc:
            print(f"✓ Malformed schema raised TemplateSchemaError: {exc}")

    print("✓ Malformed template file handling passed")


def test_schema_loading() -> None:
    print_header("TEST 7: Schema Loading")

    loader = TemplateLoader()
    template = loader.load("flashcards")
    schema = template.schema

    assert schema["template_name"] == "Flashcards"
    assert schema["output_format"] == "json"
    assert isinstance(schema["supported_input_types"], list)
    assert schema["revision_support"] is True
    assert "question" in schema["tags"] or "review" in schema["tags"]

    print("✓ Schema metadata loaded and validated")


def test_system_prompt_rendering() -> None:
    print_header("TEST 8: System Prompt Rendering")

    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        category_dir = root / "system"
        category_dir.mkdir(parents=True)
        (category_dir / "prompt.txt").write_text(
            "System context: {{instruction}}"
        )
        (category_dir / "schema.json").write_text(
            json.dumps({
                "template_name": "System Prompt",
                "description": "Minimal system prompt template for testing.",
                "supported_input_types": ["text"],
                "output_format": "json",
                "tags": ["system", "prompt"],
                "revision_support": False,
                "required": [],
            })
        )

        builder = PromptBuilder(template_type="system", templates_root=root)
        prompt = builder.build_system_prompt(instruction="Use no extra text.")

        assert "Use no extra text." in prompt
        assert "{{" not in prompt

        print("✓ System prompt rendering passed")


def main() -> int:
    test_template_loading()
    test_prompt_rendering()
    test_variable_injection()
    test_missing_placeholders()
    test_invalid_templates()
    test_malformed_template_files()
    test_schema_loading()
    test_system_prompt_rendering()

    print_header("ALL PROMPT BUILDER VALIDATION CHECKS COMPLETED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
