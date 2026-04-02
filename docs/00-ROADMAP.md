# Agentic Stock Adviser — Learning Roadmap

> A structured guide to building a deep agentic stock analysis system,
> organized as a learning journey through agentic design patterns.

## Your Starting Point

You have **advanced LangGraph experience** from ai-genai-cam: parallel execution, reflection loops,
conditional routing, NodeABC patterns, custom reducers, TypedDict state, OpenAI via APIM,
LangFuse observability, PostgreSQL/Neo4j backends, architecture enforcement tests.

**What you already know well:**
- LangGraph StateGraph, nodes, edges, conditional routing
- Parallel execution patterns
- Reflection/refill loops (ideagen, groundgen, autowizard)
- Structured output with Pydantic models
- OpenAI integration (dual-tier models, APIM)
- Async-first node patterns with error handling
- Module boundary architecture

**The paradigm shift you're learning:**
All your existing graphs have a **compile-time-known shape**. The new challenge is building
an agent where the **graph shape is determined at runtime** by the user's questions:

| ai-genai-cam (what you know) | Agentic Stock Adviser (what's new) |
|------------------------------|-------------------------------------|
| Fixed pipeline: fetch → plan → generate → review → edit | Dynamic: user asks anything, agent plans its own approach |
| Inputs are structured DB records | Inputs are freeform natural language |
| Graph compiled once, runs the same way | Agent decides which sub-agents/tools to invoke per turn |
| No conversational memory across runs | Multi-turn conversation with persistent memory |
| LLM generates content within a node | LLM **controls the flow** — decides what to do next |
| Tools are implicit (DB queries, web fetch) | Tools are **explicit** — LLM chooses and calls them via function calling |

---

## The Big Picture

You're rebuilding your stock-selector as a **conversational, multi-agent system** that can dynamically plan, research, and synthesize stock analysis. Unlike the original (fixed 7-signal pipeline → score), this system will:

- **Converse** with the user to understand what they actually want to know
- **Plan** a research strategy based on the question
- **Delegate** to specialist sub-agents (fundamentals, technicals, macro, sentiment, etc.)
- **Orchestrate** tool calls (APIs, scrapers, MCP servers) through those agents
- **Remember** user preferences, past analyses, and conversation history
- **Reflect** on its own analysis quality before presenting results
- **Evaluate** itself through tracing and systematic evaluation

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      User Interface                         │
│              (CLI / Chat UI / API endpoint)                  │
└─────────────┬───────────────────────────────┬───────────────┘
              │                               │
              ▼                               ▼
┌─────────────────────────┐     ┌─────────────────────────────┐
│    Supervisor Agent      │     │     Long-Term Memory        │
│  (Router + Planner +     │◄───►│  (User prefs, past sessions │
│   Orchestrator)          │     │   conversation history)     │
└──────┬──────┬──────┬─────┘     └─────────────────────────────┘
       │      │      │
       ▼      ▼      ▼
┌──────────┐┌──────────┐┌──────────┐┌──────────┐┌──────────┐
│Fundamental││Technical ││Sentiment ││  Macro   ││ Insider  │
│  Analyst  ││ Analyst  ││ Analyst  ││ Analyst  ││ Analyst  │
│           ││          ││          ││          ││          │
│ Tools:    ││ Tools:   ││ Tools:   ││ Tools:   ││ Tools:   │
│ yfinance  ││ yfinance ││ news API ││ FRED API ││ SEC/     │
│ financials││ OHLCV    ││ social   ││ macro    ││ OpenInsid│
└──────────┘└──────────┘└──────────┘└──────────┘└──────────┘
       │      │      │      │      │
       ▼      ▼      ▼      ▼      ▼
┌─────────────────────────────────────────────────────────────┐
│              Synthesis / Reflection Agent                     │
│        (Aggregates, cross-checks, produces final output)     │
└─────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│         Evaluation & Tracing (LangSmith / LangFuse)          │
└─────────────────────────────────────────────────────────────┘
```

---

## The 8 Pillars (Your "Thesis Chapters")

Each pillar is a major area of learning and implementation. They build on each other
but can be studied somewhat independently. We'll go deep on each one.

### Pillar 1: The Paradigm Shift — From Predefined Graphs to ReAct Agent Loops
**What you'll learn:** The ReAct agent loop where the LLM controls flow via tool calling. This is fundamentally different from your compile-time-fixed graphs in ai-genai-cam.
**Why it matters:** This is the core mechanic of all "deep agents" — the LLM decides what to do, not the developer.
**Patterns involved:** Tool Use (5), Planning (6)
**Deliverable:** A single conversational agent that uses tools to answer stock questions, with the LLM autonomously deciding which tools to call.

### Pillar 2: Tools & MCP — Connecting to the Real World
**What you'll learn:** LangChain `@tool` decorator pattern, MCP server architecture, wrapping your existing scrapers as agent-callable tools.
**Why it matters:** In ai-genai-cam, data access is implicit (DB queries inside nodes). Here, tools are explicit — the LLM chooses and calls them. Tool design directly affects agent quality.
**Patterns involved:** Tool Use (5), MCP (10)
**Deliverable:** A library of stock analysis tools exposed as both native tools and MCP servers.

### Pillar 3: Multi-Agent Architecture — Specialist Sub-Agents
**What you'll learn:** The supervisor pattern where a coordinator LLM dynamically dispatches to specialist sub-agents. Unlike your ACC orchestrator (fixed sequence), the supervisor decides at runtime.
**Why it matters:** A single agent with 30 tools degrades. Specialists with focused prompts and limited tools perform better.
**Patterns involved:** Multi-Agent Collaboration (7), Parallelization (3), Routing (2)
**Deliverable:** A supervisor agent that dynamically routes user requests to specialist sub-agents.

### Pillar 4: Memory — Conversations & Learning
**What you'll learn:** LangGraph checkpointer for multi-turn conversations (new for you — ai-genai-cam runs are stateless across invocations), long-term memory for user profiles and past analyses.
**Why it matters:** The agent must remember what was discussed earlier in the conversation and across sessions.
**Patterns involved:** Memory Management (8), Knowledge Retrieval/RAG (14)
**Deliverable:** Persistent conversation threads, user profile memory, retrievable analysis history.

### Pillar 5: Planning & Reasoning — Dynamic Research Strategies
**What you'll learn:** The agent creating its own research plan at runtime (vs. your fixed planner nodes). Plan-Execute-Reflect cycles where the agent adapts its approach based on what it discovers.
**Why it matters:** "What should I do with AAPL?" requires a different research plan than "What's driving the NVDA dip?"
**Patterns involved:** Planning (6), Reasoning (17), Reflection (4), Goal Setting (11)
**Deliverable:** An agent that creates, executes, and adapts research plans dynamically.

### Pillar 6: Safety & Quality — Guardrails and Human-in-the-Loop
**What you'll learn:** Output guardrails for financial context, LangGraph `interrupt()` for human-in-the-loop (new — ai-genai-cam doesn't pause for user input mid-graph).
**Why it matters:** Financial domain requires disclaimers, validated numbers, and user control.
**Patterns involved:** Guardrails (18), Human-in-the-Loop (13), Exception Handling (12)
**Deliverable:** Guardrail layer with disclaimers, validation, and human review support.

### Pillar 7: Evaluation & Tracing — Measuring Quality
**What you'll learn:** LangSmith tracing and evaluation (complementing your LangFuse experience). LLM-as-judge evaluation, pairwise comparison, evaluation datasets.
**Why it matters:** Systematic measurement of agent quality. You know observability from LangFuse — this adds structured evaluation.
**Patterns involved:** Evaluation & Monitoring (19), Resource-Aware Optimization (16)
**Deliverable:** LangSmith integration with evaluation datasets and automated quality regression.

### Pillar 8: Production Patterns — Putting It All Together
**What you'll learn:** Chat UI, session management, deployment. Much of the production hardening you already know from ai-genai-cam.
**Patterns involved:** Exception Handling (12), Resource-Aware Optimization (16), Prioritization (20)
**Deliverable:** A deployable chat application with full operational support.

---

## Recommended Learning Path

```
Phase 1: "The Shift" (Pillars 1-2)
  Build a single ReAct agent with tools. Experience the paradigm shift
  from fixed graphs to LLM-controlled flow.
  You'll move fast here — LangGraph mechanics are familiar.

Phase 2: "Going Deep" (Pillars 3-5)
  Add multi-agent architecture, memory, and dynamic planning.
  This is where the deep agent patterns diverge most from your existing work.
  The bulk of new learning happens here.

Phase 3: "Production Grade" (Pillars 6-8)
  Add guardrails, evaluation, and production patterns.
  Leverages your existing production experience from ai-genai-cam.
```

---

## Technology Decisions

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **Orchestration** | LangGraph | You already know it deeply. Cyclical stateful graphs, native multi-agent support. |
| **LLM** | Multi-provider (OpenAI, Azure OpenAI, Anthropic, Google Gemini) via langchain-openai / langchain-anthropic / langchain-google-genai | Runtime-configurable through web UI. Provider packages are optional extras (`poetry install -E all-providers`). |
| **Tracing/Eval** | LangSmith (+ optional LangFuse) | LangSmith for evaluation datasets/experiments. LangFuse as optional secondary for cost tracking (you already know it). |
| **Data layer** | yfinance + custom tools | Proven in stock-selector, no API keys needed to start. |
| **Memory store** | LangGraph checkpointer (PostgreSQL or SQLite) + vector store | Native conversation persistence + semantic retrieval for long-term memory. |
| **MCP** | langchain-mcp-adapters | Standardized tool interface, from your deep_research course. |
| **Testing** | pytest + LangSmith evaluations | Unit tests for tools, LangSmith for agent-level evaluation. LLM caching pattern from ai-genai-cam. |
| **Package mgmt** | Poetry | Consistent with your existing workflow. |
| **UI** | Start CLI, graduate to chat UI | Focus on agent logic first, UI second. |

---

## What We're NOT Doing (Scope Boundaries)

- **Not building a trading bot** — This is analysis and recommendation, not execution
- **Not replacing Bloomberg Terminal** — We use free data sources, not institutional feeds
- **Not guaranteed returns** — All outputs include appropriate disclaimers
- **Not real-time streaming** — Near-real-time is fine; we're not doing HFT
- **Not mobile app** — CLI and web interface are sufficient for learning

---

## Cross-Reference: Your Learning Resources → Pillars

| Resource | Relevant Pillars |
|----------|-----------------|
| deep_research_from_scratch (LangGraph + MCP) | 1, 2, 3, 5 |
| agent-memory_aware (memory notebooks) | 4 |
| lca-reliable-agents (LangSmith tracing/eval) | 7 |
| Deep_Agents.pdf (4 principles) | 1, 3, 5 (planning, sub-agents, context offload) |
| Agentic Design Patterns book (21 patterns) | All pillars |
| **ai-genai-cam (your own project)** | Patterns to port: NodeABC, error handling, caching, architecture tests |

---

## Cross-Reference: Agentic Design Patterns → Pillars

| Pattern | Pillar(s) | How It Applies |
|---------|-----------|----------------|
| 1. Prompt Chaining | 1 | Sequential analysis steps |
| 2. Routing | 3 | Route user query to right specialist |
| 3. Parallelization | 3 | Run multiple analysts concurrently |
| 4. Reflection | 5 | Agent self-checks analysis quality |
| 5. Tool Use | 1, 2 | All data access via tools |
| 6. Planning | 5 | Dynamic research plan generation |
| 7. Multi-Agent | 3 | Specialist analyst sub-agents |
| 8. Memory | 4 | Conversation + long-term memory |
| 9. Learning & Adaptation | 4, 7 | Improve from past sessions |
| 10. MCP | 2 | Standardized tool interfaces |
| 11. Goal Setting | 5 | Research goal tracking |
| 12. Exception Handling | 6, 8 | Graceful degradation when data unavailable |
| 13. HITL | 6 | User confirmation of recommendations |
| 14. RAG | 4 | Retrieve past analyses, company knowledge |
| 15. A2A | Future | Cross-system agent communication |
| 16. Resource-Aware | 7, 8 | Model selection, cost management |
| 17. Reasoning | 5 | CoT for complex analysis |
| 18. Guardrails | 6 | Financial disclaimer, output validation |
| 19. Evaluation | 7 | LangSmith metrics and monitoring |
| 20. Prioritization | 5, 8 | Research task ordering |
| 21. Exploration | Future | Proactive market opportunity discovery |

---

## Next Step

Read **docs/01-PILLAR-1-FOUNDATION.md** to begin with the paradigm shift from predefined graphs to ReAct agent loops.
