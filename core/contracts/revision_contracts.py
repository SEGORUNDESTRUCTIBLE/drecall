"""Revision engine contracts.

Defines the contract for the `RevisionEngine` used to enhance/expand
recall items. Revisions are versioned and stored immutably by the
persistence layer; the engine returns a new payload and metadata.

INPUTS:
- `RevisionRequest` includes the canonical item payload and high-level reason.

OUTPUTS:
- `RevisionResult` with `new_payload`, `version`, `provider_meta`, and `errors`.

FAILURES:
- `RevisionTransientError` vs `RevisionPermanentError` for orchestration.

PIPELINE GUARANTEES:
- Implementations must not mutate the original payload in-place. They
  must return a new payload and a deterministic `version` string.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol


class RevisionError(Exception):
    pass


class RevisionTransientError(RevisionError):
    pass


class RevisionPermanentError(RevisionError):
    pass


@dataclass
class RevisionRequest:
    payload: Dict[str, Any]
    reason: Optional[str] = None
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RevisionResult:
    new_payload: Dict[str, Any]
    version: str
    provider_meta: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


class RevisionEngineContract(Protocol):
    """Protocol for revision/enhancement engines.

    Responsibilities:
    - `enhance_content` should return a string or updated payload fragment.
    - `expand_item` returns a complete `RevisionResult` with a new version.
    - `generate_summary` returns a textual summary.
    - All methods must be idempotent where possible and surface errors
      via appropriate exceptions.
    """

    def enhance_content(self, payload: Dict[str, Any], options: Dict[str, Any] = None) -> str:
        ...

    def expand_item(self, request: RevisionRequest) -> RevisionResult:
        ...

    def generate_summary(self, payload: Dict[str, Any]) -> str:
        ...

    def revise_batch(self, requests: List[RevisionRequest]) -> List[RevisionResult]:
        ...
