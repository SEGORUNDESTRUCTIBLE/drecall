"""Sequence matcher backend for deterministic similarity checks.

Provides exact and near-duplicate detection using difflib.SequenceMatcher.
Returns `DuplicateMatch` items defined by the duplicate contracts.
"""

from __future__ import annotations

from difflib import SequenceMatcher
from typing import Dict, Iterable, List

from core.contracts.duplicate_contracts import DuplicateMatch, DuplicateType


class SequenceMatcherBackend:
    """Calculate similarity scores between textual fields.

    Responsibilities:
    - `calculate_similarity(text1, text2)` -> float in [0.0, 1.0]
    - `find_matches(candidate, existing_iterable, fields=('title','content'), threshold=0.8)`
    """

    @staticmethod
    def _clean(text: str) -> str:
        if text is None:
            return ""
        return str(text).strip().lower()

    def calculate_similarity(self, a: str, b: str) -> float:
        a_clean = self._clean(a)
        b_clean = self._clean(b)
        if not a_clean or not b_clean:
            return 0.0
        return float(SequenceMatcher(None, a_clean, b_clean).ratio())

    def find_matches(self, candidate: Dict[str, any], existing: Iterable[Dict[str, any]], fields=('title', 'content'), threshold: float = 0.8) -> List[DuplicateMatch]:
        matches: List[DuplicateMatch] = []
        for record in existing:
            best_score = 0.0
            matched_field = None
            for field in fields:
                score = self.calculate_similarity(candidate.get(field), record.get(field))
                if score > best_score:
                    best_score = score
                    matched_field = field

            if best_score >= 1.0:
                dm = DuplicateMatch(id=record.get('id'), title=record.get('title'), similarity=1.0, type=DuplicateType.EXACT, metadata={'matched_field': matched_field})
                matches.append(dm)
                continue

            if best_score >= threshold:
                dm = DuplicateMatch(id=record.get('id'), title=record.get('title'), similarity=round(best_score, 3), type=DuplicateType.SIMILAR, metadata={'matched_field': matched_field})
                matches.append(dm)

        return matches
