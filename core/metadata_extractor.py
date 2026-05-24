"""Metadata extractor for structured revision note generation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class MetadataExtractionResult:
    canonical_payload: Dict[str, Any]
    extracted_fields: Dict[str, Any]
    inferred_tags: List[str]
    revision_metadata: Dict[str, Any]


class MetadataExtractor:
    """Extracts structured metadata and revision attributes from raw input."""

    _SUBJECT_KEYWORDS: Dict[str, List[str]] = {
        "cardiology": ["cardio", "heart", "ECG", "arrhythmia", "myocardial"],
        "neurology": ["neuro", "seizure", "stroke", "brain", "spinal"],
        "ophthalmology": ["eye", "vision", "retina", "cornea", "glaucoma"],
        "radiology": ["x-ray", "mri", "ct", "ultrasound", "radiograph"],
        "pathology": ["histopathology", "biopsy", "macrophage", "granuloma"],
        "pharmacology": ["drug", "dose", "pharmac", "therapy"],
    }

    _SCHEDULE_DEFAULTS: Dict[str, Dict[str, Any]] = {
        "mcq": {"first_review_in_days": 1, "review_interval_days": 7, "priority": "high"},
        "mistake": {"first_review_in_days": 1, "review_interval_days": 5, "priority": "high"},
        "histopathology": {"first_review_in_days": 2, "review_interval_days": 10, "priority": "medium"},
        "radiology": {"first_review_in_days": 2, "review_interval_days": 12, "priority": "medium"},
        "ecg": {"first_review_in_days": 1, "review_interval_days": 7, "priority": "high"},
        "ophthalmology": {"first_review_in_days": 3, "review_interval_days": 14, "priority": "medium"},
        "pyq": {"first_review_in_days": 1, "review_interval_days": 5, "priority": "high"},
        "screenshot": {"first_review_in_days": 2, "review_interval_days": 9, "priority": "medium"},
        "concept": {"first_review_in_days": 3, "review_interval_days": 14, "priority": "medium"},
    }

    def extract(
        self,
        canonical_payload: Dict[str, Any],
        template_name: str,
        domain: Optional[str] = None,
        subtype: Optional[str] = None,
    ) -> MetadataExtractionResult:
        """Return canonical payload enrichment and inferred metadata."""
        if not isinstance(canonical_payload, dict):
            raise ValueError("Canonical payload must be a dictionary")

        inferred_tags = set(canonical_payload.get("tags", []))
        if domain:
            inferred_tags.add(domain)
        if subtype:
            inferred_tags.add(subtype)

        subject = self._detect_subject(canonical_payload.get("content", ""))
        if subject:
            inferred_tags.add(subject)

        revision_metadata = self._build_revision_metadata(
            template_name=template_name,
            content=canonical_payload.get("content", ""),
            domain=domain,
        )

        canonical_payload.setdefault("tags", [])
        canonical_payload.setdefault("subject", subject)
        canonical_payload.setdefault("subtopic", subtype)
        canonical_payload.setdefault("template_type", template_name)
        canonical_payload.setdefault("weak_topic", canonical_payload.get("weak_topic", False))
        canonical_payload.setdefault("revision_metadata", {})
        canonical_payload["revision_metadata"].update(revision_metadata)

        extracted_fields = {
            key: canonical_payload.get(key)
            for key in [
                "title",
                "content",
                "core_concept",
                "memory_hook",
                "exam_pearl",
                "one_liner",
                "retest_question",
                "trap",
                "image_required",
                "pyq",
                "weak_topic",
            ]
            if key in canonical_payload
        }

        return MetadataExtractionResult(
            canonical_payload=canonical_payload,
            extracted_fields=extracted_fields,
            inferred_tags=sorted(inferred_tags),
            revision_metadata=revision_metadata,
        )

    def _detect_subject(self, text: str) -> Optional[str]:
        normalized = text.lower()
        for subject, tokens in self._SUBJECT_KEYWORDS.items():
            if any(token.lower() in normalized for token in tokens):
                return subject
        return None

    def _build_revision_metadata(self, template_name: str, content: str, domain: Optional[str]) -> Dict[str, Any]:
        defaults = self._SCHEDULE_DEFAULTS.get(template_name, self._SCHEDULE_DEFAULTS["concept"])
        is_long = len(str(content).split()) > 80
        metadata = {
            "source_template": template_name,
            "domain": domain or "medical",
            "scheduled_in_days": defaults["first_review_in_days"],
            "review_interval_days": defaults["review_interval_days"],
            "priority": defaults["priority"],
            "confidence_score": 0.0,
        }
        if is_long:
            metadata["scheduled_in_days"] = max(1, metadata["scheduled_in_days"] - 1)
        return metadata
