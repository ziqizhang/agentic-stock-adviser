# Pillar 4: Memory — Conversations & Learning

> **Goal:** Persistent conversation threads, user profiles, and retrievable past analysis history.
> **Patterns:** Memory Management (8), Knowledge Retrieval/RAG (14)
> **Reference:** agent-memory_aware L2-L5, Agentic Patterns Ch. 8, 14

---

## Concepts to Master

### 4.1 Memory Types

| Type | Scope | Implementation | Example |
|------|-------|---------------|---------|
| **Short-term** | Within a conversation thread | LangGraph checkpointer (messages list) | "Earlier you asked about AAPL's P/E" |
| **Long-term (User)** | Across all sessions for a user | Vector store + user profile store | "You prefer growth stocks, risk tolerance: moderate" |
| **Long-term (Analysis)** | Past analyses | Structured store (SQL or vector) | "Last month AAPL was rated BUY at score 7.2" |
| **Semantic (RAG)** | External knowledge | Vector store with embeddings | "According to the Q3 earnings call..." |

### 4.2 LangGraph Memory Architecture

From the agent-memory_aware course and Agentic Patterns Ch. 8:

```
┌─────────────────────────────────────┐
│         Conversation Thread          │
│  (LangGraph Checkpointer)           │
│  - Message history                   │
│  - Tool call results                 │
│  - Within-session state              │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│         Memory Manager Agent         │
│  - Extract key facts from conversation│
│  - Store to long-term memory          │
│  - Retrieve relevant memories         │
│  - Consolidate & update              │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│         Long-Term Store              │
│  - User profiles & preferences       │
│  - Past analysis results             │
│  - Market knowledge base             │
└─────────────────────────────────────┘
```

### 4.3 Key Memory Operations (from agent-memory_aware L4)

1. **Extraction** — Pull key facts from conversation ("User holds 100 shares of AAPL")
2. **Consolidation** — Merge new info with existing memory, resolve conflicts
3. **Self-updating** — Memory evolves as new information arrives
4. **Retrieval** — Semantic search for relevant past context

### 4.4 What to Remember for a Stock Adviser

- **User profile:** Risk tolerance, investment horizon, portfolio holdings, preferred sectors
- **Analysis history:** Past recommendations, scores, key factors at time of analysis
- **Conversation patterns:** What kind of analysis the user typically asks for
- **Market context:** Key events that affected past analyses

---

## Implementation Steps

### Step 1: Add Checkpointer for Conversation Persistence
Use PostgresSaver or SQLiteSaver for thread-based persistence.

### Step 2: Build the User Profile Store
Store and retrieve user preferences across sessions.

### Step 3: Build Analysis History Store
Store past analyses in a queryable format (structured + embeddings for semantic search).

### Step 4: Build the Memory Manager
An agent (or tool) that decides what to extract and store from conversations.

### Step 5: Inject Relevant Memories into Agent Context
Before the supervisor plans, retrieve relevant memories and include them in the prompt.

---

## Key Learning Checkpoints

- [ ] How does the LangGraph checkpointer persist conversation state?
- [ ] How do you retrieve past conversations by thread_id?
- [ ] How do you build a semantic search over past analyses?
- [ ] How does the memory manager decide what's worth remembering?
- [ ] How do you inject retrieved memories into the agent's context without overwhelming it?

---

## Next Step

Proceed to **docs/05-PILLAR-5-PLANNING-REASONING.md** (Planning & Reasoning).
