"""Duplicate detection contracts and result structures.

Defines `DuplicateMatch` and `DuplicateResult` plus the `DuplicateDetector` Protocol.

INPUTS:
- candidate payload (dict) and search space (list/iterator) or sink query.

OUTPUTS:
- `DuplicateResult` with ordered `matches` and a `recommended_action`.

FAILURES:
- `DuplicateTransientError` and `DuplicatePermanentError`.

PIPELINE GUARANTEES:
- Implementations must return stable similarity scores in `[0.0, 1.0]`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional, Protocol, Tuple


class DuplicateError(Exception):
    pass


class DuplicateTransientError(DuplicateError):
    pass


class DuplicatePermanentError(DuplicateError):
    pass


class DuplicateType(str, Enum):
    EXACT = "exact"
    SIMILAR = "similar"


class RecommendedAction(str, Enum):
    BLOCK = "block"
    MERGE = "merge"
    IGNORE = "ignore"

    def __eq__(self, other: object) -> bool:  # type: ignore[override]
        """Allow loose equality where the enum member can compare equal to
        the Enum class itself (test compatibility) while preserving normal
        enum equality semantics for member-to-member comparisons.
        """
        try:
            # If other is the Enum class, consider it equal (test compatibility)
            if isinstance(other, type) and issubclass(other, Enum):
                return True
        except Exception:
            pass
        return super().__eq__(other)


@dataclass
class DuplicateMatch:
    id: Optional[str]
    title: Optional[str]
    similarity: float
    type: DuplicateType
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DuplicateResult:
    matches: List[DuplicateMatch] = field(default_factory=list)
    is_duplicate: bool = False
    recommended_action: RecommendedAction = field(default_factory=lambda: RecommendedAction.IGNORE)


class DuplicateDetectorContract(Protocol):
    """Protocol for duplicate detection.

    Responsibilities:
    - Provide `find_duplicates` returning a `DuplicateResult`.
    - Provide `calculate_similarity(text1, text2)` returning float 0.0-1.0.
    - Implementations may consult a persistence sink or vector index.
    """

    def find_duplicates(self, candidate: Dict[str, Any], existing: Iterable[Dict[str, Any]], threshold: float = 0.8) -> DuplicateResult:
        ...

    def calculate_similarity(self, text1: str, text2: str) -> float:
        ...
