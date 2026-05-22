"""Provider contracts: typed provider response and adapter protocol.

Defines:
- `ProviderResponse` dataclass: canonical provider outputs.
- `ProviderAdapter` Protocol: minimal provider interface used by ingestion.
- Provider error classes and validation rules.

INPUTS:
- `prompt: str`, optional `system_prompt: str`, `timeout: int`.

OUTPUTS:
- `ProviderResponse` with `raw_text`, optional `parsed` JSON-like dict,
  `metadata`, boolean `ok`, and optional `error` string.

FAILURES:
- `ProviderTransientError` (retryable), `ProviderPermanentError` (non-retryable).

PIPELINE GUARANTEES:
- Implementations must not mutate inputs and must return a single
  `ProviderResponse` object. Adapter must surface transient vs permanent
  errors via exceptions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol


class ProviderError(Exception):
    """Base provider exception."""


class ProviderTransientError(ProviderError):
    """Transient error (network, rate-limit) — safe to retry."""


class ProviderPermanentError(ProviderError):
    """Permanent error (invalid credentials, unsupported request)."""


@dataclass(frozen=True)
class ProviderResponse:
    """Canonical provider response contract.

    Fields:
    - raw_text: original textual response from the provider
    - parsed: optional parsed JSON-like payload (dict/list)
    - metadata: provider-specific metadata (latency, request_id)
    - ok: whether the response passes basic sanity checks
    - error: human-friendly error message when `ok` is False
    """

    raw_text: str
    parsed: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = None
    ok: bool = True
    error: Optional[str] = None


class ProviderAdapter(Protocol):
    """Protocol that provider adapters MUST implement.

    Responsibilities (single-responsibility, side-effect free):
    - Accept a rendered prompt and optional system prompt.
    - Return a `ProviderResponse` or raise a ProviderError subclass.
    - Provide deterministic behavior for a given prompt where possible
      (for testing / dry-run adapters).
    """

    def generate(self, prompt: str, system_prompt: str = "", timeout: int = 30) -> ProviderResponse:
        """Generate provider output for a rendered prompt.

        INPUTS: prompt, system_prompt, timeout
        OUTPUTS: ProviderResponse
        FAILURES: raise ProviderTransientError or ProviderPermanentError
        """

        ...
