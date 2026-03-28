# agentic-stock-adviser

Conversational stock analysis agent built on LangGraph with OpenAI. Uses specialist sub-agents (fundamentals, technicals, sentiment, macro, insider) to dynamically research and synthesise investment analysis based on user questions.

## Python Environment

Always use `poetry run <command>`. Never use global Python or assume `.venv`.

## Key Paths

- Source: `src/stock_adviser/`
- Tests: `tests/`
- Tools: `src/stock_adviser/tools/`
- Docs: `docs/`
- CI: `.github/workflows/`

## Development Commands

```
make check      # lint + test + typecheck — run after every change
make lint       # pre-commit (ruff format + ruff lint + file checks)
make test       # unit tests
make typecheck  # mypy (non-blocking until codebase stabilises)
```

## Conventions

- Pre-commit runs: ruff format, ruff lint (unused imports, isort, bare excepts), trailing whitespace, JSON/TOML/YAML validation, secret detection
- Commit prefixes: `fix:` (bugs), `feat:` (features), `chore:` (other) — enforced by semantic-release
- LLM: OpenAI via `langchain-openai`. Config via `.env` (see `.env.example`)
- All agent tools use the `@tool` decorator from `langchain_core.tools`
- Tests: pytest with `asyncio_mode = "auto"`

## Tier 2 Docs

- Learning roadmap & architecture: `docs/00-ROADMAP.md`
- Pillar deep-dives: `docs/01-PILLAR-1-FOUNDATION.md` through `docs/08-PILLAR-8-PRODUCTION.md`
