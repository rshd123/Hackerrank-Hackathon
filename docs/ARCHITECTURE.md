> **This file shows you what architecture actually won and gives you a ready-to-implement blueprint.** It contains performance data from 1,349 submissions across architecture types, a full system diagram, and layer-by-layer design details. Use this to decide your agent architecture before coding.

# Architecture — Insights & Blueprint

## What Architecture Actually Won

From 1,349 submissions, here's how different architectures performed:

| Architecture | Best Rank | Avg Rank | Median Rank | Top 10 | Top 50 | Top 100 |
|---|---|---|---|---|---|---|
| **Single agent with tools or RAG** | **1** | 592 | 565 | **7** | **27** | **60** |
| Graph or state-machine workflow | 2 | 351 | 296 | 1 | 5 | 8 |
| Explicit multi-stage or multi-agent pipeline | 3 | 468 | 378 | 2 | 16 | 26 |
| Single prompt or single model agent | 77 | 872 | 942 | 0 | 0 | 2 |
| ML models / trained classifiers | 46 | 877 | 893 | 0 | 1 | 1 |
| Deterministic rule pipeline / no explicit agent | 17 | 933 | 1002 | 0 | 1 | 3 |

### Key Insight

The dominant winning pattern was a **single agent wrapped around retrieval, tools, schemas, and guardrails**. You don't need multi-agent complexity. You need a well-engineered single agent with strong tooling and guardrails.

Most participants didn't build fully autonomous multi-agent systems. The dominant pattern was a single agent with supporting infrastructure.

---

## Recommended Architecture Blueprint

```
┌─────────────────────────────────────────────────┐
│                  INCOMING TICKET                  │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│          DETERMINISTIC SECURITY GATE             │
│  • Prompt injection detection                    │
│  • Jailbreak pattern matching                    │
│  • Input sanitization                            │
│  • Fraud/unauthorized access detection           │
└──────────────────────┬──────────────────────────┘
                       │
              ┌────────┴────────┐
              │   BLOCK/ESCALATE │
              │   (if detected)  │
              └────────┬────────┘
                       │ safe input
                       ▼
┌─────────────────────────────────────────────────┐
│              CLASSIFICATION LAYER                │
│  • Platform identification (HR/Anthropic/Visa)   │
│  • Category classification                       │
│  • Intent detection                              │
│  • Urgency scoring                               │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│              RAG RETRIEVAL LAYER                 │
│  • BM25 keyword search (primary)                 │
│  • Semantic similarity (secondary)               │
│  • Reranker for precision                        │
│  • top_k tuning based on testing                 │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│           ROUTING DECISION ENGINE                │
│  • Reply if: grounded answer available +         │
│    low/medium urgency + no risk flags            │
│  • Escalate if: no grounded answer OR            │
│    high urgency OR risk detected OR              │
│    sensitive topic OR out of scope               │
│  • Deterministic gates override LLM for          │
│    fraud/unauthorized access                     │
└──────────────────────┬──────────────────────────┘
                       │
              ┌────────┴────────┐
              │                  │
              ▼                  ▼
┌──────────────────┐  ┌──────────────────┐
│   REPLY DIRECTLY  │  │     ESCALATE     │
│   with grounded   │  │  with justification│
│   context + JSON  │  │  + urgency level  │
└──────────────────┘  └──────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│              OUTPUT FORMATTER                    │
│  • Structured JSON/CSV per ticket                │
│  • Status: replied/escalated                     │
│  • Request type, product area                    │
│  • Justification (grounded in corpus)            │
│  • Response text (if replied)                    │
└─────────────────────────────────────────────────┘
```

---

## Layer Details

### 1. Deterministic Security Gate

**Purpose:** Catch adversarial inputs BEFORE they reach the LLM.

**Components:**
- **Prompt injection detection** — Pattern matching for common injection techniques
- **Jailbreak pattern matching** — Detect attempts to bypass safety instructions
- **Input sanitization** — Clean malformed input, normalize text
- **Fraud/unauthorized access detection** — Keyword and pattern matching for security-sensitive tickets

**Key rule:** The LLM CANNOT downgrade a high-risk ticket. Deterministic gates run first.

### 2. Classification Layer

**Purpose:** Route tickets to the right handling path.

**Components:**
- **Platform identification** — Which platform is this about? (HackerRank, Anthropic, Visa)
- **Category classification** — What type of request? (billing, technical, security, general)
- **Intent detection** — What does the user want? (information, action, escalation)
- **Urgency scoring** — How urgent is this? (low, medium, high, critical)

**Implementation:** Use structured JSON output from the LLM with schema validation.

### 3. RAG Retrieval Layer

**Purpose:** Find relevant information from the 774-document corpus.

**Components:**
- **BM25 keyword search (primary)** — Fast, effective for keyword-heavy corpus
- **Semantic similarity (secondary)** — Catches conceptual matches BM25 misses
- **Reranker** — Improves precision by re-ordering top results
- **top_k tuning** — Based on testing against sample tickets

**Key decision:** BM25 as primary because corpus is small and keyword-heavy. Semantic as secondary.

### 4. Routing Decision Engine

**Purpose:** Decide whether to reply or escalate.

**Reply criteria (ALL must be true):**
- Grounded answer available from RAG
- Low or medium urgency
- No risk flags from security gate

**Escalate criteria (ANY triggers escalation):**
- No grounded answer found
- High urgency level
- Risk detected by security gate
- Sensitive topic (fraud, unauthorized access)
- Out of scope for the agent

**Key rule:** Deterministic gates override LLM decisions for fraud and unauthorized access.

### 5. Output Formatter

**Purpose:** Produce structured, consistent output for each ticket.

**Required fields:**
- `status`: replied | escalated
- `request_type`: string
- `product_area`: string
- `justification`: string (grounded in corpus)
- `response`: string (if replied)
- `urgency`: low | medium | high | critical

---

## Why This Architecture Wins

1. **Single agent simplicity** — Matches the top-performing architecture pattern
2. **Deterministic guardrails** — Security gate catches adversarial inputs before LLM
3. **Grounded RAG** — BM25 + semantic + reranker for comprehensive retrieval
4. **Clear separation** — LLM handles classification and generation, deterministic code handles safety
5. **Testable** — Each layer can be tested independently against sample tickets
6. **Explainable** — Easy to explain in the interview: "The deterministic gate runs first..."
