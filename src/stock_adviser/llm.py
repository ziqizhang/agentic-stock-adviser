"""Multi-provider LLM factory with lazy imports."""

from __future__ import annotations

from langchain_core.language_models import BaseChatModel

from stock_adviser.config import LLMProvider, load_config

# ---------------------------------------------------------------------------
# Lazy imports — provider packages are optional dependencies.
# ---------------------------------------------------------------------------

try:
    from langchain_openai import AzureChatOpenAI, ChatOpenAI
except ImportError:

    def ChatOpenAI(*args, **kwargs):  # type: ignore[misc]
        raise ImportError("langchain-openai package not installed. Run: pip install langchain-openai")

    def AzureChatOpenAI(*args, **kwargs):  # type: ignore[misc]
        raise ImportError("langchain-openai package not installed. Run: pip install langchain-openai")


try:
    from langchain_anthropic import ChatAnthropic
except ImportError:

    def ChatAnthropic(*args, **kwargs):  # type: ignore[misc]
        raise ImportError("langchain-anthropic package not installed. Run: pip install langchain-anthropic")


try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:

    def ChatGoogleGenerativeAI(*args, **kwargs):  # type: ignore[misc]
        raise ImportError("langchain-google-genai package not installed. Run: pip install langchain-google-genai")


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def _build_llm(
    config,
    max_retries: int = 0,
    temperature: float | None = None,
) -> BaseChatModel:
    """Build an LLM instance from an ``LLMConfig`` object.

    Args:
        config: An ``LLMConfig`` describing provider, model, and credentials.
        max_retries: Retry count forwarded to the provider SDK (0 = no retries).
        temperature: Sampling temperature. ``None`` means use the provider default.

    Returns:
        A ``BaseChatModel`` ready for ``.invoke()`` / ``.ainvoke()`` calls.

    Raises:
        ValueError: If ``config.provider`` is not a recognised ``LLMProvider``.
        ImportError: If the required provider package is not installed.
    """
    kwargs: dict = {}
    if temperature is not None:
        kwargs["temperature"] = temperature
    if max_retries > 0:
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
    """Load config from disk and return a ready-to-use LLM.

    This is the main entry point used by the agent graph. The return type
    is ``BaseChatModel`` so callers are provider-agnostic.
    """
    config = load_config()
    return _build_llm(config, temperature=temperature)
