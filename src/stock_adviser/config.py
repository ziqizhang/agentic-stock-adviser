"""LLM provider configuration: model, enum, persistence."""

from __future__ import annotations

import os
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, model_validator

CONFIG_DIR: Path = Path.home() / ".stock-adviser"
CONFIG_FILE: Path = CONFIG_DIR / "config.json"


class LLMProvider(StrEnum):
    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"


class ConfigNotFoundError(Exception):
    """Raised when the config file does not exist."""


class LLMConfig(BaseModel):
    provider: LLMProvider
    model: str
    api_key: str
    azure_endpoint: str | None = None
    azure_api_version: str | None = None
    azure_deployment: str | None = None

    @model_validator(mode="after")
    def _validate_azure_fields(self) -> LLMConfig:
        if self.provider is not LLMProvider.AZURE_OPENAI:
            return self
        missing = [
            name for name in ("azure_endpoint", "azure_api_version", "azure_deployment") if not getattr(self, name)
        ]
        if missing:
            raise ValueError(f"Provider is azure_openai but these fields are missing/empty: {', '.join(missing)}")
        return self


def mask_api_key(key: str) -> str:
    """Show first 4 and last 3 chars, mask middle with '...'. Short keys return '***'."""
    if len(key) <= 7:
        return "***"
    return f"{key[:4]}...{key[-3:]}"


def load_config() -> LLMConfig:
    """Read config from ~/.stock-adviser/config.json."""
    if not CONFIG_FILE.exists():
        raise ConfigNotFoundError(f"Config file not found: {CONFIG_FILE}")
    return LLMConfig.model_validate_json(CONFIG_FILE.read_text())


def save_config(config: LLMConfig) -> None:
    """Write config as JSON to ~/.stock-adviser/config.json with 0o600 permissions."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(config.model_dump_json(indent=2))
    os.chmod(CONFIG_FILE, 0o600)
