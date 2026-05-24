"""AI Provider integrations.

Provides abstract base class and implementations for different AI providers
(Groq, Gemini, etc.) with unified interface. Maintains provider-agnostic
architecture to enable easy switching and composition.

Key design principles:
- All providers implement the same interface (BaseProvider)
- No business logic in provider code
- All outputs standardized to ProviderResponse
- Easy to add new providers without affecting core code
"""

from .base_provider import BaseProvider
from .exceptions import ProviderConfigurationError, ProviderError, ProviderPermanentError, ProviderTransientError
from .gemini_provider import GeminiProvider
from .groq_provider import GroqProvider
from .provider_registry import (
    ProviderMetadata,
    available_providers,
    create_provider,
    create_provider_from_settings,
    get_provider_class,
    get_provider_metadata,
    register_provider,
)

__all__ = [
    "BaseProvider",
    "GroqProvider",
    "GeminiProvider",
    "ProviderConfigurationError",
    "ProviderError",
    "ProviderPermanentError",
    "ProviderTransientError",
    "ProviderMetadata",
    "available_providers",
    "create_provider",
    "create_provider_from_settings",
    "get_provider_class",
    "get_provider_metadata",
    "register_provider",
]
