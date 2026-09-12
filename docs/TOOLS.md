> **This file shows tool usage patterns from previous hackathons.** Use this to understand what deliberate building looks like, regardless of which tool you use.

# Tools — Usage Patterns

## Key Insight from Previous Hackathons

The leaderboard separated participants by **how they worked**, not which tool they picked. Behavior was the driver, tool was correlated.

### What Strong Users Did (Regardless of Tool)

| Behavior | Strong Pattern | Weak Pattern |
|---|---|---|
| **Planning** | "Let me read the problem first, then plan architecture" | "Build me an agent" |
| **Constraints** | "Use deterministic math, not LLM. The tie-breaker must be exact." | "Use the best approach" |
| **Architecture** | "Compare combinatorial solver vs sequential waterfall" | "Just build it" |
| **Testing** | "Run on sample_requests.csv, check request_007 specifically" | "Test it" |
| **Iteration** | "Amount is wrong — it's including spending changes. Fix to calculate BEFORE." | "Fix it" |
| **Pushback** | "No, don't use GPT-4 for the simulation. Use Python." | Accepting all suggestions |

---

## Tool Usage in Top 50 (Previous Hackathons)

| Tool | Overall | Top 50 | Top 10 |
|---|---|---|---|
| Claude Code | 14.4% | 44% | 7/10 |
| GitHub Copilot | 11.1% | 16% | 2/10 |
| Codex | 19.2% | 12% | 1/10 |
| Antigravity | 33.7% | 12% | 0/10 |

**Takeaway:** Top performers used Claude Code disproportionately. But the correlation was with **deliberate building behavior**, not the tool itself.

---

## Chat Transcript Quality Tiers

### Tier 1: Engineering Partner (Top 50)
- Read problem statement → inspect data → compare architectures → implement with constraints → test against samples → iterate on failures

### Tier 2: Directed Builder (Mid-tier)
- Sets some constraints, tests occasionally, iterates when prompted

### Tier 3: Passive Prompter (Lower-tier)
- "Build me an agent", no testing, no architecture comparison

### Tier 4: Output Paster (Lowest)
- Pasted raw output as transcript, not a development record

---

## Our Tool Setup

- **Tool:** OpenCode (opencode CLI)
- **LLM:** Groq qwen/qwen3.8-27b (free tier, 30 RPM, 14,400 RPD)
- **Language:** Python 3.11+
- **Data:** Pandas for CSV manipulation
- **Validation:** Pydantic for output schema
- **Logging:** `log.txt` in repo root (auto-appended every turn)

---

## Recommendation

Regardless of tool, follow the winner behavior pattern:
1. Plan before coding
2. Set explicit constraints
3. Test against sample data
4. Iterate based on failures
5. Own your decisions in the transcript
