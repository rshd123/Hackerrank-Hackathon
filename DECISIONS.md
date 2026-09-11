# DECISIONS.md — Architecture & Tradeoff Log

> **Purpose:** Record every architectural decision, tradeoff, and regression during the build. The AI judge interview (30% of score) rewards this heavily. Update this file as you build.

## Format

For each decision, log:

```
### [Decision Title]
- **What:** What you chose to do
- **Why:** Why you chose this approach
- **Alternatives considered:** What else you considered
- **Tradeoffs:** What you gained vs. what you lost
- **Regression test:** How you verified it didn't break anything
```

---

## Pre-Hackathon Decisions

### Architecture: Single Agent with Tools
- **What:** Single agent pipeline: Security Gate → Classifier → RAG → Router → Output
- **Why:** Data from 1,349 submissions shows single agent won (rank 1, 7/10 Top 10). Multi-agent complexity doesn't win.
- **Alternatives considered:** Multi-agent pipeline, graph-based workflow, single prompt
- **Tradeoffs:** Simpler to build and defend in interview vs. potentially less flexible for edge cases
- **Regression test:** Run `python main.py --test` after each change

### Security: Deterministic Gates Before LLM
- **What:** Regex-based injection/jailbreak/fraud detection runs BEFORE any LLM call
- **Why:** Mrinal D. (Rank #1): "Let the model describe. Let deterministic code decide." The LLM cannot override these decisions.
- **Alternatives considered:** LLM-based safety checks, post-processing safety
- **Tradeoffs:** More false positives (blocks legitimate content) vs. guaranteed safety against adversarial inputs
- **Regression test:** Test against known injection patterns

### RAG: BM25 Primary + Semantic Secondary
- **What:** BM25 keyword search as primary retrieval, semantic similarity as secondary
- **Why:** Blog data shows BM25 works well for small, keyword-heavy corpus (774 docs). Semantic adds recall for conceptual matches.
- **Alternatives considered:** Semantic-only, vector DB, hybrid search
- **Tradeoffs:** BM25 is fast and explainable vs. misses conceptual matches. Semantic catches those but adds latency.
- **Regression test:** Test retrieval quality on sample tickets

### Output: Structured CSV with Grounded Justifications
- **What:** Every ticket gets status, justification (grounded in corpus), urgency, response
- **Why:** Blog failure mode: "Agent returns correct action + reasonable response, but justification empty/generic → capped at ~70"
- **Alternatives considered:** Plain text output, JSON-only
- **Tradeoffs:** More structured code vs. guaranteed score floor on Output CSV
- **Regression test:** Validate all rows have non-empty, corpus-referenced justifications

---

## Build Session Decisions

*(Add decisions here as you build during the hackathon)*

---

## Regressions Caught

*(Log every regression — this is gold for the interview)*
