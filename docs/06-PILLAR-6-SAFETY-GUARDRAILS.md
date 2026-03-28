# Pillar 6: Safety & Quality — Guardrails and Human-in-the-Loop

> **Goal:** Validate all outputs, add disclaimers, catch hallucinated numbers.
> **Patterns:** Guardrails (18), Human-in-the-Loop (13), Exception Handling (12)
> **Reference:** Agentic Patterns Ch. 12, 13, 18

---

## Key Areas

### 6.1 Output Guardrails
- Financial disclaimers on all recommendations ("This is not financial advice...")
- Validate numerical data (prices, P/E ratios) against source data
- Detect and flag hallucinated statistics
- Ensure balanced presentation (bull AND bear case)

### 6.2 Input Validation
- Validate ticker symbols before processing
- Detect and handle ambiguous queries
- Rate-limit requests to prevent abuse

### 6.3 Human-in-the-Loop
- LangGraph's `interrupt()` for pausing and asking user for clarification
- User confirmation before high-confidence BUY/SELL recommendations
- Allow user to guide the analysis ("Focus more on technicals")

### 6.4 Exception Handling
- Graceful degradation when data sources are unavailable
- Retry with backoff for transient failures
- Fallback to cached data when fresh data isn't available
- Clear error messages ("Unable to fetch insider data for this UK stock")

---

## Next Step

Proceed to **docs/07-PILLAR-7-EVALUATION-TRACING.md** (Evaluation & Tracing).
