# Multi-LLM Provider Support

**Date**: 2026-04-02
**Status**: Approved

## Goal

Allow users to choose their LLM provider, model, and API key through the web UI. The system currently hardcodes Azure OpenAI. After this change, it supports OpenAI, Azure OpenAI, Anthropic, and Google Gemini — selectable at runtime without code changes or restarts.

## Config File

**Location**: `~/.stock-adviser/config.json`
**Permissions**: `600` (owner read/write only)

```json
{
  "provider": "openai",
  "model": "gpt-4o",
  "api_key": "sk-abc...xyz",
  "azure_endpoint": null,
  "azure_api_version": null,
  "azure_deployment": null
}
```

- `provider`: one of `"openai"`, `"azure_openai"`, `"anthropic"`, `"google"` (backed by `LLMProvider` StrEnum)
- `model`: free text, must match the provider's model name exactly (for Azure OpenAI this is the deployment name)
- `api_key`: the provider's API key, stored in plain text in the file (file permissions protect it)
- `azure_endpoint`, `azure_api_version`, `azure_deployment`: required only when provider is `azure_openai`, null otherwise

The file is created on first save. The directory `~/.stock-adviser/` is created if missing. The backend reads the file on each `get_llm()` call so changes take effect immediately.

## Provider Enum

```python
# src/stock_adviser/config.py
from enum import StrEnum

class LLMProvider(StrEnum):
    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
```

## Pydantic Config Model

```python
# src/stock_adviser/config.py
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
```

Functions: `load_config() -> LLMConfig` (reads file, raises `ConfigNotFoundError` if missing), `save_config(config: LLMConfig) -> None` (writes file with `chmod 600`).

## LLM Factory

```python
# src/stock_adviser/llm.py
def get_llm(temperature: float | None = None) -> BaseChatModel:
    config = load_config()

    if config.provider == LLMProvider.OPENAI:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(api_key=config.api_key, model=config.model, **_temp(temperature))

    elif config.provider == LLMProvider.AZURE_OPENAI:
        from langchain_openai import AzureChatOpenAI
        return AzureChatOpenAI(
            api_key=config.api_key,
            azure_endpoint=config.azure_endpoint,
            azure_deployment=config.azure_deployment,
            api_version=config.azure_api_version,
            **_temp(temperature),
        )

    elif config.provider == LLMProvider.ANTHROPIC:
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(api_key=config.api_key, model=config.model, **_temp(temperature))

    elif config.provider == LLMProvider.GOOGLE:
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(api_key=config.api_key, model=config.model, **_temp(temperature))

    raise ValueError(f"Unknown provider: {config.provider}")
```

- Return type is `BaseChatModel` — all providers implement `.bind_tools()` and `.ainvoke()`
- Lazy imports so missing provider packages don't crash the app
- `ImportError` caught and re-raised with a clear install instruction
- No changes to `graph.py`, `streaming.py`, tools, or event system

## Settings API

**New file**: `src/stock_adviser/api/routes/settings.py`

### `GET /settings/status`

Returns `{"configured": true/false}`. Checks if config file exists and is valid. Called on page load to decide whether to show the setup modal.

### `GET /settings`

Returns the current config with masked API key. Key masking: first 4 + `...` + last 3 characters. Returns 404 if not configured.

```json
{
  "provider": "openai",
  "model": "gpt-4o",
  "api_key": "sk-a...xyz",
  "azure_endpoint": null,
  "azure_api_version": null,
  "azure_deployment": null
}
```

### `POST /settings`

Accepts the full config. Validates via Pydantic model. Before writing to disk:

1. Instantiate the LLM from the provided config
2. Call `await llm.ainvoke([HumanMessage(content="hello")])` to verify credentials — the LLM is constructed with `max_retries=3` for automatic retry with backoff
3. If validation fails, return `400` with the error message
4. If it succeeds, write config file and return `200`

If `api_key` field is empty in the request, merge with the existing key from the file (allows updating other fields without re-entering the key).

### Route registration

Add the settings router to `create_app()` in `app.py`.

## Error SSE Event

New event type for surfacing LLM errors to the chat:

```python
@dataclass
class Error(SSEEvent):
    message: str
    event_type: str = "error"
```

Emitted by `_event_generator` when the agent raises an exception. The frontend renders it as a system message in the chat (e.g., "LLM authentication failed — check your API key in settings").

## Frontend — Settings Modal

### New files

- `frontend/src/settings/SettingsModal.tsx` — modal component
- `frontend/src/settings/api.ts` — `getStatus()`, `getSettings()`, `saveSettings(config)`

### Behaviour

1. `App.tsx` calls `getStatus()` on mount
2. If `configured: false`, render `<SettingsModal>` as a blocking overlay (backdrop blur, no dismiss)
3. Modal contents:
   - **Provider**: dropdown (`OpenAI`, `Azure OpenAI`, `Anthropic`, `Google Gemini`)
   - **Model**: free text input. Helper text: "Enter the exact model name from your provider". Label changes to "Deployment name" for Azure OpenAI.
   - **API Key**: `<input type="password">`. When editing existing config, shows masked value as placeholder, field is empty — user must re-enter to change. If left empty on save, existing key is kept.
   - **Azure fields** (shown only when Azure OpenAI selected): Endpoint URL, API Version, Deployment Name
   - **Save button**: shows spinner + "Validating..." during the POST
   - **Error display**: inline below the Save button
4. Gear icon in top-right corner reopens the modal anytime (pre-fills current values from `GET /settings`)

### Store changes

Add to Zustand store:
- `llmConfigured: boolean` — set on mount from `GET /settings/status`
- `settingsOpen: boolean` — controls modal visibility

### Styling

Dark theme, consistent with existing UI. Tailwind only, no new frontend dependencies beyond what's already installed.

## Dependencies

```toml
# pyproject.toml
[tool.poetry.dependencies]
langchain-openai = "^1.1"  # existing, covers OpenAI + Azure OpenAI

[tool.poetry.extras]
anthropic = ["langchain-anthropic"]
google = ["langchain-google-genai"]
all-providers = ["langchain-anthropic", "langchain-google-genai"]

# With version pins:
langchain-anthropic = {version = "^0.3", optional = true}
langchain-google-genai = {version = "^0.5", optional = true}
```

Install via `poetry install -E anthropic`, `poetry install -E google`, or `poetry install -E all-providers`.

## Files Changed

| File | Change |
|------|--------|
| `src/stock_adviser/llm.py` | Factory pattern, reads config, returns `BaseChatModel` |
| `src/stock_adviser/api/app.py` | Register settings router |
| `src/stock_adviser/events/types.py` | Add `Error` event type |
| `src/stock_adviser/api/routes/stream.py` | Emit `Error` event on LLM exceptions |
| `pyproject.toml` | Add optional provider dependencies |
| `.env.example` | Remove Azure-specific vars (config file replaces them) |
| `frontend/src/App.tsx` | Check config status on mount, render modal, add gear icon |
| `frontend/src/store/index.ts` | Add `llmConfigured`, `settingsOpen` state |
| `tests/test_llm.py` | Test factory with mocked config |
| `tests/test_settings_api.py` | Test settings endpoints |

## Files Created

| File | Purpose |
|------|---------|
| `src/stock_adviser/config.py` | `LLMProvider` enum, `LLMConfig` model, `load_config()`, `save_config()` |
| `src/stock_adviser/api/routes/settings.py` | Settings REST endpoints |
| `frontend/src/settings/SettingsModal.tsx` | Settings modal component |
| `frontend/src/settings/api.ts` | Settings API client |

## What Does NOT Change

- `graph.py` — still calls `get_llm().bind_tools(tools)`, interface unchanged
- `streaming.py` — processes `BaseChatModel` output, provider-agnostic
- `tools/` — all tools use `@tool` decorator from `langchain_core`, no provider coupling
- `events/router.py` — routes tool results, unrelated to LLM provider
- `session.py` — stores messages, unrelated to provider
- SSE architecture — unchanged
