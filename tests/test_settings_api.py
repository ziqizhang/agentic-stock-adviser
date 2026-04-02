"""Tests for settings API endpoints."""

from pathlib import Path
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from stock_adviser.api.app import create_app
from stock_adviser.config import LLMConfig, LLMProvider


def _write_config(tmp_path: Path, api_key: str = "sk-abc123xyz") -> None:
    """Helper: write a valid config file into tmp_path."""
    config = LLMConfig(provider=LLMProvider.OPENAI, model="gpt-4o", api_key=api_key)
    cfg_file = tmp_path / "config.json"
    cfg_file.write_text(config.model_dump_json(indent=2))


def _patch_config_paths(monkeypatch, tmp_path: Path) -> None:
    """Redirect CONFIG_FILE and CONFIG_DIR to tmp_path in both config and settings modules."""
    cfg_file = tmp_path / "config.json"
    monkeypatch.setattr("stock_adviser.config.CONFIG_DIR", tmp_path)
    monkeypatch.setattr("stock_adviser.config.CONFIG_FILE", cfg_file)
    monkeypatch.setattr("stock_adviser.api.routes.settings.CONFIG_FILE", cfg_file)


class TestSettingsStatus:
    def test_status_false_when_no_config(self, tmp_path, monkeypatch):
        _patch_config_paths(monkeypatch, tmp_path)
        client = TestClient(create_app())
        resp = client.get("/settings/status")
        assert resp.status_code == 200
        assert resp.json() == {"configured": False}

    def test_status_true_when_config_exists(self, tmp_path, monkeypatch):
        _patch_config_paths(monkeypatch, tmp_path)
        _write_config(tmp_path)
        client = TestClient(create_app())
        resp = client.get("/settings/status")
        assert resp.status_code == 200
        assert resp.json() == {"configured": True}


class TestGetSettings:
    def test_get_returns_404_when_no_config(self, tmp_path, monkeypatch):
        _patch_config_paths(monkeypatch, tmp_path)
        client = TestClient(create_app())
        resp = client.get("/settings")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Not configured"

    def test_get_returns_masked_key(self, tmp_path, monkeypatch):
        _patch_config_paths(monkeypatch, tmp_path)
        _write_config(tmp_path, api_key="sk-abc123xyz")
        client = TestClient(create_app())
        resp = client.get("/settings")
        assert resp.status_code == 200
        data = resp.json()
        assert data["api_key"] == "sk-a...xyz"
        assert data["provider"] == "openai"
        assert data["model"] == "gpt-4o"


class TestPostSettings:
    def test_post_saves_valid_config(self, tmp_path, monkeypatch):
        _patch_config_paths(monkeypatch, tmp_path)
        mock_validate = AsyncMock()
        monkeypatch.setattr("stock_adviser.api.routes.settings.validate_llm_connection", mock_validate)
        client = TestClient(create_app())
        resp = client.post(
            "/settings",
            json={
                "provider": "openai",
                "model": "gpt-4o",
                "api_key": "sk-test-key-12345",
            },
        )
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}
        assert (tmp_path / "config.json").exists()
        saved = LLMConfig.model_validate_json((tmp_path / "config.json").read_text())
        assert saved.api_key == "sk-test-key-12345"
        mock_validate.assert_awaited_once()

    def test_post_rejects_invalid_azure(self, tmp_path, monkeypatch):
        _patch_config_paths(monkeypatch, tmp_path)
        mock_validate = AsyncMock()
        monkeypatch.setattr("stock_adviser.api.routes.settings.validate_llm_connection", mock_validate)
        client = TestClient(create_app())
        resp = client.post(
            "/settings",
            json={
                "provider": "azure_openai",
                "model": "gpt-4o",
                "api_key": "sk-test",
                # missing azure_endpoint, azure_api_version, azure_deployment
            },
        )
        assert resp.status_code == 422

    def test_post_keeps_existing_key_when_empty(self, tmp_path, monkeypatch):
        _patch_config_paths(monkeypatch, tmp_path)
        _write_config(tmp_path, api_key="sk-original-key-999")
        mock_validate = AsyncMock()
        monkeypatch.setattr("stock_adviser.api.routes.settings.validate_llm_connection", mock_validate)
        client = TestClient(create_app())
        resp = client.post(
            "/settings",
            json={
                "provider": "openai",
                "model": "gpt-4o-mini",
                "api_key": "",
            },
        )
        assert resp.status_code == 200
        saved = LLMConfig.model_validate_json((tmp_path / "config.json").read_text())
        assert saved.api_key == "sk-original-key-999"
        assert saved.model == "gpt-4o-mini"

    def test_post_validation_failure_returns_400(self, tmp_path, monkeypatch):
        _patch_config_paths(monkeypatch, tmp_path)
        mock_validate = AsyncMock(side_effect=Exception("Invalid API key"))
        monkeypatch.setattr("stock_adviser.api.routes.settings.validate_llm_connection", mock_validate)
        client = TestClient(create_app())
        resp = client.post(
            "/settings",
            json={
                "provider": "openai",
                "model": "gpt-4o",
                "api_key": "sk-bad-key-12345",
            },
        )
        assert resp.status_code == 400
        assert "Invalid API key" in resp.json()["detail"]

    def test_post_requires_key_for_first_time(self, tmp_path, monkeypatch):
        _patch_config_paths(monkeypatch, tmp_path)
        mock_validate = AsyncMock()
        monkeypatch.setattr("stock_adviser.api.routes.settings.validate_llm_connection", mock_validate)
        client = TestClient(create_app())
        resp = client.post(
            "/settings",
            json={
                "provider": "openai",
                "model": "gpt-4o",
                "api_key": "",
            },
        )
        assert resp.status_code == 422
        assert "API key is required" in resp.json()["detail"]
