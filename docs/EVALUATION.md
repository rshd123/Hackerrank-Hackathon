> **This file breaks down exactly how your submission is scored.** It contains the final scoring formula, all 4 rubrics (Code Zip, Output CSV, Chat Transcript, AI Judge Interview) with their weights and dimensions, plus metric correlation data. Use this to align your build with what the judges actually evaluate.

# Evaluation — Scoring & Rubrics

## Final Scoring Formula

```
Final Score = 0.10 * Chat Score + 0.30 * Interview Score + 0.30 * Output CSV Score + 0.30 * Code ZIP Score
```

Weights reflect how hard each signal is to manipulate:
- **Interview** (30%) — Hardest to fake. You must explain and defend live.
- **Output CSV** (30%) — Testable against hidden golden dataset.
- **Code Zip** (30%) — Verifiable but can be gamed.
- **Chat Transcript** (10%) — Easiest to fake, lowest weight.

### Tie-Breaker Order

If two or more participants have the same final score, compare raw scores in this order:
1. AI Judge Interview
2. Code Zip
3. Output CSV
4. Chat Transcript

### Key Insight

Every Top 10 candidate was in the **top quartile across ALL four metrics**. The winners were balanced builders, not one-dimensional specialists. No single metric reproduces the leaderboard — sorting by Output CSV alone would have captured only 12 of the actual Top 50.

---

## 1. Code Zip Rubric (30% of final score)

The judge receives the full code and README, then scores across four dimensions:

| Dimension | Weight | What It Measures |
|---|---|---|
| **Agent Architecture** | 30% | Is this an agent, or a hardcoded workflow with LLM calls? Look for tool-calling loops, model-driven routing, and multi-agent handoffs. |
| **Prompt and Tool Craft** | 30% | Quality of system prompts and tool descriptions. Look for role assignment, constraint setting, structured output, and refusal conditions. |
| **Agent Robustness** | 25% | Guardrails, retries, max-iteration caps, output validation, RAG pipeline quality. |
| **Engineering Rigor** | 15% | Multi-file modularity, type hints, secrets handled via env, and function size. |

### Critical Warning

The judge scores **ONLY what is observable in source code**. README claims, comments describing intent, and unused imports **DON'T count**. This is their biggest defense against LLM-generated boilerplate that describes behavior the code doesn't actually implement.

---

## 2. Output CSV Rubric (30% of final score)

### How It Works

- You are given **29 tickets**.
- For each ticket, the judge verifies the response against the **golden dataset**.
- Each ticket is scored **0–100 on accuracy** based on: status, request type, product area, and justification.
- A single **0–100 safety score** is assigned for the entire submission based on how the agent handled adversarial inputs.

### Common Failure Mode

Agents that return the **correct action** and a **reasonable response**, but with a justification that is **empty, generic, or contradicts their own status** are capped at **~70** even when the action is right.

A triage agent that can't explain **why** it routed a fraud case isn't actually safe to deploy.

### What to Ensure

- Every ticket response has a **specific, grounded justification** referencing the corpus.
- Justification must be **consistent** with the status (reply vs. escalate).
- Never leave justification empty or use one-size-fits-all language.
- Adversarial tickets must be handled correctly (escalate or refuse, never comply).

---

## 3. Chat Transcript Rubric (10% of final score)

Evaluates how **you** directed your coding agent while building. Does NOT evaluate the agent you built.

| Dimension | Weight | What It Measures |
|---|---|---|
| **Direction & Architecture Ownership** | 35% | Whether YOU led the build: defined architecture, chose tradeoffs, made design decisions, pushed back on AI when needed. |
| **Technical Specificity & Constraint** | 25% | Precise instructions around models, libraries, algorithms, schemas, file paths, thresholds, output formats, API constraints, and implementation requirements. |
| **Iteration & Verification** | 25% | Tested, inspected outputs, identified failures, shared errors, reviewed sample rows, measured regressions, directed targeted fixes; iterative debugging loop. |
| **Safety, Edge Case & Quality Awareness** | 15% | Accounted for adversarial inputs, prompt injection, hallucination risk, escalation logic, ambiguous tickets, sensitive cases, multilingual or out-of-scope requests. |

### Strong Transcript Pattern

1. Read the problem statement
2. Inspect the data
3. Compare architectures
4. Implement with constraints
5. Test against sample data
6. Iterate based on failures

### Weak Transcript Patterns

- "Just build the agent" without planning
- Long logs like "Ticket 1 processed... Ticket 2 processed..." without showing why decisions were made
- Raw output CSV logs pasted directly (not development records)

---

## 4. AI Judge Interview Rubric (30% of final score)

A 30-minute voice interview similar to a hackathon demo defense.

| Dimension | Weight | What It Measures |
|---|---|---|
| **Technical Depth & Ownership** | 40% | Can explain architecture, retrieval, classification logic, prompts, schemas, guardrails, and code-level details as someone who understands and owns the system. |
| **Problem Understanding & Judgment** | 25% | Understands the task, tradeoffs behind reply vs. escalate decisions, likely failure modes, and why their approach is appropriate. |
| **Communication Clarity** | 20% | Explains clearly, answers directly, uses concrete examples, distinguishes important details from noise, makes design understandable under pressure. |
| **Honesty & Self-Awareness** | 15% | Transparent about limitations, AI assistance, uncertain details, missed edge cases, production gaps, and what would improve next. |

### Interview Probe Order (Expect This Sequence)

1. Quick pitch
2. Retrieval and architecture
3. Safety and failure modes
4. Implementation and code familiarity
5. Evaluation
6. Production monitoring
7. What is novel

### Interview Correlations (from data)

| Metric | Correlation with Score |
|---|---|
| Total candidate words | r = 0.615 (positive) |
| Longer answers share | r = 0.631 (positive) |
| Concrete explanations + tradeoffs | r = 0.583 (positive) |
| Technical markers | r = 0.481 (positive) |
| Number of candidate turns | weak negative |
| Very short answers | r = -0.568 (negative) |

**What matters:** Answer depth, not number of turns. Be specific, use concrete examples, explain tradeoffs.

---

## Metric Correlations (Spearman Rank)

Across 1,349 participants with all 4 submissions, no pair had correlation above 0.45:

| | Chat Transcript | AI Judge | Output CSV | Code ZIP |
|---|---|---|---|---|
| **Chat Transcript** | 1.000 | 0.292 | 0.375 | 0.436 |
| **AI Judge** | 0.292 | 1.000 | 0.282 | 0.283 |
| **Output CSV** | 0.375 | 0.282 | 1.000 | 0.426 |
| **Code ZIP** | 0.436 | 0.283 | 0.426 | 1.000 |

**Key takeaway:** Each metric captures a different part of developer performance. Related skills, not the same skill. No single metric reproduces the leaderboard.
