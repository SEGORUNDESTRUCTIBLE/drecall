"""Generic mapping logic for turning provider responses into canonical RecallItems."""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional

from core.normalizers import Normalizer
from core.schemas import RecallItem
from core.validators import Validator
from .schema_registry import TemplateSchema


class RecallMapper:
    def __init__(self, schema: Optional[TemplateSchema] = None) -> None:
        self.schema = schema
        self.normalizer = Normalizer()
        self.validator = Validator()

    def map(self, provider_data: Dict[str, Any], source: Optional[str] = None, template_type: str = "custom") -> RecallItem:
        if not isinstance(provider_data, dict):
            raise ValueError("Provider output must be a JSON object for mapping.")

        schema = self.schema
        if schema is None:
            raise ValueError("Mapping schema is required for RecallMapper.")

        self._validate_provider_data(provider_data, schema)

        title = self._extract_text(provider_data, ["title", "name", "headline", "question"], fallback="Untitled")
        content = self._extract_text(provider_data, ["content", "summary", "notes", "explanation"], fallback="")
        if not content or len(content) < 10:
            content = self._build_content_from_fields(provider_data, schema.content_fallback_fields)

        if not content or len(content) < 10:
            content = self._extract_text(provider_data, ["_fallback_content"], fallback=content)

        tags = self._extract_tags(provider_data)
        subject = self.normalizer.normalize_subject(provider_data.get("subject"))
        system = self.normalizer.normalize_system(provider_data.get("system"))
        error_type = self.normalizer.normalize_error_type(provider_data.get("error_type"))
        pattern_type = self.normalizer.normalize_pattern_type(provider_data.get("pattern_type"))
        difficulty = self.normalizer.normalize_difficulty(provider_data.get("difficulty") or provider_data.get("complexity"))
        recall_priority = self.normalizer.normalize_priority(provider_data.get("recall_priority") or provider_data.get("priority"))
        revision_metadata = self._extract_revision_metadata(provider_data)
        duplicate_fingerprint = self._compute_fingerprint(title, content)
        embedding_metadata = self._extract_embedding_metadata(provider_data)
        normalized_source = self.normalizer.normalize_text(source or provider_data.get("source") or "provider")

        metadata = {
            "provider_output": provider_data,
            "template_type": template_type,
        }
        metadata.update(provider_data.get("metadata") or {})

        recall_item = RecallItem(
            title=title,
            content=content,
            tags=tags,
            source=normalized_source,
            subject=subject,
            system=system,
            error_type=error_type,
            pattern_type=pattern_type,
            difficulty=difficulty,
            recall_priority=recall_priority,
            revision_metadata=revision_metadata,
            duplicate_fingerprint=duplicate_fingerprint,
            embedding_metadata=embedding_metadata,
            metadata=metadata,
        )

        is_valid, errors = self.validator.validate_recall_item(recall_item)
        if not is_valid:
            raise ValueError(f"Mapped RecallItem validation failed: {errors}")

        return recall_item

    def _validate_provider_data(self, provider_data: Dict[str, Any], schema: TemplateSchema) -> None:
        missing_fields = []
        for field_name in schema.required_fields:
            field_value = self._extract_text(provider_data, [field_name], fallback=None)
            if field_value not in (None, ""):
                continue

            if field_name == "content" and any(
                self._extract_text(provider_data, [fallback_field], fallback=None) not in (None, "")
                for fallback_field in schema.content_fallback_fields + ["_fallback_content"]
            ):
                continue

            missing_fields.append(field_name)

        if missing_fields:
            raise ValueError(f"Provider output missing required fields: {missing_fields}")

        for key, allowed_values in schema.enum_fields.items():
            if provider_data.get(key) is None:
                continue
            value = str(provider_data.get(key)).strip()
            if value and allowed_values and value not in allowed_values:
                raise ValueError(f"Provider output field '{key}' has invalid value '{value}'. Allowed values: {allowed_values}")

    def _extract_text(self, data: Dict[str, Any], keys: List[str], fallback: Optional[str] = None) -> Optional[str]:
        for key in keys:
            value = data.get(key)
            if value is None:
                continue

            if isinstance(value, str) and value.strip():
                return self.normalizer.normalize_text(value)

            if isinstance(value, (int, float)):
                return str(value)

            if isinstance(value, list):
                list_items = [self.normalizer.normalize_text(str(item)) for item in value if item is not None]
                if list_items:
                    return "\n".join(list_items)

            if isinstance(value, dict):
                nested_items = [self.normalizer.normalize_text(str(v)) for v in value.values() if v is not None]
                if nested_items:
                    return "\n".join(nested_items)

        return fallback

    def _extract_tags(self, data: Dict[str, Any]) -> List[str]:
        tags = data.get("tags") or data.get("labels") or []
        if isinstance(tags, str):
            return self.normalizer.normalize_tags(tags.split(","))
        if isinstance(tags, list):
            return self.normalizer.normalize_tags(tags)
        return []

    def _extract_revision_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        revision = data.get("revision")
        if isinstance(revision, dict):
            return revision
        return {"source": "provider", "raw": revision} if revision is not None else {}

    def _extract_embedding_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        embedding = data.get("embedding") or data.get("embedding_metadata")
        if isinstance(embedding, dict):
            return embedding
        return {"raw": embedding} if embedding is not None else {}

    def _build_content_from_fields(self, data: Dict[str, Any], fallback_fields: List[str]) -> str:
        content_pieces: List[str] = []
        for field in fallback_fields:
            value = data.get(field)
            if isinstance(value, str) and value.strip():
                content_pieces.append(self.normalizer.normalize_text(value))
            elif isinstance(value, list):
                list_items = [self.normalizer.normalize_text(str(item)) for item in value if item is not None]
                if list_items:
                    content_pieces.append("\n".join(list_items))
            elif isinstance(value, dict):
                nested_items = [self.normalizer.normalize_text(str(v)) for v in value.values() if v is not None]
                if nested_items:
                    content_pieces.append("\n".join(nested_items))
        if content_pieces:
            return "\n\n".join(content_pieces)
        return ""

    def _compute_fingerprint(self, title: str, content: str) -> str:
        digest = hashlib.sha256(f"{title.strip()}|{content.strip()}".encode("utf-8")).hexdigest()
        return digest
