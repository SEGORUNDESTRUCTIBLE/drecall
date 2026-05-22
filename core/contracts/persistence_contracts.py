"""Persistence contracts: sink/adapter abstraction and results.

Defines a minimal PersistenceSink Protocol used by the pipeline to
store and query items. Persistence implementations are datasource
independent and must implement the methods below.

INPUTS:
- item: Dict[str, Any] representing the canonical payload to persist.

OUTPUTS:
- `PersistenceResult` with `id` and optional metadata.

FAILURES:
- `PersistenceTransientError` (retryable) and `PersistencePermanentError`.

PIPELINE GUARANTEES:
- The sink must provide idempotent `create` behavior where possible
  (dedup-key enforcement or transaction support is recommended).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol


class PersistenceError(Exception):
    pass


class PersistenceTransientError(PersistenceError):
    pass


class PersistencePermanentError(PersistenceError):
    pass


@dataclass(frozen=True)
class PersistenceResult:
    id: str
    metadata: Dict[str, Any] = None


class PersistenceSink(Protocol):
    """Abstraction over persistence backends.

    Responsibilities:
    - `create` must persist a canonical item and return a `PersistenceResult`.
    - `update` should update fields of an existing record.
    - `exists` should check for an existing record (by dedup key or id).
    - `query_similar` is optional but recommended for duplicate search
      fallbacks for systems without vector indexes.
    """

    def create(self, item: Dict[str, Any]) -> PersistenceResult:
        """Persist `item` and return a PersistenceResult with stable id.

        INPUTS: canonical item dict
        OUTPUTS: PersistenceResult
        FAILURES: raise PersistenceTransientError or PersistencePermanentError
        """

        ...

    def update(self, item_id: str, patch: Dict[str, Any]) -> PersistenceResult:
        ...

    def exists(self, dedup_key: str) -> bool:
        ...

    def query_similar(self, text: str, limit: int = 10):
        """Optional: return similar records for duplicate detection.

        Not all sinks will provide this efficiently; return an empty list
        when unsupported.
        """

        ...
