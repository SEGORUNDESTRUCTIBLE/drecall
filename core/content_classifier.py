"""Content classifier for adaptive revision workflows."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class ContentClassificationResult:
    intent: str
    template_hint: str
    tags: Dict[str, str]
    confidence: float
    rationale: Optional[str] = None


class ContentClassifier:
    """Classifies content shape and revision intent."""

    def classify(self, text: str, domain: Optional[str] = None, content_type: Optional[str] = None) -> ContentClassificationResult:
        """Return intent, template hint, and metadata tags for raw input."""
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Text must be a non-empty string")

        normalized = text.strip().lower()
        content_type = content_type or "concept"
        intent = "revision_note"
        confidence = 0.65

        if content_type == "mcq":
            intent = "question_review"
            confidence = 0.92
        elif content_type == "mistake":
            intent = "error_analysis"
            confidence = 0.90
        elif content_type == "histopathology":
            intent = "pathology_case"
            confidence = 0.90
        elif content_type == "radiology":
            intent = "radiology_case"
            confidence = 0.90
        elif content_type == "ecg":
            intent = "ecg_interpretation"
            confidence = 0.92
        elif content_type == "ophthalmology":
            intent = "ophthalmology_case"
            confidence = 0.88
        elif content_type == "pyq":
            intent = "exam_revision"
            confidence = 0.88
        elif content_type == "screenshot":
            intent = "ocr_revision"
            confidence = 0.78
        elif "explain" in normalized or "describe" in normalized or "mechanism" in normalized:
            intent = "concept_explanation"
            confidence = 0.80
        elif "why" in normalized and "because" not in normalized:
            intent = "cause_analysis"
            confidence = 0.78

        if "one-liner" in normalized or "one liner" in normalized:
            confidence = min(1.0, confidence + 0.05)

        template_hint = content_type if content_type in {
            "mcq",
            "concept",
            "mistake",
            "histopathology",
            "radiology",
            "ecg",
            "ophthalmology",
            "pyq",
            "screenshot",
        } else "concept"

        tags = {
            "domain": domain or "medical",
            "content_type": content_type,
            "intent": intent,
        }

        return ContentClassificationResult(
            intent=intent,
            template_hint=template_hint,
            tags=tags,
            confidence=confidence,
            rationale="lightweight heuristic classification",
        )
