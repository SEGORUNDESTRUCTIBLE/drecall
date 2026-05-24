"""Base abstract provider for AI model interactions.

Defines the unified interface that all AI providers must implement.
This ensures provider-agnostic architecture and easy extensibility.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from core.contracts.provider_contracts import (
    ProviderError,
    ProviderResponse,
    ProviderPermanentError,
    ProviderTransientError,
)

logger = logging.getLogger(__name__)


class BaseProvider(ABC):
    """Abstract base class for AI providers.

    Establishes a unified interface for interacting with different AI services
    (Groq, Gemini, OpenRouter, etc.). Ensures all providers implement consistent
    methods for seamless swapping and composition.

    This design prevents provider-specific logic from leaking into core code.
    All business logic should remain independent of which provider is used.
    """

    def __init__(self, api_key: str, model: str, timeout: int = 30, retries: int = 3, retry_backoff: float = 1.0, **kwargs: Any) -> None:
        """Initialize the provider.

        Args:
            api_key: API key or authentication token for the service.
            model: Model name/ID to use for completions.
            timeout: Request timeout in seconds (default: 30).
            retries: Number of retry attempts for transient errors.
            retry_backoff: Initial backoff delay in seconds.
            **kwargs: Additional provider-specific configuration parameters.
        """
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.retries = retries
        self.retry_backoff = retry_backoff
        self.config = kwargs

    def provider_name(self) -> str:
        """Get a normalized provider name for this provider.
        
        Returns:
            Provider name as a lowercase string (e.g., 'groq', 'gemini').
        """
        class_name = self.__class__.__name__
        # Remove 'Provider' suffix if present and lowercase
        if class_name.endswith("Provider"):
            return class_name[:-8].lower()
        return class_name.lower()

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> ProviderResponse:
        """Generate a standardized provider response.

        Core method for all providers. Implementations should handle:
        - Message construction (system + user prompts)
        - API calls with proper error handling
        - Response extraction and parsing
        - Timeout and retry logic

        Args:
            prompt: The user-facing prompt/input.
            system_prompt: Optional system-level instructions that shape behavior.
            temperature: Sampling temperature (0.0-1.0+). Higher = more creative.
            max_tokens: Maximum tokens in response (provider-dependent).
            **kwargs: Additional provider-specific parameters.

        Returns:
            ProviderResponse object representing the completion.

        Raises:
            ProviderTransientError: Retryable provider failures.
            ProviderPermanentError: Terminal provider failures.
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement generate()")

    @abstractmethod
    def validate_credentials(self) -> bool:
        """Validate that the provider credentials are valid and working.

        Should perform a lightweight test (e.g., a small API call) to verify
        the API key is valid without consuming significant quota.

        Returns:
            True if credentials are valid and provider is reachable, False otherwise.
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement validate_credentials()")

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get information and capabilities of the current model.

        Returns metadata about the model being used, such as:
        - Maximum context length
        - Supported features
        - Model version/release date
        - Rate limits

        Returns:
            Dictionary containing model metadata and capabilities.
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement get_model_info()")

    @abstractmethod
    def health_check(self) -> bool:
        """Run a lightweight health check for the provider.

        Returns:
            True if the provider is reachable and configured correctly.
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement health_check()")

    @abstractmethod
    def available_models(self) -> List[str]:
        """Return a list of supported model names or aliases."""
        raise NotImplementedError(f"{self.__class__.__name__} must implement available_models()")

    @abstractmethod
    def token_usage(self) -> Dict[str, Any]:
        """Return provider-specific token usage metadata."""
        raise NotImplementedError(f"{self.__class__.__name__} must implement token_usage()")

    def _retryable_call(self, fn):
        """Execute a provider call with retry/backoff for transient failures."""
        last_error: Optional[Exception] = None
        for attempt in range(1, max(1, self.retries) + 1):
            try:
                return fn()
            except ProviderPermanentError:
                raise
            except Exception as exc:
                last_error = exc
                backoff = self.retry_backoff * (2 ** (attempt - 1))
                logger.warning(
                    "%s call failed (attempt %d/%d): %s; retrying in %.1fs",
                    self.__class__.__name__,
                    attempt,
                    self.retries,
                    exc,
                    backoff,
                )
                time.sleep(backoff)
        logger.error("All retries failed for %s", self.__class__.__name__)
        if isinstance(last_error, ProviderError):
            raise last_error
        raise ProviderTransientError(str(last_error) if last_error else "Unknown provider error")

    def __repr__(self) -> str:
        """Return string representation."""
        return f"{self.__class__.__name__}(model={self.model})"
