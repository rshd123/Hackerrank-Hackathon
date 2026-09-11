# AGENTS.md — Instructions for AI Coding Agents

## IMPORTANT: New Session Protocol

**Before making ANY code changes in a new session, ALWAYS:**

1. Read through the `/docs` folder to understand the hackathon context
2. Start with `CONTEXT.md` for overview, then read the relevant file for your task
3. Understand the evaluation rubrics in `EVALUATION.md` before writing any code
4. Check `TODO.md` for current task status and what's next

**Why:** The docs contain critical scoring formulas, winning patterns, and architecture decisions that MUST guide every code change. Without this context, you risk building something that doesn't score well.

---

## Project Overview

This is a HackerRank Orchestrate hackathon submission — a 24-hour sprint to build an AI support triage agent.

**Goal:** Build an agent that handles support tickets across HackerRank, Anthropic, and Visa using a 774-document markdown corpus as its knowledge base.

**Scoring:**
- 30% Code ZIP
- 30% Output CSV
- 30% AI Judge Interview
- 10% Chat Transcript

---

## Architecture

Single agent with tools + guardrails. NO multi-agent complexity.

```
Ticket → Security Gate → Classifier → RAG → Router → Output
```

**Key files:**
- `agent/core.py` — Main pipeline
- `agent/guardrails.py` — Deterministic security (injection/jailbreak/fraud)
- `agent/classifier.py` — Platform, category, intent, urgency
- `agent/rag.py` — BM25 + semantic retrieval + reranker
- `agent/router.py` — Reply vs escalate decisions
- `agent/schemas.py` — Pydantic models
- `config/settings.py` — All tunable parameters

---

## Code Style

- Python 3.11+
- Type hints on all functions
- Pydantic for all data models
- No hardcoded values — use `config/settings.py`
- No secrets in code — use environment variables
- Modular functions — keep functions under 50 lines
- Docstrings on all public functions

---

## Critical Rules

1. **Deterministic gates FIRST** — Security checks run before any LLM call
2. **Grounded justifications ONLY** — Every response must reference corpus documents
3. **No hallucinated policies** — Never make up rules not in the knowledge base
4. **Test after every change** — Run `python main.py --test` to check regressions
5. **Justification must match action** — If escalating, justification must explain why

---

## What NOT to Do

- Do NOT build multi-agent systems (single agent wins)
- Do NOT use only semantic search (BM25 primary, semantic secondary)
- Do NOT hardcode API keys
- Do NOT skip the security gate
- Do NOT reply to every ticket (escalate when needed)
- Do NOT escalate every ticket (shows no intelligence)
- Do NOT leave justifications empty or generic

---

## Testing

After any code change, run:
```bash
python main.py --test
```

Track regressions — if fixing one ticket breaks another, find a solution that works for both.

---

## Submission Artifacts

All four are required:
1. Code ZIP — All source code
2. Output CSV — Agent responses to 29 tickets
3. Chat Transcript — Export from your AI coding tool
4. AI Judge Interview — 30-minute voice defense

---

## Interview Prep

Be ready to explain:
- WHY you chose your architecture (not just WHAT)
- Specific tradeoffs you made
- Regressions you caught and fixed
- How deterministic gates override LLM for safety
- What you'd improve with more time

**Do NOT say:** "Claude built this"
**DO say:** "I chose this architecture because..."
