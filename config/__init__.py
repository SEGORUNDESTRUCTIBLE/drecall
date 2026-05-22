"""Configuration module for drecall.

Provides centralized settings management with environment variable support,
JSON config file parsing, and Pydantic validation.

Usage:
    from config import get_settings
    settings = get_settings()
"""

from .settings import Settings, get_settings, reset_settings

__all__ = ["Settings", "get_settings", "reset_settings"]
