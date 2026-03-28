import os

from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI


def get_llm(model: str | None = None, temperature: float | None = None) -> AzureChatOpenAI:
    """Create an LLM instance.

    Args:
        model: Deployment name (e.g. 'gpt-4o', 'gpt-4o-mini').
        temperature: Sampling temperature. 0 for deterministic output.
    """
    load_dotenv()
    deployment = model or os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
    kwargs: dict = {
        "azure_deployment": deployment,
        "api_version": os.environ["AZURE_OPENAI_API_VERSION"],
    }
    if temperature is not None:
        kwargs["temperature"] = temperature
    return AzureChatOpenAI(**kwargs)
