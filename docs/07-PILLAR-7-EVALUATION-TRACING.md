# Pillar 7: Evaluation & Tracing — Measuring Quality

> **Goal:** Full LangSmith integration with tracing, evaluation datasets, automated testing.
> **Patterns:** Evaluation & Monitoring (19), Resource-Aware Optimization (16)
> **Reference:** lca-reliable-agents (all modules), Agentic Patterns Ch. 16, 19

---

## Key Areas

### 7.1 Tracing (LangSmith)
- Trace every LLM call, tool invocation, and agent decision
- Visualize the full execution graph for debugging
- Track latency, token usage, and cost per analysis
- Tag traces by user, stock, analysis type for filtering

### 7.2 Evaluation Methods (from lca-reliable-agents)

| Method | What It Checks | When to Use |
|--------|---------------|-------------|
| **Code-based eval** | Schema correctness, required fields present | Every run (CI) |
| **LLM-as-judge** | Analysis quality, reasoning coherence | Periodic regression |
| **Pairwise eval** | Is version B better than version A? | After prompt/model changes |
| **Human eval** | Does the recommendation make sense? | Spot-check sample |

### 7.3 Evaluation Datasets
Build datasets of stock analysis scenarios with expected characteristics:
- "Analyze AAPL after a strong earnings beat" → should be bullish
- "Analyze a company with declining revenue and high debt" → should be cautious
- "Ask about an invalid ticker" → should handle gracefully

### 7.4 Cost & Latency Monitoring
- Track cost per analysis (multiple LLM calls add up)
- Monitor latency across sub-agents
- Identify bottlenecks (which tool/agent is slowest?)
- Resource-aware model selection (use cheaper model for simpler queries)

---

## Next Step

Proceed to **docs/08-PILLAR-8-PRODUCTION.md** (Production Patterns).
