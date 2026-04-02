"""Tests for multi-provider LLM factory."""

from unittest.mock import MagicMock, patch

import pytest

from stock_adviser.config import LLMConfig, LLMProvider


def _openai_config(**overrides):
    defaults = dict(provider=LLMProvider.OPENAI, model="gpt-4o", api_key="sk-test123")
    return LLMConfig(**{**defaults, **overrides})


def _azure_config(**overrides):
    defaults = dict(
        provider=LLMProvider.AZURE_OPENAI,
        model="gpt-4o",
        api_key="az-key-123",
        azure_endpoint="https://my.openai.azure.com",
        azure_api_version="2024-02-01",
        azure_deployment="gpt4o-deploy",
    )
    return LLMConfig(**{**defaults, **overrides})


def _anthropic_config(**overrides):
    defaults = dict(provider=LLMProvider.ANTHROPIC, model="claude-sonnet-4-20250514", api_key="sk-ant-xxx")
    return LLMConfig(**{**defaults, **overrides})


def _google_config(**overrides):
    defaults = dict(provider=LLMProvider.GOOGLE, model="gemini-pro", api_key="AIza-key")
    return LLMConfig(**{**defaults, **overrides})


class TestOpenAIProvider:
    @patch("stock_adviser.llm.ChatOpenAI")
    @patch("stock_adviser.llm.load_config")
    def test_openai_provider(self, mock_load, mock_cls):
        mock_load.return_value = _openai_config()
        mock_cls.return_value = MagicMock()

        from stock_adviser.llm import get_llm

        result = get_llm()

        mock_cls.assert_called_once_with(api_key="sk-test123", model="gpt-4o")
        assert result is mock_cls.return_value


class TestAzureProvider:
    @patch("stock_adviser.llm.AzureChatOpenAI")
    @patch("stock_adviser.llm.load_config")
    def test_azure_provider(self, mock_load, mock_cls):
        mock_load.return_value = _azure_config()
        mock_cls.return_value = MagicMock()

        from stock_adviser.llm import get_llm

        result = get_llm()

        mock_cls.assert_called_once_with(
            api_key="az-key-123",
            azure_endpoint="https://my.openai.azure.com",
            azure_deployment="gpt4o-deploy",
            api_version="2024-02-01",
        )
        assert result is mock_cls.return_value


class TestAnthropicProvider:
    @patch("stock_adviser.llm.ChatAnthropic")
    @patch("stock_adviser.llm.load_config")
    def test_anthropic_provider(self, mock_load, mock_cls):
        mock_load.return_value = _anthropic_config()
        mock_cls.return_value = MagicMock()

        from stock_adviser.llm import get_llm

        result = get_llm()

        mock_cls.assert_called_once_with(api_key="sk-ant-xxx", model="claude-sonnet-4-20250514")
        assert result is mock_cls.return_value


class TestGoogleProvider:
    @patch("stock_adviser.llm.ChatGoogleGenerativeAI")
    @patch("stock_adviser.llm.load_config")
    def test_google_provider(self, mock_load, mock_cls):
        mock_load.return_value = _google_config()
        mock_cls.return_value = MagicMock()

        from stock_adviser.llm import get_llm

        result = get_llm()

        mock_cls.assert_called_once_with(api_key="AIza-key", model="gemini-pro")
        assert result is mock_cls.return_value


class TestTemperature:
    @patch("stock_adviser.llm.ChatOpenAI")
    @patch("stock_adviser.llm.load_config")
    def test_temperature_passed(self, mock_load, mock_cls):
        mock_load.return_value = _openai_config()
        mock_cls.return_value = MagicMock()

        from stock_adviser.llm import get_llm

        get_llm(temperature=0.7)

        mock_cls.assert_called_once_with(api_key="sk-test123", model="gpt-4o", temperature=0.7)

    @patch("stock_adviser.llm.ChatOpenAI")
    @patch("stock_adviser.llm.load_config")
    def test_temperature_none_not_passed(self, mock_load, mock_cls):
        mock_load.return_value = _openai_config()
        mock_cls.return_value = MagicMock()

        from stock_adviser.llm import get_llm

        get_llm(temperature=None)

        mock_cls.assert_called_once_with(api_key="sk-test123", model="gpt-4o")


class TestMaxRetries:
    @patch("stock_adviser.llm.ChatOpenAI")
    def test_max_retries_passed(self, mock_cls):
        from stock_adviser.llm import _build_llm

        mock_cls.return_value = MagicMock()
        config = _openai_config()

        _build_llm(config, max_retries=3)

        mock_cls.assert_called_once_with(api_key="sk-test123", model="gpt-4o", max_retries=3)

    @patch("stock_adviser.llm.ChatOpenAI")
    def test_max_retries_zero_not_passed(self, mock_cls):
        from stock_adviser.llm import _build_llm

        mock_cls.return_value = MagicMock()
        config = _openai_config()

        _build_llm(config, max_retries=0)

        mock_cls.assert_called_once_with(api_key="sk-test123", model="gpt-4o")


class TestUnknownProvider:
    def test_unknown_provider_raises(self):
        from stock_adviser.llm import _build_llm

        # Construct a config then monkey-patch the provider to something invalid
        config = _openai_config()
        config.provider = "unknown_provider"

        with pytest.raises(ValueError, match="Unknown provider"):
            _build_llm(config)


class TestMissingPackage:
    def test_missing_package_raises_readable_error(self):
        """Simulate missing langchain-anthropic by replacing the class with a raiser."""
        import stock_adviser.llm as llm_module

        original = getattr(llm_module, "ChatAnthropic")

        def _raiser(*args, **kwargs):
            raise ImportError("langchain-anthropic package not installed. Run: pip install langchain-anthropic")

        try:
            llm_module.ChatAnthropic = _raiser
            config = _anthropic_config()

            with pytest.raises(ImportError, match="langchain-anthropic"):
                llm_module._build_llm(config)
        finally:
            llm_module.ChatAnthropic = original
