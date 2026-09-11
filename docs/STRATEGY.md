> **This file teaches you how winners think and defend their work.** It covers what Top 50 participants did differently, interview probe order, data-backed tips, chat transcript strategy, and output CSV strategy. Use this to prepare for the 30-minute AI judge interview and to guide your chat transcript behavior.

# Strategy — Winning Patterns & Interview Tips

## What the Top 50 Did Differently

### 1. They Owned the System

They explained **WHY** they chose architectures, not just WHAT they built.

**Strong answer:**
> "We used BM25 because the corpus was small and keyword-heavy, then added a reranker only after seeing retrieval misses on specific sample rows."

**Weak answer:**
> "The agent searches the data and gives the best answer."

Both describe retrieval. Only the first provides engineering judgment.

### 2. Evidence-Based Iteration

They referenced concrete results: sample ticket accuracy, specific test cases, changes they reverted because output got worse, output.csv regressions.

**Strong answer:**
> "We tried increasing top_k, but it caused regressions on the Visa fraud rows, so we reverted it and kept the deterministic escalation gate."

This pattern is rewarded because it mirrors real engineering: notice a regression, make a design change, make a judgment call.

### 3. Risk Handled Concretely

Not just "high-risk tickets should be escalated" but connected words to actual system behavior.

**Strong answer:**
> "The LLM cannot downgrade a high-risk ticket. The deterministic gate runs first, and if it detects fraud or unauthorized access, the model is only allowed to produce an escalation response."

**Weak answer:**
> "High-risk tickets should be escalated."

Both are directionally correct. Only the first explains the mechanism.

### 4. Own Decisions, Not Tool Narration

Spoke in terms of their own decisions:

- "I chose this architecture because..."
- "I rejected that approach because..."
- "We measured this and reverted it..."
- "I made the LLM output schema-enforced JSON because..."

**NOT:**
- "Claude created the pipeline."
- "The AI checked the files."
- "The agent decided the answer."

---

## Interview Strategy

### Probe Order (Expect This Sequence)

1. **Quick pitch** — 2-3 minute overview of your system
2. **Retrieval and architecture** — What kind of retrieval, why, where it fits
3. **Safety and failure modes** — How prompt injection handled, when to refuse vs escalate
4. **Implementation and code familiarity** — Code-level details, specific functions
5. **Evaluation** — How you tested, what metrics you tracked
6. **Production monitoring** — What you'd add for production deployment
7. **What is novel** — What's different about your approach

### Data-Backed Tips

| What Works | What Doesn't |
|---|---|
| Answer depth (r=0.615 with score) | More turns (weak negative correlation) |
| Concrete examples + tradeoffs (r=0.583) | Generic terms without specifics |
| Technical markers (r=0.481) | Very short answers (r=-0.568) |
| Longer answer share (r=0.631) | Staying at same abstraction level throughout |

### Leaderboard Bucket Insights

| Rank Range | What They Did | What They Missed |
|---|---|---|
| **1–50** | Explained architecture choices, tradeoffs, testing evidence, regressions, safety mechanisms. Sounded like system owners. | — |
| **51–100** | Still strong builders, knew core system | Less consistent on production monitoring, novelty, code-level details |
| **101–250** | Working systems, explained retrieval well | Didn't connect retrieval to output quality, guardrails, or measured regressions |
| **251–500** | Described task flow correctly | Couldn't explain WHY designed that way or how validated |
| **501–1000** | Used words like "validated," "risk," "safety" | No concrete failures, changes, or tradeoffs |
| **1001+** | Incomplete or non-specific | Broad product explanations, not engineering explanations |

### High-Signal Interview Behaviors

1. **Reference specific test results** — "On the 29 tickets, we got X correct on Y category"
2. **Name implementation details** — File paths, function names, specific parameters
3. **Discuss regressions** — "We tried X, it broke Y, so we reverted and did Z"
4. **Handle challenges with tradeoffs** — When the judge pushes back, explain the reasoning
5. **Be honest about gaps** — "We didn't implement X because of Y, but in production we'd add Z"

### Low-Signal Interview Behaviors

1. **Tool narration** — Describing what Claude/Cursor did instead of your decisions
2. **Repeating the problem statement** — Shows no engineering depth
3. **Generic safety language** — "We handle edge cases" without examples
4. **Contradicting your own code** — Defending features not actually implemented
5. **Short answers** — Stopping before proving real understanding

---

## Chat Transcript Strategy

### What to Show in Your Transcript

The chat transcript is evaluated on how YOU directed the AI tool, not what the tool produced.

**Strong patterns:**
1. **Plan before coding** — "Let me read the problem statement first, then inspect the data"
2. **Set constraints** — "Use BM25, not semantic search. The corpus is too small for embeddings to add value."
3. **Compare architectures** — "Should we use single agent or multi-agent? Let me compare tradeoffs."
4. **Test against samples** — "Run this on tickets 5, 12, and 17 — those are the fraud cases"
5. **Iterate on failures** — "Ticket 12 is wrong. The justification is generic. Fix it to reference the specific policy in docs/visa-fraud.md"
6. **Push back on AI** — "No, don't use GPT-4 for classification. Use a smaller model with structured output."

**Weak patterns:**
1. "Build me an agent that handles tickets"
2. "Implement the file"
3. Long processing logs without decision reasoning
4. Pasting output CSV directly as transcript

---

## Output CSV Strategy

### Common Failure Mode

Agent returns correct action + reasonable response, but justification is **empty, generic, or contradicts status** → capped at **~70**.

### What to Ensure

- Every justification must be **specific** and **grounded in the corpus**
- Justification must be **consistent** with the action (reply vs. escalate)
- Never leave justification empty
- Handle adversarial tickets correctly (escalate or refuse, never comply)
- Test every ticket category: billing, technical, security, fraud, general

### Ticket Categories to Test

Based on the three platforms (HackerRank, Anthropic, Visa):
- Account access and authentication
- Billing and payments
- Technical support
- Security and fraud
- API and integration issues
- Policy questions
- Edge cases and adversarial inputs
