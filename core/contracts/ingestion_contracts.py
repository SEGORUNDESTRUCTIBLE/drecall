"""Ingestion contracts and lifecycle definitions.

Defines typed requests/results and the ingestion engine Protocol.

INPUTS:
- `IngestRequest` captures raw inputs entering the pipeline.

OUTPUTS:
- `IngestResult` carries normalized payload, validation report,
  duplicate information and persistence metadata.

FAILURES:
- `IngestionTransientError` and `IngestionPermanentError` to surface
  failure modes and boundaries.

PIPELINE GUARANTEES:
- Stage responsibilities are explicit in docstrings. The engine
  must either return an `IngestResult` or raise a documented error.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol

from .provider_contracts import ProviderResponse


@dataclass
class IngestRequest:
    text: str
    title: Optional[str] = None
    template_type: Optional[str] = None
    tags: Optional[List[str]] = field(default_factory=list)
    source: Optional[str] = None
    instruction: Optional[str] = None


@dataclass
class DuplicateInfo:
    # Light-weight placeholder; concrete implementation lives in duplicate_contracts
    matches: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class IngestResult:
    # normalized structured payload (domain-agnostic)
    payload: Dict[str, Any]
    # underlying provider response, optional
    provider_response: Optional[ProviderResponse] = None
    # validation report produced by Validator
    validation_report: Dict[str, Any] = field(default_factory=dict)
    # duplicate detection information
    duplicate_info: Optional[DuplicateInfo] = None
    # persistence metadata (id, sink-specific data)
    persistence: Dict[str, Any] = field(default_factory=dict)
    # list of error messages encountered (empty if ok)
    errors: List[str] = field(default_factory=list)


class IngestionError(Exception):
    pass


class IngestionTransientError(IngestionError):
    pass


class IngestionPermanentError(IngestionError):
    pass


class IngestionEngineContract(Protocol):
    """Protocol for the ingestion engine.

    Responsibilities (per stage):
    - Accept an `IngestRequest`.
    - Normalize inputs (text/title/tags).
    - Render prompt via a prompt builder.
    - Call provider adapter and validate provider response.
    - Build an implementation-neutral payload (dict).
    - Run domain-agnostic validation rules and return a report.
    - Optionally detect duplicates (calls duplicate detector contract).
    - Return an `IngestResult` or raise a documented error.
    """

    def ingest_text(self, request: IngestRequest) -> IngestResult:
        """Process a single text ingestion request.

        INPUTS: `IngestRequest`
        OUTPUTS: `IngestResult` or raise IngestionError
        FAILURES: raise IngestionTransientError for retryable failures;
                  IngestionPermanentError for terminal failures.
        """

        ...
