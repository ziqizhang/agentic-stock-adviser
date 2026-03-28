# Pillar 5: Planning & Reasoning — Dynamic Research Strategies

> **Goal:** Agent creates research plans, adapts them, and reflects on completeness.
> **Patterns:** Planning (6), Reasoning (17), Reflection (4), Goal Setting (11)
> **Reference:** deep_research_from_scratch Notebook 5, Agentic Patterns Ch. 4, 6, 11, 17, Deep Agents PDF

---

## Concepts to Master

### 5.1 Why Planning Matters

From the Deep Agents PDF: **Planning is the #1 principle** all deep agent systems share.

Without planning, "What should I do with AAPL?" triggers a fixed pipeline.
With planning, the agent reasons: "The user wants an investment decision. AAPL recently had earnings. I should check: earnings results, market reaction, valuation vs peers, macro context. Let me start with earnings since that's the most timely factor."

### 5.2 Plan-Execute-Reflect Cycle

```
User Query
    │
    ▼
┌─────────┐
│  PLAN   │ → "I need fundamentals, recent earnings, and sector context"
└────┬────┘
     │
     ▼
┌─────────┐
│ EXECUTE │ → Dispatch to sub-agents, gather results
└────┬────┘
     │
     ▼
┌─────────┐
│ REFLECT │ → "I have fundamentals and earnings but sector data was incomplete.
│         │    The earnings were a big miss — I should also check insider activity
│         │    to see if insiders were selling before the miss."
└────┬────┘
     │
     ▼
  Sufficient? ──No──► REPLAN (add insider analysis)
     │
    Yes
     │
     ▼
  Synthesize & Respond
```

### 5.3 Structured Planning Output

```python
class ResearchPlan(BaseModel):
    """A plan for researching a stock analysis question."""
    user_intent: str           # What the user actually wants to know
    key_questions: list[str]   # Specific questions to answer
    required_analyses: list[str]  # Which specialist agents to invoke
    priority_order: list[str]  # What to research first
    reasoning: str             # Why this plan makes sense
```

### 5.4 Reflection (Producer-Critic Pattern)

After the analysis is complete but before presenting to the user:
- **Completeness check:** Did we address all the user's questions?
- **Consistency check:** Do the different analyses tell a coherent story?
- **Confidence check:** Where are we uncertain? Should we caveat?
- **Bias check:** Are we over-weighting one signal?

---

## Implementation Steps

### Step 1: Add a Planning Node
Before dispatching to sub-agents, the supervisor creates an explicit plan.

### Step 2: Make the Plan Adaptive
After receiving sub-agent results, check if the plan needs updating.

### Step 3: Add the Reflection Agent
A critic that reviews the synthesized output before it reaches the user.

### Step 4: Add Goal Tracking
Track which parts of the plan have been completed and which remain.

---

## Next Step

Proceed to **docs/06-PILLAR-6-SAFETY-GUARDRAILS.md** (Safety & Quality).
