"""Provider registry and factory.

Centralizes provider selection, configuration, and metadata for the
provider abstraction architecture.

This registry makes it easy to add new providers without scattering
provider-specific logic through application startup or ingestion pipelines.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Type

from config import get_settings
from .base_provider import BaseProvider
from .exceptions import ProviderConfigurationError
from .gemini_provider import GeminiProvider
from .groq_provider import GroqProvider


@dataclass(frozen=True)
class ProviderMetadata:
    name: str
    display_name: str
    description: str
    supported_models: List[str]
    default_model: Optional[str] = None


_PROVIDER_REGISTRY: Dict[str, Type[BaseProvider]] = {
    "groq": GroqProvider,
    "gemini": GeminiProvider,
}

_PROVIDER_METADATA: Dict[str, ProviderMetadata] = {
    "groq": ProviderMetadata(
        name="groq",
        display_name="Groq AI",
        description="High-speed Groq LLM inference provider.",
        supported_models=["mixtral-8x7b-32768", "llama2-70b-4096"],
        default_model="mixtral-8x7b-32768",
    ),
    "gemini": ProviderMetadata(
        name="gemini",
        display_name="Google Gemini",
        description="Google Gemini model provider.",
        supported_models=["gemini-pro", "gemini-pro-vision"],
        default_model="gemini-pro",
    ),
}


def register_provider(name: str, provider_cls: Type[BaseProvider], metadata: Optional[ProviderMetadata] = None) -> None:
    name = name.lower()
    if name in _PROVIDER_REGISTRY:
        raise ProviderConfigurationError(f"Provider '{name}' is already registered")
    _PROVIDER_REGISTRY[name] = provider_cls
    if metadata is not None:
        _PROVIDER_METADATA[name] = metadata


def get_provider_class(name: str) -> Type[BaseProvider]:
    provider_cls = _PROVIDER_REGISTRY.get(name.lower())
    if provider_cls is None:
        raise ProviderConfigurationError(f"Unknown provider '{name}'")
    return provider_cls


def available_providers() -> List[str]:
    return sorted(_PROVIDER_REGISTRY.keys())


def get_provider_metadata(name: str) -> ProviderMetadata:
    metadata = _PROVIDER_METADATA.get(name.lower())
    if metadata is None:
        raise ProviderConfigurationError(f"No metadata registered for provider '{name}'")
    return metadata


def create_provider(name: str, settings: Optional[Any] = None, **kwargs: Any) -> BaseProvider:
    settings = settings or get_settings()
    provider_cls = get_provider_class(name)

    normalized_name = name.lower()
    config: Dict[str, Any] = {}
    if normalized_name == "groq":
        config["api_key"] = kwargs.get("api_key", settings.groq_api_key)
        config["model"] = kwargs.get("model", settings.get_provider("groq"))
    elif normalized_name == "gemini":
        config["api_key"] = kwargs.get("api_key", settings.gemini_api_key)
        config["model"] = kwargs.get("model", settings.get_provider("gemini"))
    else:
        config["api_key"] = kwargs.get("api_key")
        config["model"] = kwargs.get("model")

    config["timeout"] = kwargs.get("timeout", getattr(settings, "request_timeout", 30))
    config["retries"] = kwargs.get("retries", getattr(settings, "max_retries", 3))
    config["retry_backoff"] = kwargs.get("retry_backoff", kwargs.get("retry_backoff", 1.0))

    config.update({k: v for k, v in kwargs.items() if k not in config})

    try:
        return provider_cls(**config)
    except Exception as exc:
        raise ProviderConfigurationError(f"Failed to initialize provider '{name}': {exc}") from exc


def create_provider_from_settings(name: str, settings: Optional[Any] = None) -> BaseProvider:
    settings = settings or get_settings()
    return create_provider(name, settings=settings)
