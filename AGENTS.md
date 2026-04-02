# agentic-stock-adviser

Conversational stock analysis agent built on LangGraph. Supports multiple LLM providers (OpenAI, Azure OpenAI, Anthropic, Google Gemini) — configurable at runtime through the web UI. Uses specialist sub-agents (fundamentals, technicals, sentiment, macro, insider) to dynamically research and synthesise investment analysis based on user questions.

## Python Environment

Always use `poetry run <command>`. Never use global Python or assume `.venv`.

## Key Paths

- Source: `src/stock_adviser/`
- Tests: `tests/`
- Tools: `src/stock_adviser/tools/`
- Scripts: `scripts/` (e2e test scripts)
- Docs: `docs/`
- CI: `.github/workflows/`

## Module Map

- `graph.py` — ReAct agent graph (agent node, ToolNode, conditional routing)
- `config.py` — LLM provider config (enum, Pydantic model, load/save from `~/.stock-adviser/config.json`)
- `llm.py` — Multi-provider LLM factory (OpenAI, Azure OpenAI, Anthropic, Google Gemini)
- `models.py` — Pydantic models for all tool inputs/outputs
- `prompts.py` — System prompt constants
- `state.py` — AgentState (messages-only, compatible with future memory layers)
- `streaming.py` — Stream event classification (TokenEvent, ToolStartEvent, etc.). Reusable across REPL, FastAPI, WebSocket consumers.
- `__main__.py` — Terminal REPL consumer (renders stream events to stdout)
- `server.py` — FastAPI server entry point (`make serve`)
- `tools/` — yfinance tools, each with `@tool` decorator and `.metadata["status"]` for UI display
- `api/app.py` — FastAPI app factory (create_app), CORS, session store
- `api/session.py` — In-memory session store (conversation history per session_id)
- `api/routes/health.py` — GET /health
- `api/routes/chat.py` — POST /chat (accept message, trigger agent in background)
- `api/routes/stream.py` — GET /stream/{session_id} (SSE endpoint)
- `api/routes/settings.py` — GET/POST /settings (LLM provider config via UI)
- `events/types.py` — SSE event dataclasses (Token, ChartUpdate, TableUpdate, Error, etc.)
- `events/router.py` — Maps tool results to dashboard SSE events

## Development Commands

```
make check      # lint + test + typecheck — run after every change
make lint       # pre-commit (ruff format + ruff lint + file checks)
make test       # unit tests
make typecheck  # mypy (non-blocking until codebase stabilises)
make serve      # run FastAPI server (port 8881, auto-reload)
```

## Frontend

- Stack: React + TypeScript + Vite + Tailwind CSS
- Location: `frontend/`
- Dev server: `make frontend-dev` (port 5173, proxies API to backend)
- E2E tests: `cd frontend && npx playwright test`
- Key modules:
  - `store/` — Zustand store (chat messages, stock data, UI state)
  - `stream/useSSE.ts` — Single SSE connection, dispatches events to store
  - `stream/api.ts` — POST /chat helper
  - `settings/SettingsModal.tsx` — LLM provider config modal (provider, model, API key)
  - `settings/api.ts` — Settings API client
  - `chat/ChatPanel.tsx` — Collapsible right panel
  - `dashboard/Dashboard.tsx` — Stock tabs + empty state
  - `dashboard/StockTab.tsx` — Sub-tab routing (Chart/Fundamentals/Report)
  - `panes/` — ChartPane (recharts), FundamentalsPane (table), ReportPane (markdown)

## Conventions

- Pre-commit runs: ruff format, ruff lint (unused imports, isort, bare excepts), trailing whitespace, JSON/TOML/YAML validation, secret detection
- Commit prefixes: `fix:` (bugs), `feat:` (features), `chore:` (other) — enforced by semantic-release
- LLM: Multi-provider via `langchain-openai`, `langchain-anthropic` (optional), `langchain-google-genai` (optional). Config via web UI settings modal → saved to `~/.stock-adviser/config.json`
- All agent tools use the `@tool` decorator from `langchain_core.tools` with `.metadata["status"]` for human-readable UI messages
- Streaming: `streaming.py` yields typed events; consumers (REPL, API) handle rendering
- Tests: pytest with `asyncio_mode = "auto"`

## Tier 2 Docs

- Learning roadmap & architecture: `docs/00-ROADMAP.md`
- Pillar deep-dives: `docs/01-PILLAR-1-FOUNDATION.md` through `docs/08-PILLAR-8-PRODUCTION.md`
- Dashboard design spec: `docs/superpowers/specs/2026-03-29-dashboard-design.md`
- Multi-LLM provider spec: `docs/superpowers/specs/2026-04-02-multi-llm-provider-design.md`
