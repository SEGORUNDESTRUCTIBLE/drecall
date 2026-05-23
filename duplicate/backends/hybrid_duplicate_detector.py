"""Hybrid duplicate detector combining deterministic backends.

Aggregates HashBackend, MetadataBackend, and SequenceMatcherBackend to
produce an explainable `DuplicateResult` without embeddings.
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional

from core.contracts.duplicate_contracts import (
    DuplicateResult,
    DuplicateMatch,
    DuplicateType,
    RecommendedAction,
    DuplicateDetectorContract,
)

from .hash_backend import HashBackend
from .metadata_backend import MetadataBackend
from .sequence_matcher_backend import SequenceMatcherBackend


class HybridDuplicateDetector(DuplicateDetectorContract):
    """Combine multiple symbolic backends to form a deterministic detector.

    Strategy:
    1. Check metadata backend for exact metadata matches -> recommended BLOCK
    2. Check hash backend for exact content matches -> recommended BLOCK
    3. Run sequence matcher for near-duplicates -> recommended MERGE if above threshold
    4. Aggregate matches and return a DuplicateResult with explanation
    """

    def __init__(
        self,
        hash_fields: Optional[List[str]] = None,
        seq_fields: Optional[List[str]] = None,
        metadata_keys: Optional[List[str]] = None,
        similarity_threshold: float = 0.8,
    ) -> None:
        self.hash_backend = HashBackend(fields=tuple(hash_fields) if hash_fields else ('title', 'content'))
        self.meta_backend = MetadataBackend(keys=tuple(metadata_keys) if metadata_keys else ('duplicate_fingerprint',))
        self.seq_backend = SequenceMatcherBackend()
        # Compare both title and content for more semantically meaningful scoring
        self.seq_fields = tuple(seq_fields) if seq_fields else ('title', 'content')
        self.similarity_threshold = similarity_threshold
        # small hysteresis margin to avoid borderline false-positives
        self.hysteresis_margin = 0.05

    def find_duplicates(self, candidate: Dict[str, any], existing: Iterable[Dict[str, any]], threshold: Optional[float] = None) -> DuplicateResult:
        th = threshold or self.similarity_threshold
        matches: List[DuplicateMatch] = []

        # metadata exact matches
        meta_matches = self.meta_backend.find_matches(candidate, existing)
        if meta_matches:
            matches.extend(meta_matches)
            # metadata exact match is high confidence
            return DuplicateResult(matches=matches, is_duplicate=True, recommended_action=RecommendedAction.BLOCK)

        # hash exact matches
        hash_matches = self.hash_backend.find_matches(candidate, existing)
        if hash_matches:
            matches.extend(hash_matches)
            return DuplicateResult(matches=matches, is_duplicate=True, recommended_action=RecommendedAction.BLOCK)

        # sequence matcher near matches
        seq_matches = self.seq_backend.find_matches(candidate, existing, fields=self.seq_fields, threshold=th)
        if seq_matches:
            matches.extend(seq_matches)
            # if best match very high, recommend merge else ignore
            best = max(matches, key=lambda m: m.similarity)
            # apply hysteresis: require threshold + margin to declare a definitive duplicate
            effective_threshold = th + self.hysteresis_margin
            is_dup = best.similarity >= effective_threshold
            action = RecommendedAction.MERGE if best.similarity >= th else RecommendedAction.IGNORE
            return DuplicateResult(matches=matches, is_duplicate=is_dup, recommended_action=action)

        return DuplicateResult(matches=[], is_duplicate=False, recommended_action=RecommendedAction.IGNORE)

    def calculate_similarity(self, text1: str, text2: str) -> float:
        return self.seq_backend.calculate_similarity(text1, text2)
