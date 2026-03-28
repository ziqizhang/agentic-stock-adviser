# Pillar 3: Multi-Agent Architecture — Specialist Sub-Agents

> **Goal:** Build a supervisor that routes to specialist analyst sub-agents and aggregates results.
> **Patterns:** Multi-Agent Collaboration (7), Parallelization (3), Routing (2)
> **Reference:** deep_research_from_scratch Notebook 4, Agentic Patterns Ch. 2, 3, 7, Deep Agents PDF

---

## Concepts to Master

### 3.1 Why Multi-Agent?

From the Deep Agents PDF, the key insight: **sub-agents isolate context**.

A single agent with 20+ tools and a massive prompt degrades in quality. Instead:
- Each sub-agent has a **focused prompt** (its expertise) and **limited tools** (its domain)
- The supervisor decides **which** specialists to invoke and **how** to combine their output
- Sub-agents can run **in parallel** (fundamentals + technicals + sentiment simultaneously)
- If one fails, others still produce results (**graceful degradation**)

### 3.2 Collaboration Topologies

| Topology | Description | When to Use |
|----------|-------------|-------------|
| **Supervisor** | One coordinator delegates to workers | Your primary pattern — dynamic routing based on user query |
| **Sequential Handoff** | Agent A → Agent B → Agent C | When analysis has strict dependencies (e.g., get data → analyze → synthesize) |
| **Parallel Fan-out** | Supervisor sends to N agents simultaneously | When multiple independent analyses can run concurrently |
| **Debate/Consensus** | Agents argue opposing positions | Bull vs. bear case analysis |
| **Critic-Reviewer** | One agent produces, another critiques | Quality assurance on recommendations |

### 3.3 Your Specialist Agents

| Agent | Role | Tools | Prompt Focus |
|-------|------|-------|-------------|
| **Fundamental Analyst** | Value assessment | get_fundamentals, get_earnings, get_fair_value | P/E analysis, growth metrics, balance sheet health |
| **Technical Analyst** | Price action & momentum | get_technicals, get_price_chart | Chart patterns, RSI, MACD, support/resistance |
| **Sentiment Analyst** | Market mood | get_news, get_social_sentiment | News sentiment, social buzz, event impact |
| **Macro Analyst** | Big picture | get_macro_indicators, get_sector_perf | Interest rates, inflation, sector rotation |
| **Insider/Institutional** | Smart money signals | get_insider_trades, get_institutional_holdings | Insider buying patterns, institutional flow |
| **Synthesis Agent** | Final recommendation | (no tools — works from sub-agent outputs) | Cross-domain synthesis, risk assessment, recommendation |

### 3.4 The Supervisor Pattern in LangGraph

The supervisor is itself a LangGraph node that:
1. Reads the user's question
2. Decides which specialists are needed (routing)
3. Delegates to them (potentially in parallel via `Send()`)
4. Collects their results
5. Passes everything to the synthesis agent

```python
from langgraph.types import Command, Send

def supervisor(state):
    # LLM decides which analysts to invoke
    plan = llm.invoke(planning_prompt, state.messages)

    # Fan out to selected analysts in parallel
    return [
        Send("fundamental_analyst", {"query": plan.fundamental_query}),
        Send("technical_analyst", {"query": plan.technical_query}),
        Send("sentiment_analyst", {"query": plan.sentiment_query}),
    ]
```

---

## Implementation Steps

### Step 1: Build One Sub-Agent as a Subgraph
Take your fundamental analysis and make it a self-contained LangGraph subgraph.

### Step 2: Build the Supervisor
Create the routing/planning logic that decides which sub-agents to invoke.

### Step 3: Add Parallel Execution
Use LangGraph's `Send()` to run multiple sub-agents concurrently.

### Step 4: Add the Synthesis Agent
Build the agent that takes all sub-agent outputs and produces a final recommendation.

### Step 5: Handle Partial Failures
What happens when one sub-agent fails? The system should still produce a result from the successful ones.

---

## Key Learning Checkpoints

- [ ] Can you build a subgraph that works as a standalone agent?
- [ ] How does the supervisor decide which sub-agents to invoke?
- [ ] How does `Send()` enable parallel execution?
- [ ] How do you aggregate outputs from multiple sub-agents?
- [ ] How do you handle a sub-agent timeout or failure?

---

## Next Step

Proceed to **docs/04-PILLAR-4-MEMORY.md** (Memory).
