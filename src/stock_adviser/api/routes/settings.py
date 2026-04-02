"""Settings API: status, read, and write LLM configuration."""

from __future__ import annotations

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

router = APIRouter(prefix="/settings", tags=["settings"])


# ---------------------------------------------------------------------------
# Request model
# ---------------------------------------------------------------------------


class SettingsRequest(BaseModel):
    provider: LLMProvider
    model: str
    api_key: str = ""
    azure_endpoint: str | None = None
    azure_api_version: str | None = None
    azure_deployment: str | None = None


# ---------------------------------------------------------------------------
# Validation helper
# ---------------------------------------------------------------------------


async def validate_llm_connection(config: LLMConfig) -> None:
    """Build an LLM from *config* and send a test message to verify connectivity."""
    from stock_adviser.llm import _build_llm

    llm = _build_llm(config, max_retries=3)
    await llm.ainvoke([HumanMessage(content="hello")])


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/status")
async def settings_status():
    if not CONFIG_FILE.exists():
        return {"configured": False}
    try:
        load_config()
        return {"configured": True}
    except Exception:
        return {"configured": False}


@router.get("")
async def get_settings():
    try:
        config = load_config()
    except (ConfigNotFoundError, Exception):
        raise HTTPException(status_code=404, detail="Not configured")
    data = config.model_dump()
    data["api_key"] = mask_api_key(config.api_key)
    return data


@router.post("")
async def post_settings(req: SettingsRequest):
    api_key = req.api_key

    # If no key supplied, try to reuse existing
    if not api_key:
        try:
            existing = load_config()
            api_key = existing.api_key
        except Exception:
            raise HTTPException(status_code=422, detail="API key is required for first-time setup")

    # Build LLMConfig — Pydantic validation catches missing Azure fields
    try:
        config = LLMConfig(
            provider=req.provider,
            model=req.model,
            api_key=api_key,
            azure_endpoint=req.azure_endpoint,
            azure_api_version=req.azure_api_version,
            azure_deployment=req.azure_deployment,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # Validate connection
    try:
        await validate_llm_connection(config)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    save_config(config)
    return {"status": "ok"}
