"""Tests for LLM config module."""

import os
import stat

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

    def test_construction_from_string(self):
        assert LLMProvider("openai") is LLMProvider.OPENAI
        assert LLMProvider("azure_openai") is LLMProvider.AZURE_OPENAI
        assert LLMProvider("anthropic") is LLMProvider.ANTHROPIC
        assert LLMProvider("google") is LLMProvider.GOOGLE


class TestLLMConfig:
    def test_valid_openai(self):
        cfg = LLMConfig(provider=LLMProvider.OPENAI, model="gpt-4o", api_key="sk-abc123")
        assert cfg.provider == LLMProvider.OPENAI
        assert cfg.model == "gpt-4o"
        assert cfg.api_key == "sk-abc123"
        assert cfg.azure_endpoint is None

    def test_valid_azure(self):
        cfg = LLMConfig(
            provider=LLMProvider.AZURE_OPENAI,
            model="gpt-4o",
            api_key="key123",
            azure_endpoint="https://my.openai.azure.com",
            azure_api_version="2024-02-01",
            azure_deployment="gpt4o-deploy",
        )
        assert cfg.provider == LLMProvider.AZURE_OPENAI
        assert cfg.azure_endpoint == "https://my.openai.azure.com"

    def test_azure_missing_endpoint_raises(self):
        with pytest.raises(ValueError, match="azure_endpoint"):
            LLMConfig(
                provider=LLMProvider.AZURE_OPENAI,
                model="gpt-4o",
                api_key="key123",
                azure_api_version="2024-02-01",
                azure_deployment="gpt4o-deploy",
            )

    def test_azure_missing_api_version_raises(self):
        with pytest.raises(ValueError, match="azure_api_version"):
            LLMConfig(
                provider=LLMProvider.AZURE_OPENAI,
                model="gpt-4o",
                api_key="key123",
                azure_endpoint="https://my.openai.azure.com",
                azure_deployment="gpt4o-deploy",
            )

    def test_azure_missing_deployment_raises(self):
        with pytest.raises(ValueError, match="azure_deployment"):
            LLMConfig(
                provider=LLMProvider.AZURE_OPENAI,
                model="gpt-4o",
                api_key="key123",
                azure_endpoint="https://my.openai.azure.com",
                azure_api_version="2024-02-01",
            )

    def test_non_azure_ignores_azure_fields(self):
        cfg = LLMConfig(provider=LLMProvider.ANTHROPIC, model="claude-sonnet-4-20250514", api_key="sk-ant-xxx")
        assert cfg.azure_endpoint is None
        assert cfg.azure_api_version is None
        assert cfg.azure_deployment is None


class TestMaskApiKey:
    def test_masks_middle(self):
        assert mask_api_key("sk-abcdefghijk") == "sk-a...ijk"

    def test_short_key_returns_stars(self):
        assert mask_api_key("1234567") == "***"
        assert mask_api_key("short") == "***"

    def test_empty_key_returns_stars(self):
        assert mask_api_key("") == "***"

    def test_exactly_eight_chars(self):
        # length 8 > 7, so should mask: first 4 + ... + last 3
        assert mask_api_key("12345678") == "1234...678"


class TestConfigPersistence:
    def test_save_and_load_round_trip(self, tmp_path, monkeypatch):
        fake_dir = tmp_path / ".stock-adviser"
        fake_file = fake_dir / "config.json"
        monkeypatch.setattr("stock_adviser.config.CONFIG_DIR", fake_dir)
        monkeypatch.setattr("stock_adviser.config.CONFIG_FILE", fake_file)

        original = LLMConfig(provider=LLMProvider.OPENAI, model="gpt-4o", api_key="sk-test-key-123456")
        save_config(original)
        loaded = load_config()
        assert loaded == original

    def test_load_missing_file_raises(self, tmp_path, monkeypatch):
        fake_file = tmp_path / ".stock-adviser" / "config.json"
        monkeypatch.setattr("stock_adviser.config.CONFIG_FILE", fake_file)

        with pytest.raises(ConfigNotFoundError):
            load_config()

    def test_save_creates_directory(self, tmp_path, monkeypatch):
        fake_dir = tmp_path / ".stock-adviser"
        fake_file = fake_dir / "config.json"
        monkeypatch.setattr("stock_adviser.config.CONFIG_DIR", fake_dir)
        monkeypatch.setattr("stock_adviser.config.CONFIG_FILE", fake_file)

        cfg = LLMConfig(provider=LLMProvider.GOOGLE, model="gemini-pro", api_key="AIza-key-12345678")
        save_config(cfg)
        assert fake_dir.is_dir()
        assert fake_file.exists()

    def test_save_sets_600_permissions(self, tmp_path, monkeypatch):
        fake_dir = tmp_path / ".stock-adviser"
        fake_file = fake_dir / "config.json"
        monkeypatch.setattr("stock_adviser.config.CONFIG_DIR", fake_dir)
        monkeypatch.setattr("stock_adviser.config.CONFIG_FILE", fake_file)

        cfg = LLMConfig(provider=LLMProvider.OPENAI, model="gpt-4o", api_key="sk-test-key-123456")
        save_config(cfg)

        file_stat = os.stat(fake_file)
        permissions = stat.S_IMODE(file_stat.st_mode)
        assert permissions == 0o600
