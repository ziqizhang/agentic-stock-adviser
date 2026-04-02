# Multi-LLM Provider Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let users choose their LLM provider, model, and API key through the web UI — replacing the hardcoded Azure OpenAI configuration.

**Architecture:** A server-side config file (`~/.stock-adviser/config.json`) stores provider settings. A factory function in `llm.py` reads this file and returns the appropriate LangChain `BaseChatModel`. Three new REST endpoints let the frontend read/write settings. A blocking modal prompts the user on first launch.

**Tech Stack:** Python (Pydantic, FastAPI), TypeScript/React (Zustand, Tailwind), LangChain provider packages (`langchain-openai`, `langchain-anthropic`, `langchain-google-genai`)

**Spec:** `docs/superpowers/specs/2026-04-02-multi-llm-provider-design.md`

---

## File Structure

### New files

| File | Responsibility |
|------|---------------|
| `src/stock_adviser/config.py` | `LLMProvider` enum, `LLMConfig` Pydantic model, `load_config()`, `save_config()`, `ConfigNotFoundError` |
| `src/stock_adviser/api/routes/settings.py` | REST endpoints: `GET /settings/status`, `GET /settings`, `POST /settings` |
| `tests/test_config.py` | Tests for config model, load/save, validation |
| `tests/test_settings_api.py` | Tests for settings endpoints |
| `frontend/src/settings/SettingsModal.tsx` | Settings modal component |
| `frontend/src/settings/api.ts` | Settings API client functions |

### Modified files

| File | Change |
|------|--------|
| `src/stock_adviser/llm.py` | Replace Azure-only with provider factory |
| `src/stock_adviser/api/app.py` | Register settings router |
| `src/stock_adviser/events/types.py` | Add `Error` event dataclass |
| `src/stock_adviser/api/routes/stream.py` | Emit `Error` SSE event on LLM exceptions |
| `frontend/src/store/types.ts` | Add `llmConfigured`, `settingsOpen` fields |
| `frontend/src/store/index.ts` | Add settings state and actions |
| `frontend/src/stream/useSSE.ts` | Handle `error` SSE event type |
| `frontend/src/App.tsx` | Check config on mount, render modal, add gear icon |
| `pyproject.toml` | Add optional provider dependencies |
| `.env.example` | Update to show all provider options |

---

## Task 1: Config module — model and enum

**Files:**
- Create: `src/stock_adviser/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write failing tests for LLMProvider enum and LLMConfig model**

```python
# tests/test_config.py
"""Tests for LLM configuration model and persistence."""

import json
from pathlib import Path

import pytest

from stock_adviser.config import (
    ConfigNotFoundError,
    LLMConfig,
    LLMProvider,
    load_config,
    mask_api_key,
    save_config,
)


class TestLLMProvider:
    def test_enum_values(self):
        assert LLMProvider.OPENAI == "openai"
        assert LLMProvider.AZURE_OPENAI == "azure_openai"
        assert LLMProvider.ANTHROPIC == "anthropic"
        assert LLMProvider.GOOGLE == "google"

    def test_enum_from_string(self):
        assert LLMProvider("openai") == LLMProvider.OPENAI


class TestLLMConfig:
    def test_valid_openai_config(self):
        config = LLMConfig(provider=LLMProvider.OPENAI, model="gpt-4o", api_key="sk-test123")
        assert config.provider == LLMProvider.OPENAI

    def test_valid_azure_config(self):
        config = LLMConfig(
            provider=LLMProvider.AZURE_OPENAI,
            model="gpt-4o",
            api_key="abc123",
            azure_endpoint="https://myendpoint.openai.azure.com/",
            azure_api_version="2024-12-01-preview",
            azure_deployment="gpt-4o",
        )
        assert config.azure_endpoint == "https://myendpoint.openai.azure.com/"

    def test_azure_config_requires_endpoint(self):
        with pytest.raises(ValueError, match="azure_endpoint"):
            LLMConfig(
                provider=LLMProvider.AZURE_OPENAI,
                model="gpt-4o",
                api_key="abc123",
            )

    def test_azure_config_requires_api_version(self):
        with pytest.raises(ValueError, match="azure_api_version"):
            LLMConfig(
                provider=LLMProvider.AZURE_OPENAI,
                model="gpt-4o",
                api_key="abc123",
                azure_endpoint="https://myendpoint.openai.azure.com/",
            )

    def test_azure_config_requires_deployment(self):
        with pytest.raises(ValueError, match="azure_deployment"):
            LLMConfig(
                provider=LLMProvider.AZURE_OPENAI,
                model="gpt-4o",
                api_key="abc123",
                azure_endpoint="https://myendpoint.openai.azure.com/",
                azure_api_version="2024-12-01-preview",
            )

    def test_non_azure_ignores_azure_fields(self):
        config = LLMConfig(provider=LLMProvider.ANTHROPIC, model="claude-sonnet-4-20250514", api_key="sk-ant-test")
        assert config.azure_endpoint is None


class TestMaskApiKey:
    def test_masks_middle(self):
        assert mask_api_key("sk-abc123xyz") == "sk-a...xyz"

    def test_short_key_fully_masked(self):
        assert mask_api_key("short") == "***"

    def test_empty_key(self):
        assert mask_api_key("") == "***"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `poetry run pytest tests/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'stock_adviser.config'`

- [ ] **Step 3: Implement the config module**

```python
# src/stock_adviser/config.py
"""LLM provider configuration — enum, model, and persistence."""

import json
import os
import stat
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, model_validator

CONFIG_DIR = Path.home() / ".stock-adviser"
CONFIG_FILE = CONFIG_DIR / "config.json"


class LLMProvider(StrEnum):
    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"


class ConfigNotFoundError(Exception):
    """Raised when no LLM configuration file exists."""


class LLMConfig(BaseModel):
    provider: LLMProvider
    model: str
    api_key: str
    azure_endpoint: str | None = None
    azure_api_version: str | None = None
    azure_deployment: str | None = None

    @model_validator(mode="after")
    def azure_fields_required(self) -> "LLMConfig":
        if self.provider == LLMProvider.AZURE_OPENAI:
            for field in ("azure_endpoint", "azure_api_version", "azure_deployment"):
                if not getattr(self, field):
                    raise ValueError(f"{field} is required for Azure OpenAI")
        return self


def mask_api_key(key: str) -> str:
    """Show first 4 and last 3 characters, mask the rest."""
    if len(key) <= 7:
        return "***"
    return f"{key[:4]}...{key[-3:]}"


def load_config() -> LLMConfig:
    """Read config from ~/.stock-adviser/config.json."""
    if not CONFIG_FILE.exists():
        raise ConfigNotFoundError("LLM not configured. Open settings to configure your provider.")
    data = json.loads(CONFIG_FILE.read_text())
    return LLMConfig(**data)


def save_config(config: LLMConfig) -> None:
    """Write config to ~/.stock-adviser/config.json with 600 permissions."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(config.model_dump_json(indent=2))
    os.chmod(CONFIG_FILE, stat.S_IRUSR | stat.S_IWUSR)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `poetry run pytest tests/test_config.py -v`
Expected: All pass

- [ ] **Step 5: Add persistence tests**

Append to `tests/test_config.py`:

```python
class TestConfigPersistence:
    def test_save_and_load(self, tmp_path, monkeypatch):
        monkeypatch.setattr("stock_adviser.config.CONFIG_DIR", tmp_path)
        monkeypatch.setattr("stock_adviser.config.CONFIG_FILE", tmp_path / "config.json")

        config = LLMConfig(provider=LLMProvider.OPENAI, model="gpt-4o", api_key="sk-test123")
        save_config(config)
        loaded = load_config()
        assert loaded.provider == LLMProvider.OPENAI
        assert loaded.api_key == "sk-test123"

    def test_load_missing_file_raises(self, tmp_path, monkeypatch):
        monkeypatch.setattr("stock_adviser.config.CONFIG_FILE", tmp_path / "nope.json")
        with pytest.raises(ConfigNotFoundError):
            load_config()

    def test_save_creates_directory(self, tmp_path, monkeypatch):
        nested = tmp_path / "nested" / "dir"
        monkeypatch.setattr("stock_adviser.config.CONFIG_DIR", nested)
        monkeypatch.setattr("stock_adviser.config.CONFIG_FILE", nested / "config.json")

        config = LLMConfig(provider=LLMProvider.OPENAI, model="gpt-4o", api_key="sk-test")
        save_config(config)
        assert (nested / "config.json").exists()

    def test_save_sets_file_permissions(self, tmp_path, monkeypatch):
        monkeypatch.setattr("stock_adviser.config.CONFIG_DIR", tmp_path)
        monkeypatch.setattr("stock_adviser.config.CONFIG_FILE", tmp_path / "config.json")

        config = LLMConfig(provider=LLMProvider.OPENAI, model="gpt-4o", api_key="sk-test")
        save_config(config)
        file_stat = os.stat(tmp_path / "config.json")
        assert stat.S_IMODE(file_stat.st_mode) == 0o600
```

- [ ] **Step 6: Run all config tests**

Run: `poetry run pytest tests/test_config.py -v`
Expected: All pass

- [ ] **Step 7: Commit**

```bash
git add src/stock_adviser/config.py tests/test_config.py
git commit -m "feat: add LLM config module with provider enum and persistence"
```

---

## Task 2: LLM factory — multi-provider support

**Files:**
- Modify: `src/stock_adviser/llm.py`
- Create: `tests/test_llm.py`

- [ ] **Step 1: Write failing tests for the provider factory**

```python
# tests/test_llm.py
"""Tests for multi-provider LLM factory."""

from unittest.mock import MagicMock, patch

import pytest

from stock_adviser.config import LLMConfig, LLMProvider
from stock_adviser.llm import get_llm


class TestGetLLM:
    @patch("stock_adviser.llm.load_config")
    @patch("stock_adviser.llm.ChatOpenAI")
    def test_openai_provider(self, mock_cls, mock_load):
        mock_load.return_value = LLMConfig(
            provider=LLMProvider.OPENAI, model="gpt-4o", api_key="sk-test"
        )
        mock_cls.return_value = MagicMock()
        llm = get_llm()
        mock_cls.assert_called_once_with(api_key="sk-test", model="gpt-4o")
        assert llm is mock_cls.return_value

    @patch("stock_adviser.llm.load_config")
    @patch("stock_adviser.llm.AzureChatOpenAI")
    def test_azure_provider(self, mock_cls, mock_load):
        mock_load.return_value = LLMConfig(
            provider=LLMProvider.AZURE_OPENAI,
            model="gpt-4o",
            api_key="abc",
            azure_endpoint="https://ep.openai.azure.com/",
            azure_api_version="2024-12-01-preview",
            azure_deployment="gpt-4o",
        )
        mock_cls.return_value = MagicMock()
        llm = get_llm()
        mock_cls.assert_called_once_with(
            api_key="abc",
            azure_endpoint="https://ep.openai.azure.com/",
            azure_deployment="gpt-4o",
            api_version="2024-12-01-preview",
        )
        assert llm is mock_cls.return_value

    @patch("stock_adviser.llm.load_config")
    @patch("stock_adviser.llm.ChatAnthropic")
    def test_anthropic_provider(self, mock_cls, mock_load):
        mock_load.return_value = LLMConfig(
            provider=LLMProvider.ANTHROPIC, model="claude-sonnet-4-20250514", api_key="sk-ant-test"
        )
        mock_cls.return_value = MagicMock()
        llm = get_llm()
        mock_cls.assert_called_once_with(api_key="sk-ant-test", model="claude-sonnet-4-20250514")
        assert llm is mock_cls.return_value

    @patch("stock_adviser.llm.load_config")
    @patch("stock_adviser.llm.ChatGoogleGenerativeAI")
    def test_google_provider(self, mock_cls, mock_load):
        mock_load.return_value = LLMConfig(
            provider=LLMProvider.GOOGLE, model="gemini-2.5-pro", api_key="AIza-test"
        )
        mock_cls.return_value = MagicMock()
        llm = get_llm()
        mock_cls.assert_called_once_with(api_key="AIza-test", model="gemini-2.5-pro")
        assert llm is mock_cls.return_value

    @patch("stock_adviser.llm.load_config")
    @patch("stock_adviser.llm.ChatOpenAI")
    def test_temperature_passed(self, mock_cls, mock_load):
        mock_load.return_value = LLMConfig(
            provider=LLMProvider.OPENAI, model="gpt-4o", api_key="sk-test"
        )
        mock_cls.return_value = MagicMock()
        get_llm(temperature=0.5)
        mock_cls.assert_called_once_with(api_key="sk-test", model="gpt-4o", temperature=0.5)

    @patch("stock_adviser.llm.load_config")
    def test_missing_package_raises_readable_error(self, mock_load):
        mock_load.return_value = LLMConfig(
            provider=LLMProvider.ANTHROPIC, model="claude-sonnet-4-20250514", api_key="sk-ant-test"
        )
        with patch.dict("sys.modules", {"langchain_anthropic": None}):
            with pytest.raises(ImportError, match="langchain-anthropic"):
                get_llm()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `poetry run pytest tests/test_llm.py -v`
Expected: FAIL — imports from old `llm.py` don't match

- [ ] **Step 3: Rewrite llm.py as a multi-provider factory**

```python
# src/stock_adviser/llm.py
"""LLM factory — returns the appropriate BaseChatModel based on config."""

from langchain_core.language_models import BaseChatModel

from stock_adviser.config import LLMProvider, load_config


def get_llm(temperature: float | None = None) -> BaseChatModel:
    """Create an LLM instance from the saved config file.

    Reads ~/.stock-adviser/config.json on each call so config changes
    take effect without restarting the server.
    """
    config = load_config()
    kwargs: dict = {}
    if temperature is not None:
        kwargs["temperature"] = temperature

    if config.provider == LLMProvider.OPENAI:
        return ChatOpenAI(api_key=config.api_key, model=config.model, **kwargs)

    if config.provider == LLMProvider.AZURE_OPENAI:
        return AzureChatOpenAI(
            api_key=config.api_key,
            azure_endpoint=config.azure_endpoint,
            azure_deployment=config.azure_deployment,
            api_version=config.azure_api_version,
            **kwargs,
        )

    if config.provider == LLMProvider.ANTHROPIC:
        return ChatAnthropic(api_key=config.api_key, model=config.model, **kwargs)

    if config.provider == LLMProvider.GOOGLE:
        return ChatGoogleGenerativeAI(api_key=config.api_key, model=config.model, **kwargs)

    raise ValueError(f"Unknown provider: {config.provider}")


# ---------------------------------------------------------------------------
# Lazy imports — provider packages are optional; fail with a clear message
# ---------------------------------------------------------------------------

def _import_error(package: str, pip_name: str):
    raise ImportError(f"{pip_name} package not installed. Run: pip install {pip_name}")


try:
    from langchain_openai import AzureChatOpenAI, ChatOpenAI
except ImportError:
    def ChatOpenAI(**kw):  # type: ignore[misc]
        _import_error("langchain_openai", "langchain-openai")

    def AzureChatOpenAI(**kw):  # type: ignore[misc]
        _import_error("langchain_openai", "langchain-openai")

try:
    from langchain_anthropic import ChatAnthropic
except ImportError:
    def ChatAnthropic(**kw):  # type: ignore[misc]
        _import_error("langchain_anthropic", "langchain-anthropic")

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    def ChatGoogleGenerativeAI(**kw):  # type: ignore[misc]
        _import_error("langchain_google_genai", "langchain-google-genai")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `poetry run pytest tests/test_llm.py -v`
Expected: All pass

- [ ] **Step 5: Run existing tests to check nothing is broken**

Run: `poetry run pytest tests/ -v`
Expected: All pass (existing tests don't call `get_llm()` directly with real credentials)

- [ ] **Step 6: Commit**

```bash
git add src/stock_adviser/llm.py tests/test_llm.py
git commit -m "feat: multi-provider LLM factory with lazy imports"
```

---

## Task 3: Settings API endpoints

**Files:**
- Create: `src/stock_adviser/api/routes/settings.py`
- Modify: `src/stock_adviser/api/app.py`
- Create: `tests/test_settings_api.py`

- [ ] **Step 1: Write failing tests for the settings endpoints**

```python
# tests/test_settings_api.py
"""Tests for settings API endpoints."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from stock_adviser.api.app import create_app
from stock_adviser.config import LLMConfig, LLMProvider


@pytest.fixture()
def app():
    return create_app()


@pytest.fixture()
def client(app):
    return TestClient(app)


class TestSettingsStatus:
    def test_returns_false_when_no_config(self, client, tmp_path, monkeypatch):
        monkeypatch.setattr("stock_adviser.config.CONFIG_FILE", tmp_path / "nope.json")
        monkeypatch.setattr("stock_adviser.api.routes.settings.CONFIG_FILE", tmp_path / "nope.json")
        response = client.get("/settings/status")
        assert response.status_code == 200
        assert response.json() == {"configured": False}

    def test_returns_true_when_config_exists(self, client, tmp_path, monkeypatch):
        config = LLMConfig(provider=LLMProvider.OPENAI, model="gpt-4o", api_key="sk-test")
        config_file = tmp_path / "config.json"
        config_file.write_text(config.model_dump_json())
        monkeypatch.setattr("stock_adviser.config.CONFIG_FILE", config_file)
        monkeypatch.setattr("stock_adviser.api.routes.settings.CONFIG_FILE", config_file)
        response = client.get("/settings/status")
        assert response.json() == {"configured": True}


class TestGetSettings:
    def test_returns_404_when_no_config(self, client, tmp_path, monkeypatch):
        monkeypatch.setattr("stock_adviser.config.CONFIG_FILE", tmp_path / "nope.json")
        response = client.get("/settings")
        assert response.status_code == 404

    def test_returns_masked_key(self, client, tmp_path, monkeypatch):
        config = LLMConfig(provider=LLMProvider.OPENAI, model="gpt-4o", api_key="sk-abc123xyz")
        config_file = tmp_path / "config.json"
        config_file.write_text(config.model_dump_json())
        monkeypatch.setattr("stock_adviser.config.CONFIG_FILE", config_file)
        response = client.get("/settings")
        assert response.status_code == 200
        data = response.json()
        assert data["api_key"] == "sk-a...xyz"
        assert data["provider"] == "openai"


class TestSaveSettings:
    def test_saves_valid_config(self, client, tmp_path, monkeypatch):
        monkeypatch.setattr("stock_adviser.config.CONFIG_DIR", tmp_path)
        monkeypatch.setattr("stock_adviser.config.CONFIG_FILE", tmp_path / "config.json")
        monkeypatch.setattr("stock_adviser.api.routes.settings.CONFIG_FILE", tmp_path / "config.json")

        with patch("stock_adviser.api.routes.settings.validate_llm_connection", new_callable=AsyncMock):
            response = client.post("/settings", json={
                "provider": "openai",
                "model": "gpt-4o",
                "api_key": "sk-test123456",
            })
        assert response.status_code == 200
        saved = json.loads((tmp_path / "config.json").read_text())
        assert saved["provider"] == "openai"

    def test_rejects_invalid_azure_config(self, client):
        response = client.post("/settings", json={
            "provider": "azure_openai",
            "model": "gpt-4o",
            "api_key": "abc",
        })
        assert response.status_code == 422

    def test_keeps_existing_key_when_empty(self, client, tmp_path, monkeypatch):
        config = LLMConfig(provider=LLMProvider.OPENAI, model="gpt-4o", api_key="sk-original-key-12345")
        config_file = tmp_path / "config.json"
        config_file.write_text(config.model_dump_json())
        monkeypatch.setattr("stock_adviser.config.CONFIG_DIR", tmp_path)
        monkeypatch.setattr("stock_adviser.config.CONFIG_FILE", config_file)
        monkeypatch.setattr("stock_adviser.api.routes.settings.CONFIG_FILE", config_file)

        with patch("stock_adviser.api.routes.settings.validate_llm_connection", new_callable=AsyncMock):
            response = client.post("/settings", json={
                "provider": "openai",
                "model": "gpt-4o-mini",
                "api_key": "",
            })
        assert response.status_code == 200
        saved = json.loads(config_file.read_text())
        assert saved["api_key"] == "sk-original-key-12345"
        assert saved["model"] == "gpt-4o-mini"

    def test_validation_failure_returns_400(self, client, tmp_path, monkeypatch):
        monkeypatch.setattr("stock_adviser.config.CONFIG_DIR", tmp_path)
        monkeypatch.setattr("stock_adviser.config.CONFIG_FILE", tmp_path / "config.json")
        monkeypatch.setattr("stock_adviser.api.routes.settings.CONFIG_FILE", tmp_path / "config.json")

        with patch(
            "stock_adviser.api.routes.settings.validate_llm_connection",
            new_callable=AsyncMock,
            side_effect=Exception("Invalid API key"),
        ):
            response = client.post("/settings", json={
                "provider": "openai",
                "model": "gpt-4o",
                "api_key": "sk-bad-key-123456",
            })
        assert response.status_code == 400
        assert "Invalid API key" in response.json()["detail"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `poetry run pytest tests/test_settings_api.py -v`
Expected: FAIL — `ImportError: cannot import name 'settings'`

- [ ] **Step 3: Create the settings route**

```python
# src/stock_adviser/api/routes/settings.py
"""Settings API — configure LLM provider, model, and credentials."""

import logging

from fastapi import APIRouter, HTTPException
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from stock_adviser.config import (
    CONFIG_FILE,
    ConfigNotFoundError,
    LLMConfig,
    LLMProvider,
    load_config,
    mask_api_key,
    save_config,
)
from stock_adviser.llm import get_llm

router = APIRouter()
logger = logging.getLogger(__name__)


class SettingsRequest(BaseModel):
    provider: LLMProvider
    model: str
    api_key: str = ""
    azure_endpoint: str | None = None
    azure_api_version: str | None = None
    azure_deployment: str | None = None


@router.get("/settings/status")
def settings_status() -> dict:
    """Check whether LLM is configured."""
    try:
        load_config()
        return {"configured": True}
    except (ConfigNotFoundError, Exception):
        return {"configured": False}


@router.get("/settings")
def get_settings() -> dict:
    """Return current config with masked API key."""
    try:
        config = load_config()
    except ConfigNotFoundError:
        raise HTTPException(status_code=404, detail="Not configured")
    data = config.model_dump()
    data["api_key"] = mask_api_key(config.api_key)
    return data


async def validate_llm_connection(config: LLMConfig) -> None:
    """Test the LLM connection with a simple hello message.

    The LLM is constructed with max_retries=3 for automatic retry.
    """
    from stock_adviser.llm import _build_llm

    llm = _build_llm(config, max_retries=3)
    await llm.ainvoke([HumanMessage(content="hello")])


@router.post("/settings")
async def save_settings(body: SettingsRequest) -> dict:
    """Validate and save LLM configuration."""
    api_key = body.api_key

    # If key is empty, keep existing key
    if not api_key:
        try:
            existing = load_config()
            api_key = existing.api_key
        except ConfigNotFoundError:
            raise HTTPException(status_code=422, detail="API key is required for first-time setup")

    config = LLMConfig(
        provider=body.provider,
        model=body.model,
        api_key=api_key,
        azure_endpoint=body.azure_endpoint,
        azure_api_version=body.azure_api_version,
        azure_deployment=body.azure_deployment,
    )

    try:
        await validate_llm_connection(config)
    except Exception as exc:
        logger.warning("LLM validation failed: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))

    save_config(config)
    return {"status": "ok"}
```

- [ ] **Step 4: Update llm.py — extract `_build_llm` helper for reuse by validation**

Add `_build_llm` to `src/stock_adviser/llm.py` so the settings endpoint can build a test LLM from an arbitrary config without writing it to disk first:

```python
# Add this function before get_llm() in src/stock_adviser/llm.py

def _build_llm(config: "LLMConfig", max_retries: int = 0, temperature: float | None = None) -> BaseChatModel:
    """Build an LLM instance from a config object.

    Used by get_llm() (reads from file) and by the settings endpoint (validates before saving).
    """
    from stock_adviser.config import LLMProvider

    kwargs: dict = {}
    if temperature is not None:
        kwargs["temperature"] = temperature
    if max_retries:
        kwargs["max_retries"] = max_retries

    if config.provider == LLMProvider.OPENAI:
        return ChatOpenAI(api_key=config.api_key, model=config.model, **kwargs)

    if config.provider == LLMProvider.AZURE_OPENAI:
        return AzureChatOpenAI(
            api_key=config.api_key,
            azure_endpoint=config.azure_endpoint,
            azure_deployment=config.azure_deployment,
            api_version=config.azure_api_version,
            **kwargs,
        )

    if config.provider == LLMProvider.ANTHROPIC:
        return ChatAnthropic(api_key=config.api_key, model=config.model, **kwargs)

    if config.provider == LLMProvider.GOOGLE:
        return ChatGoogleGenerativeAI(api_key=config.api_key, model=config.model, **kwargs)

    raise ValueError(f"Unknown provider: {config.provider}")


def get_llm(temperature: float | None = None) -> BaseChatModel:
    """Create an LLM instance from the saved config file."""
    config = load_config()
    return _build_llm(config, temperature=temperature)
```

- [ ] **Step 5: Register the settings router in app.py**

In `src/stock_adviser/api/app.py`, add:

```python
from stock_adviser.api.routes.settings import router as settings_router
```

And in `create_app()`, add after the existing router registrations:

```python
app.include_router(settings_router)
```

- [ ] **Step 6: Run tests**

Run: `poetry run pytest tests/test_settings_api.py -v`
Expected: All pass

- [ ] **Step 7: Run all tests**

Run: `poetry run pytest tests/ -v`
Expected: All pass

- [ ] **Step 8: Commit**

```bash
git add src/stock_adviser/api/routes/settings.py src/stock_adviser/api/app.py src/stock_adviser/llm.py tests/test_settings_api.py
git commit -m "feat: settings API with validation and key masking"
```

---

## Task 4: Error SSE event type

**Files:**
- Modify: `src/stock_adviser/events/types.py`
- Modify: `src/stock_adviser/api/routes/stream.py`
- Modify: `frontend/src/stream/useSSE.ts`

- [ ] **Step 1: Add Error event to types.py**

Add at the end of `src/stock_adviser/events/types.py`, after the `Done` class:

```python
@dataclass
class Error(SSEEvent):
    message: str = ""
    event_type: str = "error"
```

- [ ] **Step 2: Update stream.py to emit Error event**

In `src/stock_adviser/api/routes/stream.py`, add `Error` to the imports from `stock_adviser.events.types`:

```python
from stock_adviser.events.types import Done, Error, Token, ToolResult, ToolStart
```

Replace the `except Exception` block (lines 58-60) with:

```python
        except Exception as exc:
            logger.exception("Error during agent streaming")
            yield Error(message=str(exc)).to_sse()
            yield Done().to_sse()
```

- [ ] **Step 3: Handle error event in useSSE.ts**

In `frontend/src/stream/useSSE.ts`, add a new case in the switch block, before the `"done"` case:

```typescript
        case "error":
          addStatusMessage(`Error: ${data.message as string}`);
          break;
```

- [ ] **Step 4: Run existing tests to verify nothing broke**

Run: `poetry run pytest tests/ -v`
Expected: All pass

- [ ] **Step 5: Commit**

```bash
git add src/stock_adviser/events/types.py src/stock_adviser/api/routes/stream.py frontend/src/stream/useSSE.ts
git commit -m "feat: add Error SSE event for surfacing LLM errors to chat"
```

---

## Task 5: Frontend — settings API client and store changes

**Files:**
- Create: `frontend/src/settings/api.ts`
- Modify: `frontend/src/store/types.ts`
- Modify: `frontend/src/store/index.ts`

- [ ] **Step 1: Create the settings API client**

```typescript
// frontend/src/settings/api.ts
const API_BASE = "";

export interface LLMSettings {
  provider: string;
  model: string;
  api_key: string;
  azure_endpoint: string | null;
  azure_api_version: string | null;
  azure_deployment: string | null;
}

export async function getSettingsStatus(): Promise<boolean> {
  const res = await fetch(`${API_BASE}/settings/status`);
  const data = await res.json();
  return data.configured;
}

export async function getSettings(): Promise<LLMSettings> {
  const res = await fetch(`${API_BASE}/settings`);
  if (!res.ok) throw new Error("Not configured");
  return res.json();
}

export async function saveSettings(settings: LLMSettings): Promise<void> {
  const res = await fetch(`${API_BASE}/settings`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(settings),
  });
  if (!res.ok) {
    const data = await res.json();
    throw new Error(data.detail || "Failed to save settings");
  }
}
```

- [ ] **Step 2: Add settings state to store types**

In `frontend/src/store/types.ts`, add to the `AppState` interface, after the `toggleChat` line:

```typescript
  // Settings
  llmConfigured: boolean;
  settingsOpen: boolean;
  setLlmConfigured: (configured: boolean) => void;
  setSettingsOpen: (open: boolean) => void;
```

- [ ] **Step 3: Add settings state to store implementation**

In `frontend/src/store/index.ts`, add after the `toggleChat` line (before the closing `}));`):

```typescript
  // Settings
  llmConfigured: false,
  settingsOpen: false,
  setLlmConfigured: (configured) => set({ llmConfigured: configured }),
  setSettingsOpen: (open) => set({ settingsOpen: open }),
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/settings/api.ts frontend/src/store/types.ts frontend/src/store/index.ts
git commit -m "feat: settings API client and store state"
```

---

## Task 6: Frontend — settings modal component

**Files:**
- Create: `frontend/src/settings/SettingsModal.tsx`

- [ ] **Step 1: Create the modal component**

```tsx
// frontend/src/settings/SettingsModal.tsx
import { useState, useEffect } from "react";
import { useStore } from "../store";
import { getSettings, saveSettings, type LLMSettings } from "./api";

const PROVIDERS = [
  { value: "openai", label: "OpenAI" },
  { value: "azure_openai", label: "Azure OpenAI" },
  { value: "anthropic", label: "Anthropic" },
  { value: "google", label: "Google Gemini" },
];

export function SettingsModal() {
  const settingsOpen = useStore((s) => s.settingsOpen);
  const setSettingsOpen = useStore((s) => s.setSettingsOpen);
  const setLlmConfigured = useStore((s) => s.setLlmConfigured);

  const [provider, setProvider] = useState("openai");
  const [model, setModel] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [azureEndpoint, setAzureEndpoint] = useState("");
  const [azureApiVersion, setAzureApiVersion] = useState("");
  const [azureDeployment, setAzureDeployment] = useState("");
  const [maskedKey, setMaskedKey] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const isAzure = provider === "azure_openai";

  // Load existing settings when modal opens
  useEffect(() => {
    if (!settingsOpen) return;
    getSettings()
      .then((s) => {
        setProvider(s.provider);
        setModel(s.model);
        setMaskedKey(s.api_key);
        setApiKey("");
        setAzureEndpoint(s.azure_endpoint || "");
        setAzureApiVersion(s.azure_api_version || "");
        setAzureDeployment(s.azure_deployment || "");
      })
      .catch(() => {
        // Not configured yet — keep defaults
      });
  }, [settingsOpen]);

  if (!settingsOpen) return null;

  const handleSave = async () => {
    setError("");
    setSaving(true);
    try {
      const settings: LLMSettings = {
        provider,
        model,
        api_key: apiKey,
        azure_endpoint: isAzure ? azureEndpoint : null,
        azure_api_version: isAzure ? azureApiVersion : null,
        azure_deployment: isAzure ? azureDeployment : null,
      };
      await saveSettings(settings);
      setLlmConfigured(true);
      setSettingsOpen(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  };

  const canSave = model.trim() && (apiKey.trim() || maskedKey) && (!isAzure || (azureEndpoint.trim() && azureApiVersion.trim() && azureDeployment.trim()));

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-gray-900 border border-gray-700 rounded-xl shadow-2xl w-full max-w-md p-6 space-y-4">
        <h2 className="text-lg font-semibold text-gray-100">LLM Settings</h2>
        <p className="text-sm text-gray-400">
          Configure your LLM provider to get started. Make sure the model name
          exactly matches your provider's naming (e.g. <code className="text-teal-400">gpt-4o</code>,{" "}
          <code className="text-teal-400">claude-sonnet-4-20250514</code>).
        </p>

        {/* Provider */}
        <label className="block">
          <span className="text-sm text-gray-400">Provider</span>
          <select
            value={provider}
            onChange={(e) => setProvider(e.target.value)}
            className="mt-1 block w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 outline-none focus:ring-1 focus:ring-teal-400/50"
          >
            {PROVIDERS.map((p) => (
              <option key={p.value} value={p.value}>
                {p.label}
              </option>
            ))}
          </select>
        </label>

        {/* Model */}
        <label className="block">
          <span className="text-sm text-gray-400">
            {isAzure ? "Deployment name" : "Model"}
          </span>
          <input
            type="text"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            placeholder={isAzure ? "e.g. gpt-4o" : "e.g. gpt-4o, claude-sonnet-4-20250514"}
            className="mt-1 block w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-500 outline-none focus:ring-1 focus:ring-teal-400/50"
          />
        </label>

        {/* API Key */}
        <label className="block">
          <span className="text-sm text-gray-400">API Key</span>
          <input
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder={maskedKey || "Paste your API key"}
            className="mt-1 block w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-500 outline-none focus:ring-1 focus:ring-teal-400/50"
          />
        </label>

        {/* Azure-specific fields */}
        {isAzure && (
          <>
            <label className="block">
              <span className="text-sm text-gray-400">Azure Endpoint</span>
              <input
                type="text"
                value={azureEndpoint}
                onChange={(e) => setAzureEndpoint(e.target.value)}
                placeholder="https://your-resource.openai.azure.com/"
                className="mt-1 block w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-500 outline-none focus:ring-1 focus:ring-teal-400/50"
              />
            </label>
            <label className="block">
              <span className="text-sm text-gray-400">API Version</span>
              <input
                type="text"
                value={azureApiVersion}
                onChange={(e) => setAzureApiVersion(e.target.value)}
                placeholder="e.g. 2024-12-01-preview"
                className="mt-1 block w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-500 outline-none focus:ring-1 focus:ring-teal-400/50"
              />
            </label>
            <label className="block">
              <span className="text-sm text-gray-400">Azure Deployment</span>
              <input
                type="text"
                value={azureDeployment}
                onChange={(e) => setAzureDeployment(e.target.value)}
                placeholder="e.g. gpt-4o"
                className="mt-1 block w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-500 outline-none focus:ring-1 focus:ring-teal-400/50"
              />
            </label>
          </>
        )}

        {/* Error message */}
        {error && (
          <p className="text-sm text-red-400">{error}</p>
        )}

        {/* Save button */}
        <button
          onClick={handleSave}
          disabled={!canSave || saving}
          className="w-full bg-teal-600 hover:bg-teal-500 disabled:bg-gray-700 disabled:text-gray-500 text-white rounded-lg px-4 py-2 text-sm font-medium transition-colors"
        >
          {saving ? "Validating..." : "Save"}
        </button>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/settings/SettingsModal.tsx
git commit -m "feat: settings modal component"
```

---

## Task 7: Frontend — wire modal into App.tsx

**Files:**
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Update App.tsx to check config status and render modal**

Replace the full content of `frontend/src/App.tsx`:

```tsx
import { useState, useRef, useCallback, useEffect } from "react";
import { ChatPanel, SESSION_ID } from "./chat/ChatPanel";
import { Dashboard } from "./dashboard/Dashboard";
import { SettingsModal } from "./settings/SettingsModal";
import { getSettingsStatus } from "./settings/api";
import { useSSE } from "./stream/useSSE";
import { useStore } from "./store";

const MIN_CHAT_WIDTH = 280;
const DEFAULT_CHAT_WIDTH = 360;

function App() {
  useSSE(SESSION_ID);

  const llmConfigured = useStore((s) => s.llmConfigured);
  const setLlmConfigured = useStore((s) => s.setLlmConfigured);
  const setSettingsOpen = useStore((s) => s.setSettingsOpen);

  const [chatWidth, setChatWidth] = useState(DEFAULT_CHAT_WIDTH);
  const dragging = useRef(false);

  // Check config on mount
  useEffect(() => {
    getSettingsStatus().then((configured) => {
      setLlmConfigured(configured);
      if (!configured) {
        setSettingsOpen(true);
      }
    });
  }, [setLlmConfigured, setSettingsOpen]);

  const onMouseDown = useCallback(() => {
    dragging.current = true;
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";

    const onMouseMove = (e: MouseEvent) => {
      if (!dragging.current) return;
      const maxWidth = window.innerWidth / 2;
      const newWidth = Math.min(maxWidth, Math.max(MIN_CHAT_WIDTH, window.innerWidth - e.clientX));
      setChatWidth(newWidth);
    };

    const onMouseUp = () => {
      dragging.current = false;
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("mouseup", onMouseUp);
    };

    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseup", onMouseUp);
  }, []);

  return (
    <div className="h-screen bg-gray-950 text-gray-200 flex">
      {/* Gear icon */}
      <button
        onClick={() => setSettingsOpen(true)}
        className="fixed top-3 right-3 z-40 text-gray-500 hover:text-teal-400 transition-colors"
        title="LLM Settings"
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
        </svg>
      </button>

      <div className="flex-1 min-w-0 overflow-hidden">
        <Dashboard />
      </div>
      {/* Drag handle */}
      <div
        onMouseDown={onMouseDown}
        className="w-1 cursor-col-resize bg-gray-800 hover:bg-teal-400/50 transition-colors flex-shrink-0"
      />
      <div style={{ width: chatWidth }} className="flex-shrink-0 border-l border-gray-800">
        <ChatPanel />
      </div>

      <SettingsModal />
    </div>
  );
}

export default App;
```

- [ ] **Step 2: Manually verify in browser**

Run the backend and frontend:
```bash
poetry run uvicorn stock_adviser.api.app:create_app --factory --reload --port 8000 &
cd frontend && npm run dev &
```

Open `http://localhost:5173`. Expected:
- If no `~/.stock-adviser/config.json` exists → modal appears, blocking the UI
- Fill in provider, model, API key → click Save → "Validating..." spinner → modal dismisses
- Gear icon in top-right opens modal again with current values (masked key as placeholder)

- [ ] **Step 3: Commit**

```bash
git add frontend/src/App.tsx
git commit -m "feat: wire settings modal and gear icon into App"
```

---

## Task 8: Update dependencies and env example

**Files:**
- Modify: `pyproject.toml`
- Modify: `.env.example`

- [ ] **Step 1: Add optional provider dependencies to pyproject.toml**

In `pyproject.toml`, add the optional dependencies after `sse-starlette` (line 23) and before `[tool.poetry.group.dev.dependencies]` (line 25):

```toml
langchain-anthropic = {version = "^0.3", optional = true}
langchain-google-genai = {version = "^0.5", optional = true}

[tool.poetry.extras]
anthropic = ["langchain-anthropic"]
google = ["langchain-google-genai"]
all-providers = ["langchain-anthropic", "langchain-google-genai"]
```

- [ ] **Step 2: Update .env.example**

Replace the content of `.env.example`:

```
# LLM configuration is now managed through the web UI (Settings modal).
# On first launch, you'll be prompted to select your provider and enter credentials.
# Config is saved to ~/.stock-adviser/config.json
#
# Supported providers: OpenAI, Azure OpenAI, Anthropic, Google Gemini
#
# To install optional provider packages:
#   poetry install -E anthropic
#   poetry install -E google
#   poetry install -E all-providers

# LangSmith (optional, for tracing)
LANGSMITH_API_KEY=your-key-here
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=agentic-stock-adviser
```

- [ ] **Step 3: Run full test suite**

Run: `poetry run pytest tests/ -v`
Expected: All pass

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml .env.example
git commit -m "feat: add optional provider deps and update env example"
```

---

## Task 9: E2E smoke test script

**Files:**
- Create: `tests/e2e_settings.sh`

- [ ] **Step 1: Write a curl-based e2e test**

```bash
#!/usr/bin/env bash
# E2E smoke test for settings API
# Requires: backend running on localhost:8000
set -euo pipefail

BASE="http://localhost:8000"
PASS=0
FAIL=0

check() {
  local desc="$1" expected="$2" actual="$3"
  if [[ "$actual" == *"$expected"* ]]; then
    echo "  PASS: $desc"
    ((PASS++))
  else
    echo "  FAIL: $desc (expected '$expected', got '$actual')"
    ((FAIL++))
  fi
}

echo "=== Settings API E2E ==="

# 1. Status endpoint
echo ""
echo "--- GET /settings/status ---"
STATUS=$(curl -s "$BASE/settings/status")
check "status returns JSON" "configured" "$STATUS"

# 2. GET settings when not configured
echo ""
echo "--- GET /settings (no config) ---"
GET_RESP=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/settings")
# May be 200 or 404 depending on whether config exists
echo "  INFO: GET /settings returned HTTP $GET_RESP"

# 3. POST settings with bad key (should fail validation)
echo ""
echo "--- POST /settings (bad key, expect 400) ---"
BAD_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE/settings" \
  -H "Content-Type: application/json" \
  -d '{"provider":"openai","model":"gpt-4o","api_key":"sk-bad-key"}')
BAD_CODE=$(echo "$BAD_RESP" | tail -1)
check "bad key returns 400" "400" "$BAD_CODE"

# 4. POST settings with missing azure fields
echo ""
echo "--- POST /settings (azure missing fields, expect 422) ---"
AZ_RESP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/settings" \
  -H "Content-Type: application/json" \
  -d '{"provider":"azure_openai","model":"gpt-4o","api_key":"abc"}')
check "azure missing fields returns 422" "422" "$AZ_RESP"

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
[[ $FAIL -eq 0 ]] && exit 0 || exit 1
```

- [ ] **Step 2: Make it executable**

```bash
chmod +x tests/e2e_settings.sh
```

- [ ] **Step 3: Commit**

```bash
git add tests/e2e_settings.sh
git commit -m "feat: add e2e smoke test for settings API"
```

---

Plan complete and saved to `docs/superpowers/plans/2026-04-02-multi-llm-provider.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?