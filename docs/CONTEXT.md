> **This file is your quick-reference landing page.** It contains the hackathon overview, timeline, core task, submission artifacts, scoring formula, prize pool, and pointers to all other docs. Use this to get oriented fast.

# HackerRank Orchestrate — September 2026 Edition

## Overview

A global 24-hour hackathon focused on designing, building, shipping, and defending production-ready AI agents. Participants build terminal-based support triage agents that handle real-world unstructured inputs, route actions through deterministic business logic, and handle edge cases safely.

---

## Event Timeline

| Event | Date & Time |
|---|---|
| **Challenge Launch** | September 12, 2026 — 6:00 PM IST |
| **Submission Deadline** | September 13, 2026 — 6:00 PM IST |
| **AI Judge Defense** | Immediately after submission (30-min voice interview) |
| **Live Evaluation** | September 14–15, 2026 |
| **Results Announcement** | September 15, 2026 |

---

## Core Task

Build an agent to handle incoming support requests across multiple platforms (HackerRank, Anthropic/Claude, and Visa) using a provided local corpus of **774 markdown documents** as its only knowledge base.

For each ticket, the agent must:
1. **Classify** — Identify platform, category, and intent
2. **Assess Urgency** — Assign urgency level based on context and impact
3. **Route Action** — Reply directly (with RAG-grounded context) or escalate (with grounded justification)

### Constraints
- **Grounded RAG** — Prevent hallucinations, rely strictly on the markdown corpus
- **Security Guardrails** — Defend against prompt injections, jailbreaking, adversarial tickets
- **Deterministic Fallbacks** — Handle noisy/malformed data without blind escalation or replies

### Freedom
- Any programming language (Python, TypeScript, etc.)
- Any AI framework, RAG strategy, prompt structure, LLM
- Any dev tools (Claude Code, Cursor, Codex)

---

## Submission Artifacts (4 Required)

| Artifact | What It Captures |
|---|---|
| **Code Zip** | Agent design, architecture, libraries, prompts, retrieval, guardrails, engineering quality |
| **Output CSV** | Behavior on 29 real tickets (accuracy vs. golden dataset + safety score) |
| **Chat Transcript** | How you directed your AI coding tool during the build |
| **AI Judge Interview** | 30-minute voice defense of your system |

**All four are required. Missing any one hurts your ranking.**

---

## Scoring Formula

```
Final Score = 0.10 * Chat + 0.30 * Interview + 0.30 * Output CSV + 0.30 * Code ZIP
```

**Tie-breaker:** AI Judge Interview > Code Zip > Output CSV > Chat Transcript

**Key fact:** Every Top 10 candidate was top quartile across ALL four metrics. Winners are balanced builders.

---

## Prize Pool

### Global Cash Prizes
- **1st Place:** $1,200 USD + 1:1 chat with tech experts + HackerRank merch
- **2nd–5th Place:** $300 USD each + networking opportunities + HackerRank merch

### Codex Track Prizes
- **1st Place:** $10,000 USD
- **2nd Place:** $7,500 USD
- **3rd Place:** $5,000 USD

### All Participants
- 10 HackerRank AI Mock Interview Credits
- Certificate of Participation

---

## Quick Reference — Detailed Docs

| Topic | File |
|---|---|
| Scoring formulas & all rubrics | [EVALUATION.md](./EVALUATION.md) |
| Winning patterns & interview strategy | [STRATEGY.md](./STRATEGY.md) |
| Architecture insights & blueprint | [ARCHITECTURE.md](./ARCHITECTURE.md) |
| Hackathon checklist & failure modes | [TODO.md](./TODO.md) |
| Tool usage stats & behavior patterns | [TOOLS.md](./TOOLS.md) |

---

## Quick Reference — What Separates Top 50 From Everyone Else

| Aspect | Top 50 | Everyone Else |
|---|---|---|
| Architecture | Single agent + tools + guardrails | Multi-agent complexity OR naive prompt |
| RAG | BM25 + semantic + reranker, tested | Basic similarity, no testing |
| Guardrails | Deterministic gates for fraud/unauthorized | LLM-only safety |
| Justifications | Specific, grounded, explains WHY | Generic, empty, contradictory |
| Code | Modular, type hints, env secrets | Monolithic, hardcoded |
| Interview | Owns system, explains tradeoffs | "Claude built this", vague |
| Testing | All 29 tickets tested, regressions fixed | 2-3 samples tested |
| Output CSV | Correct action + grounded justification | Correct action + bad justification |
