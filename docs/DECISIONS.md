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

### Architecture: Deterministic Engine + LLM Extraction Frontend
- **What:** Pure Python financial simulator for all math; LLM only for image OCR, message parsing, explanation writing
- **What:** Combinatorial solver generates ALL candidates, simulates each, ranks by exact 6-step tie-breaker
- **Why:** LLMs hallucinate numbers. Financial math must be reproducible. Previous winners proved "deterministic code decides, LLM describes"
- **Alternatives considered:** LLM-for-everything (risky), sequential waterfall (misses optimal plans), multi-agent (unnecessary complexity)
- **Tradeoffs:** More code to write vs. guaranteed mathematical accuracy on hidden test cases
- **Regression test:** Run against 25 sample requests, verify format + accuracy

### LLM: Groq qwen/qwen3.8-27b for Everything
- **What:** Single model for image OCR, message parsing, and explanation writing
- **Why:** Already have API key, free tier (30 RPM, 14,400 RPD), supports both text and images (inline base64)
- **Alternatives considered:** Gemini (needs separate API key), separate models for text vs vision
- **Tradeoffs:** Groq rate limits vs. zero setup overhead. qwen3.8-27b quality vs. GPT-4o/Gemini Pro
- **Regression test:** Test image extraction on all 16 images, verify amounts are numeric

### Data: Pandas for All Data Manipulation
- **What:** Pandas DataFrames for CSV loading, joining, currency conversion
- **Why:** Handles 25k events efficiently, native CSV support, easy joins
- **Alternatives considered:** Native Python CSV, SQLAlchemy, Polars
- **Tradeoffs:** Pandas memory usage vs. developer speed and readability
- **Regression test:** Verify row counts match expected (250 requests, 275 profiles, 25,342 events)

### Solver: Combinatorial Over Sequential Waterfall
- **What:** Generate ALL valid candidates (full, partial, installments, wait, spending changes), simulate each, sort survivors
- **Why:** Sequential waterfall tries plans in order and picks first safe one — misses optimal. Combinatorial guarantees finding the best
- **Alternatives considered:** Sequential waterfall (simpler but suboptimal), greedy heuristic
- **Tradeoffs:** More computation (but 250 requests × ~10 candidates each = ~2,500 simulations, trivial)
- **Regression test:** Compare combinatorial vs waterfall output on sample requests — combinatorial should find equal or better plans

### Tie-Breaker: Exact 6-Step Code Ranking
- **What:** Sort safe plans by exact tie-breaker hierarchy from §6.3 rules
- **Why:** Hidden test cases check exact compliance. Missing tie-breaker = losing points
- **Alternatives considered:** LLM-based ranking (non-deterministic), partial tie-breaker
- **Tradeoffs:** Strict compliance vs. flexibility for edge cases
- **Regression test:** Verify sorted order on sample requests with known optimal plans

---

## Build Session Decisions

*(Add decisions here as you build during the hackathon)*

---

## Regressions Caught

*(Log every regression — this is gold for the interview)*
