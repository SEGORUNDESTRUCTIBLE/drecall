"""Hash-based exact duplicate backend.

Provides deterministic exact-match detection via content hashing.
Useful for idempotency and fast exact duplicate checks.
"""

from __future__ import annotations

import hashlib
from typing import Dict, Iterable, List

from core.contracts.duplicate_contracts import DuplicateMatch, DuplicateType


class HashBackend:
    """Compute stable hashes for title/content and compare equality.

    Responsibilities:
    - `hash_item(item, fields=('title','content'))` -> hex digest
    - `find_matches(candidate, existing_iterable, fields=('title','content'))` -> list of exact matches
    """

    def __init__(self, fields=('title', 'content')) -> None:
        self.fields = fields

    def _normalize(self, value: str) -> str:
        if value is None:
            return ""

        normalized = str(value).strip().lower()
        return " ".join(normalized.split())

    def hash_item(self, item: Dict[str, any]) -> str:
        pieces = [self._normalize(item.get(f)) for f in self.fields]
        joined = "||".join(pieces)
        return hashlib.sha256(joined.encode("utf-8")).hexdigest()

    def find_matches(self, candidate: Dict[str, any], existing: Iterable[Dict[str, any]]) -> List[DuplicateMatch]:
        matches: List[DuplicateMatch] = []
        cand_hash = self.hash_item(candidate)
        for record in existing:
            rec_hash = self.hash_item(record)
            if cand_hash == rec_hash:
                matches.append(DuplicateMatch(id=record.get('id'), title=record.get('title'), similarity=1.0, type=DuplicateType.EXACT, metadata={'hash': cand_hash}))

        return matches
