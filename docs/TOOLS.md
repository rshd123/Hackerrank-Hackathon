> **This file shows you which tools top performers used and how they used them.** It contains tool usage stats from 1,349 submissions, breakdowns by rank tier, winner behavior patterns, and chat transcript quality tiers. Use this to choose your AI coding tool and understand what deliberate building looks like.

# Tools — Usage Stats & Behavior Patterns

## Tool Usage Across All Submissions

From 1,349 submitted transcripts (658 valid):

| Tool | Overall Usage |
|---|---|
| Antigravity | 33.7% |
| Codex | 19.2% |
| Claude Code | 14.4% |
| GitHub Copilot | 11.1% |
| Claude Web | 8.4% |
| Cursor | small share |
| Gemini | small share |
| OpenCode | small share |
| ChatGPT | small share |
| Windsurf | small share |
| Kiro | small share |
| Amazon Q | small share |
| Replit Agent | small share |

13 distinct tools were found in active use across all transcripts.

---

## Tool Usage in Top 50

The mix shifts dramatically among top performers:

| Tool | Overall Usage | Top 50 Usage | Top 10 Usage |
|---|---|---|---|
| Antigravity | 33.7% | 12% | 0 |
| Codex | 19.2% | 12% | 1 |
| **Claude Code** | **14.4%** | **44%** | **7/10** |
| GitHub Copilot | 11.1% | 16% | 2 |
| Claude Web | 8.4% | 8% | 0 |

### Key Insight

Claude Code dominated the top 50 (44%) and top 10 (7 out of 10). Not a single Top 10 submission came from an Antigravity user despite Antigravity being the most popular tool overall.

### But the Correlation Is With BEHAVIOR, Not the Tool

The better read isn't that Claude Code is a superior tool. It's that participants who used Claude Code in this cohort also tended to be more deliberate builders:

- They logged their sessions completely
- They planned before coding
- They iterated against sample data
- They treated the AI as an engineering partner that needed direction, not a code generator that needed a prompt

**Tool and behavior were correlated. But the behavior was the actual driver.**

The leaderboard separated participants by how they worked with their tools, not which tool they picked.

---

## Distribution Shifts by Rank

| Rank Range | Leader | Runner-up |
|---|---|---|
| Top 50 | Claude Code (44%) | Copilot (16%) |
| Top 10 | Claude Code (70%) | Copilot (20%) |
| 101–500 | Antigravity (34%) | Claude Code (16%) |
| 500+ | Antigravity dominant | Claude Code nearly absent |

The tool mix inverts as you move down the leaderboard.

---

## Winner Behavior Pattern

The strongest participants, regardless of tool, followed this workflow:

1. **Read the problem statement** — Understand requirements before touching code
2. **Inspect the data** — Look at ticket structure, categories, edge cases
3. **Compare architectures** — Evaluate single agent vs multi-agent, BM25 vs semantic
4. **Implement with constraints** — Set specific parameters, schemas, thresholds
5. **Test against sample data** — Run on known tickets, check output quality
6. **Iterate based on failures** — Fix issues, check for regressions, re-test

### What Strong Users Did With Their Tool

| Behavior | Strong Pattern | Weak Pattern |
|---|---|---|
| **Planning** | "Let me read the problem first, then plan architecture" | "Build me an agent" |
| **Constraints** | "Use BM25, not semantic. Corpus is too small for embeddings." | "Use the best approach" |
| **Architecture** | "Compare single agent vs multi-agent. Trade off complexity vs maintainability." | "Just build it" |
| **Testing** | "Run on tickets 5, 12, 17 — those are fraud cases" | "Test it" |
| **Iteration** | "Ticket 12 is wrong. Justification is generic. Fix to reference docs/visa-fraud.md" | "Fix it" |
| **Pushback** | "No, don't use GPT-4 for classification. Use smaller model with structured output." | Accepting all suggestions |

---

## Chat Transcript Quality Tiers

### Tier 1: Engineering Partner (Top 50 behavior)
- Read the problem statement
- Inspect the data
- Compare architectures
- Implement with constraints
- Test against sample data
- Iterate based on failures
- Push back on AI when needed
- Reference specific tickets and regressions

### Tier 2: Directed Builder (Mid-tier behavior)
- Sets some constraints
- Tests occasionally
- Iterates when prompted
- Doesn't compare architectures
- Doesn't reference specific test results

### Tier 3: Passive Prompter (Lower-tier behavior)
- "Build me an agent that handles tickets"
- "Implement the file"
- Long processing logs without decision reasoning
- No testing evidence
- No architecture comparison

### Tier 4: Output Paster (Lowest tier)
- Pasted raw output CSV directly as transcript
- Not a development record at all
- "User: I lost my visa card" → "Agent: Please call Visa immediately"
- This was the output, not the build process

---

## Recommendation

**Use Claude Code** — not because it's inherently better, but because:
1. Top performers used it, suggesting it supports deliberate building behavior
2. It logs sessions well (important for chat transcript scoring)
3. It supports planning before coding
4. It handles iteration loops effectively

**But more importantly:** Regardless of tool, follow the winner behavior pattern:
1. Plan before coding
2. Set explicit constraints
3. Test against sample data
4. Iterate based on failures
5. Own your decisions in the transcript
