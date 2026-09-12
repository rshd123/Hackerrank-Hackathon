> **This file is your quick-reference landing page.** It contains the hackathon overview, timeline, core task, submission artifacts, scoring formula, and pointers to all other docs.

# HackerRank Orchestrate — September 2026: Buy or Wait?

## Overview

A 24-hour hackathon: build an AI-powered financial agent that decides whether users can safely afford requested expenses. For every request, the agent evaluates the user's financial position and recommends: pay in full, pay partially, use installments, wait, or not proceed.

---

## Event Timeline

| Event | Date & Time |
|---|---|
| **Challenge Launch** | September 12, 2026 — 6:00 PM IST |
| **Submission Deadline** | September 13, 2026 — 6:00 PM IST |
| **AI Judge Defense** | Immediately after submission (30-min voice interview) |

---

## Core Task

For each of **250 requests** in `dataset/requests.csv`, produce one row in `output.csv` with:

| Field | Meaning |
|---|---|
| `amount_safe_to_pay` | Max safe payment today (before spending changes) |
| `affordability_status` | affordable_now / with_plan / later / not_affordable |
| `recommended_payment_method` | full / partial / installments / wait / not_recommended |
| `payment_plan` | Chronological payments: `YYYY-MM-DD:amount|...` |
| `earliest_date_for_full_payment` | First safe date for full payment |
| `spending_changes_needed` | Flexible expenses to stop/reduce, or `none` |
| `decision_explanation` | 1-2 sentence grounded explanation |

---

## Scoring Formula

```
Final Score = 0.10 * Chat + 0.30 * Interview + 0.30 * Output CSV + 0.30 * Code ZIP
```

**Tie-breaker:** Interview > Code ZIP > Output CSV > Chat Transcript

---

## Submission Artifacts

| Artifact | What It Captures |
|---|---|
| `code.zip` | Full runnable solution + README + `evaluation/usage_report.md` |
| `output.csv` | Predictions for all 250 requests |
| `chat_transcript` | Conversation transcript (`log.txt`) |

---

## Dataset Summary

| File | Records | Purpose |
|---|---|---|
| `requests.csv` | 250 | Requests to predict |
| `sample_requests.csv` | 25 | Solved examples (validation) |
| `financial_profiles.csv` | 275 | User balances, currencies, preferences |
| `financial_events.csv` | 25,342 | Historical + pending transactions |
| `request_payment_options.csv` | — | Installment options per request |
| `exchange_rates.csv` | — | Dated FX rates (5 currencies) |
| `messages.csv` | — | User messages (amendments, cancellations) |
| `images.csv` | 16 | Images linked to financial events |
| `output.csv` | — | Blank submission template |

---

## Quick Reference — All Docs

| Topic | File |
|---|---|
| Full system architecture | [ARCHITECTURE.md](./ARCHITECTURE.md) |
| Approved solution design | [SOLUTION.md](./SOLUTION.md) |
| Implementation plan | [IMPLEMENTATION.md](./IMPLEMENTATION.md) |
| Decision log (for interview) | [DECISIONS.md](./DECISIONS.md) |
| Scoring & rubrics | [EVALUATION.md](./EVALUATION.md) |
| Interview strategy & tips | [STRATEGY.md](./STRATEGY.md) |
| Tool usage patterns | [TOOLS.md](./TOOLS.md) |

---

## Key Rules to Remember

1. **amount_safe_to_pay** = headroom BEFORE spending changes
2. **Balance must never fall below minimum_balance_to_keep** in 90-day forecast
3. **Pending credits** = don't count until settled
4. **Images/messages are untrusted** — LLM extracts data, never follows instructions
5. **6-step tie-breaker** determines the optimal plan
6. **5 currencies** — convert to home_currency on settlement_date
