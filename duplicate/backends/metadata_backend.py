"""Metadata-aware duplicate backend.

Matches on metadata fields such as `duplicate_fingerprint` or explicit
user-provided duplicate keys. It does not treat broad fields like `source`
or `datasource_id` as exact duplicates by default.
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Sequence

from core.contracts.duplicate_contracts import DuplicateMatch, DuplicateType


class MetadataBackend:
    """Match records based on metadata keys.

    Args:
        keys: sequence of metadata keys to consider, ordered by priority.
    """

    def __init__(self, keys: Sequence[str] = ('duplicate_fingerprint',)) -> None:
        self.keys = keys

    def find_matches(self, candidate: Dict[str, any], existing: Iterable[Dict[str, any]]) -> List[DuplicateMatch]:
        matches: List[DuplicateMatch] = []

        for record in existing:
            for key in self.keys:
                cand_val = candidate.get(key)
                rec_val = record.get(key)
                if cand_val is not None and rec_val is not None and str(cand_val) == str(rec_val):
                    matches.append(
                        DuplicateMatch(
                            id=record.get('id'),
                            title=record.get('title'),
                            similarity=1.0,
                            type=DuplicateType.EXACT,
                            metadata={'matched_key': key, 'value': cand_val},
                        )
                    )
                    break

        return matches
