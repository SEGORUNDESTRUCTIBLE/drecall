"""Application settings and configuration management.

Centralized configuration system that merges settings from multiple sources:
- Defaults
- .env environment variables
- Optional settings.json for non-sensitive overrides

This module exposes a singleton `settings` instance for application-wide use.
"""

import json
import logging
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[1]

logger = logging.getLogger(__name__)


class Environment(str, Enum):
    development = "development"
    staging = "staging"
    production = "production"


class ProviderName(str, Enum):
    groq = "groq"
    gemini = "gemini"


class Settings(BaseSettings):
    """Application configuration settings.

    Loads configuration from environment variables, optional JSON config,
    and default values. Provides typed, validated access to application
    configuration values.
    """

    app_name: str = "drecall"
    version: str = "0.1.0"
    environment: Environment = Field(Environment.development)
    debug: bool = Field(False)

    log_level: str = Field("INFO")
    log_format: str = Field("json")

    project_root: Path = Field(default_factory=lambda: BASE_DIR)
    log_dir: Path = Field(default_factory=lambda: BASE_DIR / "logs")
    templates_dir: Path = Field(default_factory=lambda: BASE_DIR / "templates")
    screenshot_dir: Path = Field(default_factory=lambda: BASE_DIR / "screenshots")
    export_dir: Path = Field(default_factory=lambda: BASE_DIR / "exports")
    temp_dir: Path = Field(default_factory=lambda: BASE_DIR / "tmp")
    config_dir: Path = Field(default_factory=lambda: BASE_DIR / "config")

    request_timeout: int = Field(30)
    max_retries: int = Field(3)
    batch_size: int = Field(10)

    groq_api_key: Optional[str] = Field(None)
    groq_model: str = Field("mixtral")
    enable_groq: bool = Field(False)

    gemini_api_key: Optional[str] = Field(None)
    gemini_model: str = Field("pro")
    enable_gemini: bool = Field(False)

    notion_api_key: Optional[str] = Field(None)
    notion_datasource_id: Optional[str] = Field(None)
    notion_database_id: Optional[str] = Field(None)
    enable_notion: bool = Field(False)

    default_provider: ProviderName = Field(ProviderName.groq)

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_ignore_empty=True,
        extra="ignore",
    )

    @property
    def logs_dir(self) -> Path:
        return self.log_dir

    @field_validator("log_level", mode="before")
    def normalize_log_level(cls, value: str) -> str:
        return str(value).upper()

    @field_validator("request_timeout", "max_retries", "batch_size", mode="before")
    def validate_positive_ints(cls, value: Any) -> int:
        if value is None:
            raise ValueError("Value must be provided and be a positive integer")
        try:
            value_int = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("Value must be an integer") from exc
        if value_int < 1:
            raise ValueError("Value must be a positive integer")
        return value_int

    @model_validator(mode="after")
    def validate_provider_flags(self) -> "Settings":
        if self.enable_groq and not self.groq_api_key:
            logger.warning("ENABLE_GROQ is true but GROQ_API_KEY is not configured")
        if self.enable_gemini and not self.gemini_api_key:
            logger.warning("ENABLE_GEMINI is true but GEMINI_API_KEY is not configured")
        if self.enable_notion:
            if not self.notion_api_key:
                logger.warning("ENABLE_NOTION is true but NOTION_API_KEY is not configured")
            if not (self.notion_datasource_id or self.notion_database_id):
                logger.warning("ENABLE_NOTION is true but no Notion datasource or database ID is configured")
        return self

    def model_post_init(self, __context: Any) -> None:
        self.log_dir = self._resolve_path(self.log_dir, self.project_root / "logs")
        self.templates_dir = self._resolve_path(self.templates_dir, self.project_root / "templates")
        self.screenshot_dir = self._resolve_path(self.screenshot_dir, self.project_root / "screenshots")
        self.export_dir = self._resolve_path(self.export_dir, self.project_root / "exports")
        self.temp_dir = self._resolve_path(self.temp_dir, self.project_root / "tmp")
        self.config_dir = self._resolve_path(self.config_dir, self.project_root / "config")

        for directory in [self.log_dir, self.templates_dir, self.screenshot_dir, self.export_dir, self.temp_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {directory}")

        self._load_json_config()
        logger.debug(f"Settings initialized: environment={self.environment}, debug={self.debug}")

    def _resolve_path(self, path: Path, default_path: Path) -> Path:
        resolved = Path(path)
        if not resolved.is_absolute():
            resolved = self.project_root / resolved
        return resolved

    def _load_json_config(self) -> None:
        config_file = self.config_dir / "settings.json"
        if not config_file.exists():
            logger.debug(f"No settings.json found at {config_file}")
            return
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                json_config = json.load(f)
            logger.debug(f"Loaded settings.json: {config_file}")
            self._merge_json_settings(json_config)
        except json.JSONDecodeError as exc:
            logger.warning(f"Invalid JSON in settings.json: {exc}")
        except Exception as exc:
            logger.warning(f"Failed to load settings.json: {exc}")

    def _merge_json_settings(self, json_config: Dict[str, Any]) -> None:
        if "processing" in json_config:
            proc = json_config["processing"]
            if self.request_timeout == 30:
                self.request_timeout = proc.get("request_timeout", self.request_timeout)
            if self.max_retries == 3:
                self.max_retries = proc.get("max_retries", self.max_retries)
            if self.batch_size == 10:
                self.batch_size = proc.get("batch_size", self.batch_size)

    def get_provider(self, name: str = "default") -> str:
        provider_models = {
            "groq": self.groq_model,
            "gemini": self.gemini_model,
            "default": getattr(self, f"{self.default_provider.value}_model"),
        }
        return provider_models.get(name, self.groq_model)

    def is_provider_enabled(self, name: str) -> bool:
        if name == "groq":
            return self.enable_groq and bool(self.groq_api_key)
        if name == "gemini":
            return self.enable_gemini and bool(self.gemini_api_key)
        if name == "notion":
            return self.enable_notion and bool(self.notion_api_key)
        return False

    def get_active_providers(self) -> List[str]:
        return [name for name in ["groq", "gemini", "notion"] if self.is_provider_enabled(name)]

    def validate_configuration(self) -> None:
        errors: List[str] = []
        if self.enable_groq and not self.groq_api_key:
            errors.append("GROQ_API_KEY is required when ENABLE_GROQ is true")
        if self.enable_gemini and not self.gemini_api_key:
            errors.append("GEMINI_API_KEY is required when ENABLE_GEMINI is true")
        if self.enable_notion:
            if not self.notion_api_key:
                errors.append("NOTION_API_KEY is required when ENABLE_NOTION is true")
            if not (self.notion_datasource_id or self.notion_database_id):
                errors.append("NOTION_DATASOURCE_ID or NOTION_DATABASE_ID is required when ENABLE_NOTION is true")
        if errors:
            raise ValueError("Invalid configuration: " + "; ".join(errors))


_settings_instance: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings_instance
    if _settings_instance is None:
        env_file_path = Settings.model_config['env_file']
        logger.debug(
            "Resolved settings env file: %s (exists=%s)",
            env_file_path,
            Path(env_file_path).exists(),
        )
        _settings_instance = Settings()
        # Overlay critical environment variables to ensure runtime overrides
        try:
            import os

            env_overrides = {
                "GROQ_API_KEY": "groq_api_key",
                "GEMINI_API_KEY": "gemini_api_key",
                "GROQ_MODEL": "groq_model",
                "GEMINI_MODEL": "gemini_model",
                "DEFAULT_PROVIDER": "default_provider",
                "ENABLE_GROQ": "enable_groq",
                "ENABLE_GEMINI": "enable_gemini",
                "ENABLE_NOTION": "enable_notion",
                "NOTION_DATASOURCE_ID": "notion_datasource_id",
                "NOTION_DATABASE_ID": "notion_database_id",
            }
            for env_key, attr in env_overrides.items():
                val = os.environ.get(env_key)
                if val is None:
                    continue
                # normalize booleans
                if attr.startswith("enable_"):
                    setattr(_settings_instance, attr, str(val).lower() in ("1", "true", "yes", "on"))
                elif attr == "default_provider":
                    try:
                        from config.settings import ProviderName

                        setattr(_settings_instance, attr, ProviderName(str(val)))
                    except Exception:
                        pass
                else:
                    if val != "":
                        setattr(_settings_instance, attr, val)

        except Exception:
            logger.debug("Failed to overlay environment variables on Settings")
        logger.debug("Created new Settings instance")
    return _settings_instance


def reset_settings() -> None:
    global _settings_instance
    _settings_instance = None
    logger.debug("Settings singleton reset")


settings = get_settings()
