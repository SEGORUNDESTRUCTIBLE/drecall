"""Prompt construction and management.

Builds optimized prompts for AI providers with template support.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Pattern, Set

from .schemas import RecallItem

logger = logging.getLogger(__name__)

PLACEHOLDER_PATTERN: Pattern[str] = re.compile(r"{{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*}}")
REQUIRED_TEMPLATE_METADATA = {
    "template_name",
    "description",
    "supported_input_types",
    "output_format",
    "tags",
    "revision_support",
}


class TemplateError(RuntimeError):
    """Base exception for template-loading failures."""


class TemplateNotFoundError(TemplateError):
    """Raised when a requested template category does not exist."""


class TemplateSchemaError(TemplateError):
    """Raised when template schema metadata is invalid or malformed."""


class TemplateRenderError(TemplateError):
    """Raised when a template cannot be rendered because variables are missing."""


class PromptTemplate:
    """Wrapper for a loaded prompt template and its metadata."""

    def __init__(
        self,
        category: str,
        prompt_text: str,
        schema: Dict[str, Any],
        template_path: Path,
    ) -> None:
        self.category = category
        self.prompt_text = prompt_text
        self.schema = schema
        self.template_path = template_path
        self._validate_schema_metadata(schema)
        self.placeholders = self._extract_placeholders(prompt_text)
        self._validate_placeholders(prompt_text)

    @staticmethod
    def _validate_schema_metadata(schema: Dict[str, Any]) -> None:
        missing = sorted(REQUIRED_TEMPLATE_METADATA - set(schema.keys()))
        if missing:
            raise TemplateSchemaError(
                f"Template schema is missing required metadata fields: {', '.join(missing)}"
            )

        if not isinstance(schema["template_name"], str):
            raise TemplateSchemaError("template_name must be a string")
        if not isinstance(schema["description"], str):
            raise TemplateSchemaError("description must be a string")
        if not isinstance(schema["supported_input_types"], list):
            raise TemplateSchemaError("supported_input_types must be a list")
        if not isinstance(schema["output_format"], str):
            raise TemplateSchemaError("output_format must be a string")
        if not isinstance(schema["tags"], list):
            raise TemplateSchemaError("tags must be a list")
        if not isinstance(schema["revision_support"], bool):
            raise TemplateSchemaError("revision_support must be a boolean")

    @staticmethod
    def _extract_placeholders(prompt_text: str) -> Set[str]:
        return {match.group(1) for match in PLACEHOLDER_PATTERN.finditer(prompt_text)}

    @staticmethod
    def _validate_placeholders(prompt_text: str) -> None:
        for candidate in re.finditer(r"{{.*?}}", prompt_text):
            if PLACEHOLDER_PATTERN.fullmatch(candidate.group(0)) is None:
                raise TemplateSchemaError(
                    f"Malformed placeholder '{candidate.group(0)}' in template {candidate.string}"
                )

    def render(self, variables: Dict[str, Any]) -> str:
        missing = sorted(self.placeholders - set(variables.keys()))
        if missing:
            raise TemplateRenderError(
                f"Missing variables for template '{self.category}': {', '.join(missing)}"
            )

        def replace(match: re.Match[str]) -> str:
            value = variables.get(match.group(1), "")
            return str(value if value is not None else "")

        return PLACEHOLDER_PATTERN.sub(replace, self.prompt_text)


class TemplateLoader:
    """Loads prompt templates from the templates directory."""

    def __init__(self, templates_root: Optional[Path] = None) -> None:
        self.templates_root = (
            templates_root
            if templates_root is not None
            else Path(__file__).resolve().parents[1] / "templates"
        )

    def get_categories(self) -> List[str]:
        if not self.templates_root.exists():
            return []

        categories = []
        for category in self.templates_root.iterdir():
            if not category.is_dir():
                continue
            prompt_file = category / "prompt.txt"
            schema_file = category / "schema.json"
            if prompt_file.exists() and schema_file.exists():
                categories.append(category.name)
        return sorted(categories)

    def validate_template_exists(self, category: str) -> None:
        category_dir = self.templates_root / category
        if not category_dir.exists() or not category_dir.is_dir():
            raise TemplateNotFoundError(
                f"Template category '{category}' does not exist."
            )

        prompt_file = category_dir / "prompt.txt"
        schema_file = category_dir / "schema.json"
        if not prompt_file.exists():
            raise TemplateNotFoundError(
                f"Missing prompt.txt for template category '{category}'."
            )
        if not schema_file.exists():
            raise TemplateNotFoundError(
                f"Missing schema.json for template category '{category}'."
            )

    def load(self, category: str) -> PromptTemplate:
        self.validate_template_exists(category)
        category_dir = self.templates_root / category
        prompt_file = category_dir / "prompt.txt"
        schema_file = category_dir / "schema.json"

        if not prompt_file.exists():
            raise TemplateNotFoundError(
                f"Missing prompt file for template category '{category}'."
            )
        if not schema_file.exists():
            raise TemplateNotFoundError(
                f"Missing schema.json for template category '{category}'."
            )

        try:
            prompt_text = prompt_file.read_text(encoding="utf-8")
        except OSError as exc:
            logger.error("Failed to read prompt file %s", prompt_file)
            raise TemplateError("Unable to read prompt file") from exc

        try:
            schema = json.loads(schema_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            logger.error("Malformed JSON schema in %s", schema_file)
            raise TemplateSchemaError(
                f"Template schema file is not valid JSON: {schema_file}"
            ) from exc

        if not isinstance(schema, dict):
            raise TemplateSchemaError("Template schema must be a JSON object.")

        return PromptTemplate(category=category, prompt_text=prompt_text, schema=schema, template_path=category_dir)


class PromptBuilder:
    """Builder for constructing AI prompts from templates."""

    def __init__(
        self,
        template_type: str = "custom",
        templates_root: Optional[Path] = None,
    ) -> None:
        self.template_type = template_type
        self.loader = TemplateLoader(templates_root=templates_root)
        self.template = self.loader.load(template_type)

    def build_prompt(
        self,
        item: RecallItem,
        instruction: str,
        **context: Any,
    ) -> str:
        if not instruction:
            raise ValueError("instruction is required to build a prompt")

        variables = self._build_context(item, context)
        variables["instruction"] = instruction

        rendered = self.template.render(variables)
        # Append deterministic strict JSON enforcement to every prompt to
        # force providers to return canonical JSON only (no fences, no prose).
        rendered += "\n\n" + self._strict_json_instructions()
        return rendered

    def _strict_json_instructions(self) -> str:
        """Return a deterministic, strict JSON instruction block appended to prompts.

        This enforces provider-side structured output and lists the canonical
        RecallItem fields to avoid name mismatch.
        """
        # Use RecallItem model fields as the canonical set of allowed keys.
        recall_fields = sorted(list(RecallItem.model_fields.keys()))
        fields_list = ", ".join(recall_fields)

        instructions = (
            "IMPORTANT: Return ONLY valid JSON. DO NOT include any explanatory "
            "text, headings, markdown, or code fences. Do not include any content "
            "outside the single JSON payload.\n"
            "- The response must be a single JSON object (or array only when the "
            "template explicitly requires it).\n"
            "- Use these exact field names if present: "
            f"{fields_list}.\n"
            "- Use ISO 8601 for timestamps (e.g. 2023-01-01T12:00:00Z).\n"
            "- Do not wrap the JSON in backticks or code fences.\n"
            "- Do not prepend or append any prose, explanation, or commentary.\n"
            "- If a field cannot be inferred, return an empty string or empty array.\n"
            "- Return the JSON only and nothing else.\n"
            "Example minimal output: {\"title\": \"...\", \"content\": \"...\"}\n"
        )
        return instructions

    def build_system_prompt(
        self,
        template_type: Optional[str] = None,
        **context: Any,
    ) -> str:
        template = self.template
        if template_type is not None and template_type != self.template_type:
            template = self.loader.load(template_type)

        variables = {"instruction": context.pop("instruction", ""), **context}
        return template.render(variables)

    def build_revision_prompt(self, item: RecallItem, **context: Any) -> str:
        revision_instruction = (
            "Revise the following recall item for clarity, completeness, and accuracy "
            "while maintaining the original meaning."
        )
        return self.build_prompt(item, revision_instruction, **context)

    @staticmethod
    def _build_context(item: RecallItem, context: Dict[str, Any]) -> Dict[str, Any]:
        item_context = item.model_dump(mode="python")
        if not isinstance(item_context, dict):
            raise TemplateError("Unable to extract variables from RecallItem.")

        rendered_context = dict(item_context)
        rendered_context.update(context)
        return rendered_context
