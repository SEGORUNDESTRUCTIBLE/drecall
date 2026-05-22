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
from .gemini_provider import GeminiProvider
from .groq_provider import GroqProvider

__all__ = [
    "BaseProvider",
    "GroqProvider",
    "GeminiProvider",
]
