# ADR-006: Memory Storage Strategy

**Status:** Proposed  
**Date:** 2026-06-07  
**Context:** FreightHero Watchtower Agentic Memory Architecture  
**Decision:** ADR-006 through ADR-010 are documented in detail in [memory-architecture.md](memory-architecture.md)

---

## Context

The FreightHero Watchtower system needs to store different types of memory (STM, Episodic, Semantic, Procedural) with different requirements for persistence, retrieval, and scalability. STM requires fast access and bounded size; LTM requires persistence and semantic search.

## Decision

We adopt a layered storage strategy:

| Memory Type | Storage | Rationale |
|---|---|---|
| **STM** | LangGraph Checkpointer (PostgreSQL prod / SQLite dev) | Native graph state persistence; thread_id per load for isolation; automatic recovery |
| **LTM (Semantic)** | PostgreSQL + PGVector | Structured storage + semantic search via embeddings; no additional service dependency |
| **LTM (Episodic)** | PostgreSQL + PGVector | Structured event data + semantic search on summaries |
| **LTM (Procedural)** | PostgreSQL | Workflow patterns with tool sequence similarity search |

## Alternatives Considered

| Alternative | Pros | Cons | Verdict |
|---|---|---|---|
| Redis for STM | Very fast; native TTL | Poor persistence across restarts; memory cost | ❌ |
| MongoDB for LTM | Flexible; good for documents | Limited semantic search; overhead | ❌ |
| Pinecone for embeddings | Managed; fast | Cost; external dependency; cold start | ❌ |
| Chroma in production | Lightweight; easy dev setup | Not production-ready; limited scale | ❌ (dev only) |
| FAISS | Fast; local | No native persistence; no metadata filtering | ❌ |

## Consequences

- **Positive:** Simplified stack (PostgreSQL for everything); PGVector enables semantic search without additional service; LangGraph Checkpointer integrates natively
- **Negative:** PostgreSQL may not scale as well as specialized vector databases for very large embedding collections; PGVector index management required
- **Risk:** Embedding generation latency for real-time memory operations

---

# ADR-007: Memory Retrieval Strategy

**Status:** Proposed  
**Date:** 2026-06-07

## Context

The agent needs to retrieve relevant memories efficiently, combining exact match (customer rules) with semantic search (learned facts, episodes). Retrieval must be agent-driven, not hardcoded pipelines.

## Decision

Hybrid layered retrieval strategy:

1. **Exact Match**: Customer rules and driver preferences — direct lookup by `scope` + `scope_id`
2. **Semantic Search**: Learned facts and episodes — embedding similarity search with scope filtering
3. **Recent-First**: Working context — most recent events first, with semantic fallback
4. **Agent-Driven**: Agent decides when and what to retrieve via `MemoryRetrieve` tool

## Alternatives Considered

| Alternative | Pros | Cons | Verdict |
|---|---|---|---|
| Exact match only | Simple; fast | Can't find learned facts by similarity | ❌ Insufficient |
| Semantic search only | Flexible | Slow for exact rules; may return irrelevant results | ❌ Insufficient |
| Hardcoded pipeline | Deterministic | Doesn't scale; not agent-driven | ❌ Violates requirement |
| Hybrid layered | Best of both worlds; agent-driven | Implementation complexity | ✅ Selected |

## Consequences

- **Positive:** Precise retrieval for customer rules; flexible retrieval for learned facts; agent decides what to retrieve
- **Negative:** Implementation complexity of hybrid search; embedding generation cost for semantic search
- **Risk:** Retrieval latency if both exact and semantic searches are needed in sequence

---

# ADR-008: Memory Summarization Strategy

**Status:** Proposed  
**Date:** 2026-06-07

## Context

STM has bounded size and must be compressed when it exceeds token limits. Long episodes must be summarized before storing in LTM. Summarization must preserve key information (state changes, agent decisions, important facts).

## Decision

Three summarization strategies:

| Strategy | Use Case | Method |
|---|---|---|
| **Compress Older** (`compress_older`) | STM overflow | Compress older events into summary, preserve N most recent intact |
| **Episode Compression** (`episode_compression`) | Long episodes | Compress N events into structured summary (trigger, actions, outcome) |
| **Relevance Filter** (`relevance_filter`) | Pre-workflow transition | Remove low-relevance items, keep items above threshold |

**Implementation:** LLM-based summarization with specific prompts for each strategy. Mandatory preservation of: state changes, tool calls, agent decisions, customer facts. Token reduction metrics recorded for observability.

## Alternatives Considered

| Alternative | Pros | Cons | Verdict |
|---|---|---|---|
| Sliding window | Simple | Loses important information | ❌ Too simple |
| LLM summarization | Preserves key info | Token cost; latency | ✅ Selected |
| Extractive summarization | No LLM cost | Less coherent | ❌ Less effective |
| Hybrid (extractive + LLM) | Balanced | Complexity | ⚠️ Future consideration |

## Consequences

- **Positive:** Preserves key information during summarization; reduces context token consumption; metrics for observability
- **Negative:** Additional token cost for summarization LLM; additional latency
- **Risk:** Summarization may lose nuanced context; needs eval testing

---

# ADR-009: Memory Retention Policy

**Status:** Proposed  
**Date:** 2026-06-07

## Context

Memories need different retention periods based on type and scope. Load memories can expire after delivery; customer memories are permanent; driver memories can expire by inactivity.

## Decision

| Memory Type | Scope | Retention | Eviction |
|---|---|---|---|
| STM | load + session | Until session end or summarization | LRU + summarization when over limit |
| Episodic | load | 30 days after pod_collected, then archive | Automatic archival |
| Episodic | driver | 90 days | Remove unaccessed episodes |
| Semantic | customer | Permanent | Update when confidence is superseded |
| Semantic | driver | 180 days without access | Remove by inactivity |
| Semantic | global | Permanent | Update when confidence is superseded |
| Procedural | customer | Permanent | Update based on success_rate |
| Procedural | global | Permanent | Update based on success_rate |

## Consequences

- **Positive:** Customer memories are permanent (rules don't expire); load memories are cleaned after completion; driver memories expire by inactivity
- **Negative:** Need maintenance job for cleanup; need to monitor LTM growth
- **Risk:** Aggressive retention policies may remove useful memories; conservative policies may cause unbounded growth

---

# ADR-010: LangChain Memory Selection

**Status:** Proposed  
**Date:** 2026-06-07

## Context

The LangChain ecosystem offers several memory primitives. We need to select which to use and document why each was chosen.

## Decision

| Primitive | Usage | Justification |
|---|---|---|
| **LangGraph Memory (Checkpointer)** | STM and session state | Native graph state persistence; guaranteed recovery; sub-graph support for workflow transitions; thread_id per load for isolation |
| **LangMem** | LTM (Semantic and Episodic) | Explicit long-term memory management; native semantic search; rich metadata; automatic compression; LangGraph integration via tools |
| **PGVector** | Embeddings for semantic search | Already using PostgreSQL; no additional dependency; production-ready; metadata filtering |
| **Conversation Summary Memory** | STM compression only | Useful for compressing long conversations; not primary memory; only a compression component |

## Alternatives Considered and Rejected

| Alternative | Reason for Rejection |
|---|---|
| Redis as STM | Poor persistence across restarts; memory cost; no native LangGraph integration |
| Chroma in production | Not production-ready; limited scalability |
| Pinecone | Cost; external dependency; cold start latency |
| FAISS | No native persistence; no metadata filtering |
| Prompt-only memory | Doesn't scale; doesn't persist across events; not agent-driven |
| Vector store as only memory | No efficient exact search; doesn't model memory types |

## Consequences

- **Positive:** Simplified stack (PostgreSQL + LangGraph + LangMem); native integration between components; observability via tool call records
- **Negative:** LangGraph learning curve; LangChain ecosystem dependency; PGVector may need tuning at scale
- **Risk:** LangChain ecosystem changes may require migration; PGVector performance at very large scale