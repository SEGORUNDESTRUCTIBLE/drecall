"""Data ingestion engine.

Handles importing and processing data from various sources into recall items.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from .mappers import TemplateRegistry
from .normalizers import Normalizer
from .prompt_builder import PromptBuilder
from .schemas import RecallItem
from .validators import Validator
from .parsing.json_sanitizer import sanitize_and_parse
from core.contracts.provider_contracts import ProviderResponse as ProviderContractResponse

logger = logging.getLogger(__name__)


class MockProvider:
    """Simulates provider responses for dry-run ingestion."""

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Return simulated JSON output for a rendered prompt."""
        prompt_lower = prompt.lower()
        if "flashcards" in prompt_lower:
            response = {
                "cards": [
                    {
                        "question": "What is the main takeaway?",
                        "answer": "A structured study path helps retention.",
                        "category": "learning",
                    }
                ]
            }
        elif "mistake" in prompt_lower or "errors" in prompt_lower:
            response = {
                "issues": ["Ambiguous sentence structure"],
                "causes": ["Note contains unclear terminology"],
                "corrections": ["Clarify the language and preserve meaning"],
                "confidence": "high",
            }
        else:
            response = {
                "topic": "Structured Knowledge",
                "key_points": [
                    "Extract the main concepts",
                    "Capture examples and next steps",
                ],
                "examples": ["Example usage of the concept."],
                "summary": "A concise study object is generated.",
                "next_steps": ["Review the extracted key points."],
            }
        return json.dumps(response)


class IngestionEngine:
    """Engine for ingesting and normalizing raw input into RecallItem objects."""

    def __init__(
        self,
        template_type: str = "structured_learning",
        prompt_builder: Optional[PromptBuilder] = None,
        validator: Optional[Validator] = None,
        normalizer: Optional[Normalizer] = None,
        provider: Optional[Any] = None,
        mapper: Optional[Any] = None,
        templates_root: Optional[Path] = None,
    ) -> None:
        self.template_type = template_type
        self.validator = validator or Validator()
        self.normalizer = normalizer or Normalizer()
        self.provider = provider or MockProvider()
        self.prompt_builder = (
            prompt_builder
            if prompt_builder is not None
            else PromptBuilder(template_type=template_type, templates_root=templates_root)
        )
        self.mapper = mapper or TemplateRegistry.get_mapper(template_type)

    def ingest_text(
        self,
        text: str,
        title: Optional[str] = None,
        template_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        source: Optional[str] = None,
        instruction: Optional[str] = None,
    ) -> RecallItem:
        """Ingest plain text through a dry-run pipeline."""
        self._log_stage("Raw input received")

        if not isinstance(text, str) or not text.strip():
            raise ValueError("Text content must be a non-empty string")

        normalized_text = self.normalizer.normalize_text(text)
        normalized_title = self.normalizer.normalize_title(title or self._generate_title(normalized_text))
        normalized_tags = self.normalizer.normalize_tags(tags or [])
        normalized_source = source.strip() if isinstance(source, str) and source.strip() else None
        selected_template = template_type or self.template_type

        self._log_stage("Template selection")
        if selected_template != self.prompt_builder.template_type:
            self.prompt_builder = PromptBuilder(template_type=selected_template)

        self._log_stage("Prompt rendering")
        prompt_instruction = instruction or self._get_default_instruction(selected_template)
        prompt = self.prompt_builder.build_prompt(
            RecallItem(
                title=normalized_title,
                content=normalized_text,
                source=normalized_source,
                template_type=selected_template,
                tags=normalized_tags,
            ),
            instruction=prompt_instruction,
            extra_note="dry-run ingestion",
        )

        provider_name = self.provider.__class__.__name__
        self._log_stage(f"Provider response from {provider_name}")
        provider_output = None
        try:
            try:
                provider_output = self.provider.generate(prompt, expect_json=True)
            except TypeError:
                provider_output = self.provider.generate(prompt)
        except Exception as exc:
            logger.error("Provider generation failed: %s", exc)
            raise

        parsed = None
        sanitized_preview = None
        raw_text = None

        if isinstance(provider_output, ProviderContractResponse):
            if provider_output.error:
                raise RuntimeError(provider_output.error or "Provider returned failed response")
            parsed = getattr(provider_output, 'parsed', None)
            raw_text = getattr(provider_output, 'raw_text', None)
            if parsed is not None:
                sanitized_preview = json.dumps(parsed)

        if parsed is None and isinstance(provider_output, (dict, list)):
            parsed = provider_output
            sanitized_preview = json.dumps(provider_output)

        if parsed is None:
            raw_text = raw_text if isinstance(raw_text, str) else (provider_output if isinstance(provider_output, str) else str(provider_output))
            logger.debug("[IngestionEngine] provider raw preview=%s", (raw_text or '')[:300].replace('\n', ' '))
            parsed, sanitized_preview = sanitize_and_parse(raw_text)

        # If parsing still failed, attempt a single recovery prompt to the provider
        if parsed is None:
            logger.warning("[IngestionEngine] initial JSON parse failed, attempting recovery prompt")
            recovery_instruction = "Return ONLY valid JSON matching the schema. Do not include any markdown, code fences, or explanation."
            recovery_prompt = self.prompt_builder.build_prompt(
                RecallItem(
                    title=normalized_title,
                    content=normalized_text,
                    source=normalized_source,
                    template_type=selected_template,
                    tags=normalized_tags,
                ),
                instruction=recovery_instruction,
                extra_note="recovery attempt",
            )
            try:
                try:
                    recovery_output = self.provider.generate(recovery_prompt, expect_json=True)
                except TypeError:
                    recovery_output = self.provider.generate(recovery_prompt)
            except Exception as exc:
                logger.error("Provider recovery attempt failed: %s", exc)
                raise RuntimeError("Provider recovery attempt failed") from exc

            if isinstance(recovery_output, ProviderContractResponse):
                if not recovery_output.ok:
                    raise RuntimeError(recovery_output.error or "Recovery provider returned failed response")
                parsed = recovery_output.parsed
                raw_text = recovery_output.raw_text
                if parsed is not None:
                    sanitized_preview = json.dumps(parsed)
                else:
                    parsed, sanitized_preview = sanitize_and_parse(raw_text)
            elif isinstance(recovery_output, (dict, list)):
                parsed = recovery_output
                sanitized_preview = json.dumps(recovery_output)
            else:
                parsed, sanitized_preview = sanitize_and_parse(str(recovery_output))

        logger.debug("[IngestionEngine] sanitized preview=%s", (sanitized_preview or '')[:300].replace('\n', ' '))

        # Final validation of parsed provider data
        if parsed is None:
            raise ValueError("Provider response validation failed: unable to parse JSON after sanitization and recovery")

        # Ensure structured data is valid according to existing validators
        valid_response, error_message = True, None
        # Validator expects raw string; reuse validate_structured_json for parsed data
        is_structured_valid, errors = self.validator.validate_structured_json(parsed)
        if not is_structured_valid:
            raise ValueError(f"Provider response validation failed: {'; '.join(errors)}")

        structured_data = parsed

        self._log_stage("RecallItem mapping")
        if isinstance(structured_data, list):
            structured_data = {"items": structured_data}

        if not structured_data.get("title"):
            structured_data["title"] = normalized_title

        if normalized_tags and not structured_data.get("tags"):
            structured_data["tags"] = normalized_tags

        structured_data["_fallback_content"] = normalized_text

        if not any(key in structured_data for key in ["content", "summary", "notes", "explanation"]):
            structured_data["content"] = normalized_text

        self.mapper = TemplateRegistry.get_mapper(selected_template)
        recall_item = self.mapper.map(
            structured_data,
            source=normalized_source,
            template_type=selected_template,
        )

        self._log_stage("RecallItem validation")
        is_valid, errors = self.validator.validate_recall_item(recall_item)
        if not is_valid:
            raise ValueError(f"RecallItem validation failed: {errors}")

        self._log_stage("Normalization")
        recall_item = self._normalize_recall_item(recall_item)

        self._log_stage("Final structured RecallItem output")
        return recall_item

    def ingest_file(
        self,
        file_path: str,
        template_type: Optional[str] = None,
        **kwargs: Any,
    ) -> RecallItem:
        self._log_stage(f"Ingesting file: {file_path}")
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"File not found: {file_path}")

        text = path.read_text(encoding="utf-8")
        title = kwargs.pop("title", path.stem)
        return self.ingest_text(
            text=text,
            title=title,
            template_type=template_type or self.template_type,
            tags=kwargs.get("tags"),
            source=kwargs.get("source"),
            instruction=kwargs.get("instruction"),
        )

    def ingest_batch(
        self,
        items: List[Dict[str, Any]],
        template_type: Optional[str] = None,
    ) -> List[RecallItem]:
        self._log_stage("Starting batch ingestion")
        results: List[RecallItem] = []
        errors: List[str] = []

        for index, item in enumerate(items):
            try:
                results.append(
                    self.ingest_text(
                        text=item.get("text", ""),
                        title=item.get("title"),
                        template_type=item.get("template_type", template_type or self.template_type),
                        tags=item.get("tags"),
                        source=item.get("source"),
                        instruction=item.get("instruction"),
                    )
                )
            except Exception as exc:
                error_message = f"Batch item {index} failed: {exc}"
                logger.error(error_message)
                errors.append(error_message)

        if errors:
            raise ValueError(f"Batch ingestion failed: {errors}")

        return results

    def _build_recall_item(
        self,
        title: str,
        content: str,
        source: Optional[str],
        tags: List[str],
        template_type: str,
        provider_payload: Any,
    ) -> RecallItem:
        return RecallItem(
            title=title,
            content=content,
            source=source,
            tags=tags,
            template_type=template_type,
            metadata={"provider_output": provider_payload},
        )

    def _normalize_recall_item(self, item: RecallItem) -> RecallItem:
        cleaned_metadata = self.normalizer.normalize_metadata(item.metadata)
        normalized_fields = {
            "title": self.normalizer.normalize_title(item.title),
            "content": self.normalizer.normalize_text(item.content),
            "source": item.source.strip() if item.source else None,
            "tags": self.normalizer.normalize_tags(item.tags),
            "subject": self.normalizer.normalize_subject(item.subject),
            "system": self.normalizer.normalize_system(item.system),
            "error_type": self.normalizer.normalize_error_type(item.error_type),
            "pattern_type": self.normalizer.normalize_pattern_type(item.pattern_type),
            "difficulty": self.normalizer.normalize_difficulty(item.difficulty),
            "recall_priority": self.normalizer.normalize_priority(item.recall_priority),
            "metadata": cleaned_metadata,
        }
        updated = item.model_copy(update=normalized_fields)
        return updated

    def _generate_title(self, text: str) -> str:
        first_line = text.strip().splitlines()[0] if text.strip() else "Untitled"
        return first_line[:60].strip()

    def _get_default_instruction(self, template_type: str) -> str:
        return f"Generate a structured JSON output following the {template_type} workflow." \
            " Preserve the meaning of the original content."

    def _log_stage(self, message: str) -> None:
        logger.info("[IngestionEngine] %s", message)
