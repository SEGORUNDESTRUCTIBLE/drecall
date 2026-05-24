"""Canonical schema definitions for adaptive medical revision payloads."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ValidationError


CANONICAL_FIELD_ALIASES: Dict[str, List[str]] = {
    "title": ["title", "heading", "question", "case_title"],
    "content": ["content", "body", "text", "summary", "description", "case_summary"],
    "core_concept": ["core_concept", "core concept", "concept", "key_point", "key point"],
    "memory_hook": ["memory_hook", "memory hook", "mnemonic", "memory"],
    "trap": ["trap", "pitfall", "mistake", "error"],
    "retest_question": ["retest_question", "retest question", "practice_question", "quiz"],
    "exam_pearl": ["exam_pearl", "exam pearl", "pearl", "clinical_pearl"],
    "one_liner": ["one_liner", "one liner", "one-line", "summary_line"],
    "image_required": ["image_required", "image required", "visual_required"],
    "pyq": ["pyq", "previous_year_question", "past_year_question"],
    "weak_topic": ["weak_topic", "weak topic", "weakness"],
    "subject": ["subject", "discipline", "specialty"],
    "subtopic": ["subtopic", "chapter", "section"],
    "revision_metadata": ["revision_metadata", "revision metadata", "schedule", "revision"],
    "tags": ["tags", "labels", "categories"],
    "image_references": ["image_references", "images", "screenshots", "figures"],
    "options": ["options", "answers", "choices"],
    "answer": ["answer", "correct_answer"],
    "explanation": ["explanation", "rationale", "reasoning"],
}


class CanonicalRevisionPayload(BaseModel):
    title: str = Field(..., description="Title of the revision item")
    content: str = Field(..., description="Primary content or case text")
    memory_hook: Optional[str] = Field(None, description="Memory hook or mnemonic")
    trap: Optional[str] = Field(None, description="Common trap or confusion")
    retest_question: Optional[str] = Field(None, description="Retest or practice question")
    core_concept: Optional[str] = Field(None, description="Core concept distilled from the content")
    exam_pearl: Optional[str] = Field(None, description="High-yield exam pearl")
    one_liner: Optional[str] = Field(None, description="One-liner revision summary")
    image_required: bool = Field(False, description="Indicates if an image is required for the item")
    pyq: bool = Field(False, description="Marks if this is a previous year question")
    weak_topic: bool = Field(False, description="Marks if this item identifies a weak topic")
    revision_metadata: Dict[str, Any] = Field(default_factory=dict, description="Revision scheduling and metadata")
    tags: List[str] = Field(default_factory=list, description="Associated tags for retrieval")
    subject: Optional[str] = Field(None, description="Primary medical subject")
    subtopic: Optional[str] = Field(None, description="Secondary subtopic or chapter")
    source: Optional[str] = Field(None, description="Source of the raw content")
    template_type: str = Field("medical", description="Template type used for generation")
    image_references: List[str] = Field(default_factory=list, description="Image or screenshot references")
    options: List[str] = Field(default_factory=list, description="MCQ options if applicable")
    answer: Optional[str] = Field(None, description="MCQ answer or diagnosis outcome")
    explanation: Optional[str] = Field(None, description="Detailed explanation or rationale")

    @classmethod
    def from_provider_output(cls, provider_output: Any, template_name: str, title: Optional[str] = None) -> "CanonicalRevisionPayload":
        if provider_output is None:
            raise ValueError("Provider output cannot be None")
        if isinstance(provider_output, str):
            try:
                provider_output = json.loads(provider_output)
            except json.JSONDecodeError as exc:
                raise ValueError("Provider output must be valid JSON") from exc

        if isinstance(provider_output, list) and provider_output:
            provider_output = provider_output[0]

        if not isinstance(provider_output, dict):
            raise ValueError("Provider output must be a JSON object")

        canonical_data: Dict[str, Any] = {}
        for field, aliases in CANONICAL_FIELD_ALIASES.items():
            for alias in aliases:
                if alias in provider_output and provider_output[alias] not in (None, ""):
                    canonical_data[field] = provider_output[alias]
                    break

        canonical_data["template_type"] = template_name
        if title:
            canonical_data["title"] = title
        canonical_data.setdefault("title", provider_output.get("title", ""))
        canonical_data.setdefault("content", provider_output.get("content", ""))

        if not canonical_data.get("title"):
            fallback_title = str(canonical_data.get("content", "")).strip().splitlines()[0][:120]
            canonical_data["title"] = fallback_title

        if not canonical_data.get("content"):
            fallback_content = str(provider_output.get("summary", "")) or str(provider_output.get("notes", ""))
            canonical_data["content"] = fallback_content

        canonical_data.setdefault("tags", [])
        canonical_data.setdefault("revision_metadata", {})
        canonical_data.setdefault("image_references", [])
        canonical_data.setdefault("options", [])

        try:
            return cls(**canonical_data)
        except ValidationError as exc:
            raise ValueError(f"Failed to validate canonical payload: {exc}") from exc

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(mode="json")
