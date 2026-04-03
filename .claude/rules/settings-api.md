# LLM Settings & Configuration

Applies when working in: `src/stock_adviser/config.py`, `src/stock_adviser/llm.py`, `src/stock_adviser/api/routes/settings.py`, `frontend/src/settings/`

## Config file

LLM configuration is stored at `~/.stock-adviser/config.json` (user home, not the repo).
File permissions are set to `0o600` (owner read/write only) on every save — never weaken this.

## Module dependency chain

```
config.py        — LLMProvider enum, LLMConfig Pydantic model, load_config(), save_config(), mask_api_key()
    ↓
llm.py           — get_llm() loads from disk; _build_llm(config, max_retries, temperature) builds provider instance
    ↓
api/routes/settings.py — REST API; validates connection before saving
```

`graph.py` calls `get_llm()` which reads from disk. `settings.py` calls `_build_llm()` directly (with `max_retries=3`) to test connectivity before committing to disk.

## Adding a new LLM provider

1. Add a new value to `LLMProvider` StrEnum in `config.py`
2. Add the `elif provider == LLMProvider.NEW:` branch in `llm.py::_build_llm()`
3. Use a lazy import (try/except ImportError with a clear install instruction) — the package is optional
4. Add an optional Poetry extra in `pyproject.toml` if needed
5. Update the provider dropdown in `frontend/src/settings/SettingsModal.tsx`
6. If the provider needs extra fields (like Azure's endpoint/deployment), add them to `LLMConfig` with a Pydantic validator that requires them only when the provider is selected

## PATCH semantics for api_key

`POST /settings` with an empty `api_key` reuses the existing key from the config file. This lets the frontend show a masked placeholder without forcing re-entry on every settings open. Do not change this behaviour — it is intentional.

## Connection validation

Before saving config, `settings.py::validate_llm_connection()` calls `llm.ainvoke([HumanMessage("hello")])` with `max_retries=3`. A 400 response means the key/endpoint is wrong. A 422 means the request body is invalid (e.g., Azure fields missing). Never save config without validating first.

## Frontend integration

- `frontend/src/settings/api.ts` — `getSettings()`, `saveSettings()`, `getSettingsStatus()`
- `frontend/src/settings/SettingsModal.tsx` — form UI; shows Azure-specific fields only when provider is `azure_openai`; uses masked placeholder for api_key
- Zustand store: `llmConfigured` (bool) and `settingsOpen` (bool) in `frontend/src/store/`
- On app load, `App.tsx` calls `getSettingsStatus()` and auto-opens the modal if `configured: false`
