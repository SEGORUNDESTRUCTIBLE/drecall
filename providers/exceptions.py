"""Provider error classes for the provider abstraction layer."""

from core.contracts.provider_contracts import ProviderError, ProviderPermanentError, ProviderTransientError


class ProviderConfigurationError(ProviderPermanentError):
    """Raised when provider configuration or initialization is invalid."""


class ProviderInitializationError(ProviderPermanentError):
    """Raised when provider initialization fails."""
