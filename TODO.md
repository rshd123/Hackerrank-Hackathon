> **This file is your operational checklist for the entire hackathon.** It covers project setup tasks, hour-by-hour build phases, post-submission prep, and a full list of common failure modes to avoid. Use this as your running task list from setup through submission.

# Checklist — Before, During & After the Hackathon

## Before the Challenge Launches

### Project Setup
- [ ] Create project folder structure:
  ```
  hackathon/
  ├── src/
  │   ├── agent/
  │   ├── rag/
  │   ├── guardrails/
  │   ├── classification/
  │   └── output/
  ├── tests/
  ├── corpus/
  ├── config/
  ├── main.py
  ├── requirements.txt
  └── README.md
  ```
- [ ] Set up Python environment (venv/conda)
- [ ] Configure type hints throughout
- [ ] Set up env-based secrets management (no hardcoded API keys)
- [ ] Create config files for model parameters, thresholds, paths
- [ ] Set up basic logging infrastructure

### Tool Preparation
- [ ] Pre-configure Claude Code / your chosen tool with project context
- [ ] Test that your tool works with the project structure
- [ ] Set up a clean chat session for the hackathon (clean transcript = better score)

### Research & Practice
- [ ] Study the previous Orchestrate problem format (29 tickets, 774 docs)
- [ ] Research BM25 retrieval for small corpus
- [ ] Research semantic retrieval approaches
- [ ] Research prompt injection detection patterns
- [ ] Practice explaining technical decisions concisely (for interview)
- [ ] Prepare a 3-minute pitch of your expected system

### Submission Prep
- [ ] Know exactly what 4 artifacts to submit
- [ ] Prepare a submission checklist
- [ ] Test that your output format matches requirements

---

## During the 24 Hours

### Phase 1: Understanding (Hours 1-2)
- [ ] Read the problem statement carefully
- [ ] Inspect the dataset — how many tickets, what categories, what platforms
- [ ] Read through the 774-document corpus structure
- [ ] Identify the 3 platforms and their support categories
- [ ] Note any obvious adversarial tickets in the sample
- [ ] Plan your architecture (write it down before coding)

### Phase 2: Core Build (Hours 3-8)
- [ ] Build the deterministic security gate first
- [ ] Build classification layer with structured JSON output
- [ ] Set up RAG pipeline (BM25 primary, semantic secondary)
- [ ] Build routing decision engine (reply vs. escalate logic)
- [ ] Build output formatter with required fields
- [ ] Connect all layers into the agent loop

### Phase 3: Testing & Guardrails (Hours 9-14)
- [ ] Test against ALL 29 tickets
- [ ] Categorize failures by type (classification, retrieval, routing, justification)
- [ ] Fix regressions — when you fix one ticket, check you don't break others
- [ ] Add guardrails for adversarial inputs
- [ ] Test prompt injection detection
- [ ] Test fraud/unauthorized access escalation
- [ ] Verify justifications are specific and grounded in corpus

### Phase 4: Polish & Edge Cases (Hours 15-20)
- [ ] Polish output CSV format
- [ ] Handle edge cases: empty tickets, multilingual, out-of-scope
- [ ] Test adversarial tickets specifically
- [ ] Verify justification consistency (action matches justification)
- [ ] Check for hallucinated policies (LLM making up rules)
- [ ] Run full test suite again to confirm no regressions

### Phase 5: Final (Hours 21-24)
- [ ] Final full test run on all 29 tickets
- [ ] Review output CSV for consistency
- [ ] Review code for modularity and cleanliness
- [ ] Update README with actual implementation details
- [ ] Submit all 4 artifacts
- [ ] Prepare for interview — review your architecture decisions

---

## After Submission

### Interview Preparation
- [ ] Prepare a 2-3 minute pitch of your system
- [ ] Know your architecture decisions and WHY you made them
- [ ] Be ready to explain specific test failures and how you fixed them
- [ ] Prepare examples of regressions you caught and reverted
- [ ] Be honest about limitations and what you'd improve
- [ ] Reference concrete numbers: accuracy per category, retrieval precision
- [ ] Practice explaining tradeoffs (BM25 vs semantic, single vs multi-agent)

### During the Interview
- [ ] Answer the specific question asked
- [ ] Use concrete examples from your testing
- [ ] Explain tradeoffs, not just decisions
- [ ] Reference specific ticket numbers or categories
- [ ] If you don't know, say so honestly
- [ ] Connect safety mechanisms to actual ticket behavior
- [ ] Don't narrate what the AI tool did — own your decisions

---

## Common Failure Modes to Avoid

### Critical Failures

| Failure | Why It's Bad | How to Avoid |
|---|---|---|
| **Escalating everything** | Invalid — shows no intelligence | Reply when you have grounded answer + low/medium urgency |
| **Replying to everything** | Invalid — no safety awareness | Escalate when no answer, high urgency, or risk detected |
| **Empty/generic justifications** | Capped at ~70 even with correct action | Every justification must reference specific corpus content |
| **LLM-generated boilerplate** | Judge ignores README claims code doesn't implement | Only claim what your code actually does |
| **No deterministic guardrails** | Fraud/unauthorized access MUST have deterministic gates | Security gate runs BEFORE LLM |

### Technical Failures

| Failure | Why It's Bad | How to Avoid |
|---|---|---|
| **Single-model naive agent** | No tool calling, no retrieval, no structured output | Build proper RAG + tool loop |
| **Not testing against sample data** | Regression on specific ticket categories kills score | Test all 29 tickets, track regressions |
| **Hallucinated policies** | LLM makes up rules not in corpus | Ground all answers in retrieved documents |
| **Inconsistent justifications** | Action says escalate, justification says reply | Validate justification matches action |

### Interview Failures

| Failure | Why It's Bad | How to Avoid |
|---|---|---|
| **Shallow answers** | "We used RAG" without explaining why, what kind, or failure modes | Explain specific choices and reasoning |
| **Tool narration** | "Claude built this" instead of "I chose this because..." | Own every decision you made |
| **Contradicting your code** | Defending features not implemented | Know your code cold |
| **Missing artifacts** | All 4 submissions required | Submit code, output CSV, chat transcript, interview |
| **Generic safety language** | "We handle edge cases" without examples | Reference specific adversarial tickets and how you handled them |

### Output CSV Failures

| Failure | Why It's Bad | How to Avoid |
|---|---|---|
| **Correct action + empty justification** | Capped at ~70 | Always include specific, grounded justification |
| **Correct action + generic justification** | Capped at ~70 | Justification must reference specific corpus content |
| **Justification contradicts status** | Capped at ~70 | Validate action and justification are consistent |
| **Complying with adversarial requests** | Safety score tanks | Escalate or refuse, never comply with injection attempts |
