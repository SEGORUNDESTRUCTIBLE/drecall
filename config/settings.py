"""Application settings and configuration management.

Centralized configuration system that merges settings from multiple sources:
1. Default values (hardcoded in Settings class)
2. settings.json file (project configuration)
3. Environment variables (via .env)
4. Runtime overrides (for tests/special cases)

All settings are validated through Pydantic for type safety.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application configuration settings.
    
    Loads configuration from multiple sources with proper precedence:
    Environment variables > settings.json > defaults
    
    All settings are validated using Pydantic to catch configuration errors early.
    """
    
    # Application info
    app_name: str = "drecall"
    version: str = "0.1.0"
    environment: str = "development"
    debug: bool = True
    
    # Paths (always resolved relative to project root)
    project_root: Path = Path(__file__).parent.parent.parent
    logs_dir: Path = Path()
    templates_dir: Path = Path()
    assets_dir: Path = Path()
    config_dir: Path = Path()
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"  # json or standard
    
    # API Configuration
    request_timeout: int = 30
    max_retries: int = 3
    batch_size: int = 10
    
    # AI Providers - API Keys (sensitive, from environment only)
    groq_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    groq_model: str = "mixtral-8x7b-32768"
    gemini_model: str = "gemini-pro"
    enable_groq: bool = True
    enable_gemini: bool = True
    default_provider: str = "groq"
    
    # Notion Integration
    notion_api_key: Optional[str] = None
    notion_database_id: Optional[str] = None
    enable_notion: bool = True
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def model_post_init(self, __context) -> None:
        """Post-initialization configuration setup.
        
        - Resolves relative paths
        - Loads settings.json if it exists
        - Creates required directories
        """
        # Set up directory paths relative to project root
        self.logs_dir = self.project_root / "logs"
        self.templates_dir = self.project_root / "templates"
        self.assets_dir = self.project_root / "assets"
        self.config_dir = self.project_root / "config"
        
        # Create required directories
        for directory in [self.logs_dir, self.templates_dir, self.assets_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {directory}")
        
        # Load additional settings from settings.json if it exists
        self._load_json_config()
        
        logger.debug(f"Settings initialized: environment={self.environment}, debug={self.debug}")
    
    def _load_json_config(self) -> None:
        """Load and merge settings from settings.json.
        
        JSON settings are lower precedence than environment variables.
        Useful for storing non-sensitive configuration in version control.
        """
        config_file = self.config_dir / "settings.json"
        
        if not config_file.exists():
            logger.debug(f"No settings.json found at {config_file}")
            return
        
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                json_config = json.load(f)
            logger.debug(f"Loaded settings.json: {config_file}")
            
            # Merge JSON settings (don't override env vars)
            self._merge_json_settings(json_config)
            
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in settings.json: {e}")
        except Exception as e:
            logger.warning(f"Failed to load settings.json: {e}")
    
    def _merge_json_settings(self, json_config: Dict[str, Any]) -> None:
        """Merge settings from JSON config.
        
        Intelligently merges JSON settings without overriding
        environment-sourced values.
        
        Args:
            json_config: Dictionary of settings from JSON file.
        """
        if "processing" in json_config:
            proc = json_config["processing"]
            # Only set if not already set by env
            if self.request_timeout == 30:  # default value
                self.request_timeout = proc.get("request_timeout", self.request_timeout)
            if self.max_retries == 3:  # default value
                self.max_retries = proc.get("max_retries", self.max_retries)
            if self.batch_size == 10:  # default value
                self.batch_size = proc.get("batch_size", self.batch_size)
    
    def get_provider(self, name: str = "default") -> str:
        """Get provider model name.
        
        Args:
            name: Provider name (groq, gemini, or 'default').
            
        Returns:
            Model name for the provider.
        """
        provider_models = {
            "groq": self.groq_model,
            "gemini": self.gemini_model,
            "default": getattr(self, f"{self.default_provider}_model"),
        }
        return provider_models.get(name, self.groq_model)
    
    def is_provider_enabled(self, name: str) -> bool:
        """Check if a provider is enabled.
        
        Args:
            name: Provider name (groq, gemini, notion).
            
        Returns:
            True if provider is enabled and has credentials.
        """
        if name == "groq":
            return self.enable_groq and bool(self.groq_api_key)
        elif name == "gemini":
            return self.enable_gemini and bool(self.gemini_api_key)
        elif name == "notion":
            return self.enable_notion and bool(self.notion_api_key)
        return False
    
    def get_active_providers(self) -> list[str]:
        """Get list of enabled providers with valid credentials.
        
        Returns:
            List of provider names that are enabled and configured.
        """
        return [
            name for name in ["groq", "gemini", "notion"]
            if self.is_provider_enabled(name)
        ]


_settings_instance: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the application settings instance (singleton pattern).
    
    Uses singleton pattern to ensure consistent configuration throughout
    the application lifetime.
    
    Returns:
        Settings: Configured application settings.
    """
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
        logger.debug("Created new Settings instance")
    return _settings_instance


def reset_settings() -> None:
    """Reset settings singleton (mainly for testing).
    
    Clears the cached settings instance so next call to get_settings()
    will create a fresh instance.
    """
    global _settings_instance
    _settings_instance = None
    logger.debug("Settings singleton reset")
