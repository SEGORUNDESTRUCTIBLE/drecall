"""Domain detection for adaptive knowledge ingestion."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Pattern, Tuple


@dataclass(frozen=True)
class DomainDetectionResult:
    domain: str
    content_type: str
    subtype: Optional[str]
    confidence: float
    rationale: Optional[str] = None


class DomainDetector:
    """Detects domain and content type from raw input."""

    _PATTERNS: List[Tuple[str, List[Pattern[str]], float]] = [
        (
            "mcq",
            [
                re.compile(r"\boption[s]?\b", re.IGNORECASE),
                re.compile(r"\bchoices?\b", re.IGNORECASE),
                re.compile(r"\bselect the best answer\b", re.IGNORECASE),
                re.compile(r"\bwhich of the following\b", re.IGNORECASE),
                re.compile(r"\bA\.[ \t]*.*B\.[ \t]*.*C\.[ \t]*.*D\.", re.IGNORECASE),
            ],
            0.94,
        ),
        (
            "mistake",
            [
                re.compile(r"\bmistake\b", re.IGNORECASE),
                re.compile(r"\berror\b", re.IGNORECASE),
                re.compile(r"\bwrong answer\b", re.IGNORECASE),
                re.compile(r"\btrap\b", re.IGNORECASE),
                re.compile(r"\bconfusion\b", re.IGNORECASE),
            ],
            0.92,
        ),
        (
            "histopathology",
            [
                re.compile(r"\bhistopathology\b", re.IGNORECASE),
                re.compile(r"\bH&E\b", re.IGNORECASE),
                re.compile(r"\bmacrophage\b", re.IGNORECASE),
                re.compile(r"\bgranuloma\b", re.IGNORECASE),
                re.compile(r"\bfoamy\b", re.IGNORECASE),
            ],
            0.93,
        ),
        (
            "radiology",
            [
                re.compile(r"\bradiolog(y|ical)?\b", re.IGNORECASE),
                re.compile(r"\bCT scan\b", re.IGNORECASE),
                re.compile(r"\bMRI\b", re.IGNORECASE),
                re.compile(r"\bx[- ]?ray\b", re.IGNORECASE),
                re.compile(r"\bimpression\b", re.IGNORECASE),
            ],
            0.93,
        ),
        (
            "ecg",
            [
                re.compile(r"\bECG\b", re.IGNORECASE),
                re.compile(r"\belectrocardiogram\b", re.IGNORECASE),
                re.compile(r"\bQRS\b", re.IGNORECASE),
                re.compile(r"\bP wave\b", re.IGNORECASE),
                re.compile(r"\bT wave\b", re.IGNORECASE),
            ],
            0.95,
        ),
        (
            "ophthalmology",
            [
                re.compile(r"\bophthalmology\b", re.IGNORECASE),
                re.compile(r"\bvisual acuity\b", re.IGNORECASE),
                re.compile(r"\bfundus\b", re.IGNORECASE),
                re.compile(r"\bretina\b", re.IGNORECASE),
                re.compile(r"\bcornea\b", re.IGNORECASE),
            ],
            0.93,
        ),
        (
            "pyq",
            [
                re.compile(r"\bPYQ\b", re.IGNORECASE),
                re.compile(r"\bprevious year\b", re.IGNORECASE),
                re.compile(r"\bpast year question\b", re.IGNORECASE),
                re.compile(r"\bentrance exam\b", re.IGNORECASE),
            ],
            0.90,
        ),
        (
            "screenshot",
            [
                re.compile(r"\bscreenshot\b", re.IGNORECASE),
                re.compile(r"\bOCR\b", re.IGNORECASE),
                re.compile(r"\bimage text\b", re.IGNORECASE),
                re.compile(r"\bphoto of\b", re.IGNORECASE),
            ],
            0.82,
        ),
        (
            "concept",
            [
                re.compile(r"\bdefine\b", re.IGNORECASE),
                re.compile(r"\bmechanism\b", re.IGNORECASE),
                re.compile(r"\bpathophysiology\b", re.IGNORECASE),
                re.compile(r"\bmanagement\b", re.IGNORECASE),
                re.compile(r"\bclassification\b", re.IGNORECASE),
                re.compile(r"\bcause\b", re.IGNORECASE),
            ],
            0.87,
        ),
    ]

    _SUBTYPE_PATTERNS: Dict[str, List[Pattern[str]]] = {
        "foamy_macrophages": [re.compile(r"foamy\s*macrophage", re.IGNORECASE)],
        "papillary_melanoma": [re.compile(r"papillary\s*melanoma", re.IGNORECASE)],
        "uvula_swelling": [re.compile(r"uvula\s*swelling", re.IGNORECASE)],
    }

    def detect(self, text: str, metadata: Optional[Dict[str, str]] = None) -> DomainDetectionResult:
        """Classify raw content into a domain and content type."""
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Text must be a non-empty string")

        cleaned = text.strip()
        normalized = cleaned.lower()
        candidates: List[DomainDetectionResult] = []

        for content_type, patterns, base_score in self._PATTERNS:
            matches = sum(1 for pattern in patterns if pattern.search(normalized))
            if matches:
                confidence = min(1.0, base_score + 0.03 * matches)
                candidates.append(
                    DomainDetectionResult(
                        domain="medical",
                        content_type=content_type,
                        subtype=self._detect_subtype(normalized),
                        confidence=confidence,
                        rationale=f"Matched {matches} pattern(s) for {content_type}",
                    )
                )

        if candidates:
            best = max(candidates, key=lambda candidate: candidate.confidence)
            return best

        fallback_type = "concept" if len(normalized.split()) > 15 else "mcq"
        return DomainDetectionResult(
            domain="medical",
            content_type=fallback_type,
            subtype=self._detect_subtype(normalized),
            confidence=0.60,
            rationale="no strong pattern matched, using lightweight fallback",
        )

    def _detect_subtype(self, normalized_text: str) -> Optional[str]:
        for subtype, patterns in self._SUBTYPE_PATTERNS.items():
            if any(pattern.search(normalized_text) for pattern in patterns):
                return subtype
        return None
