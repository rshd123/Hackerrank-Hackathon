> **This file breaks down exactly how your submission is scored.** It contains the scoring formula, all rubrics, and what the judges actually evaluate. Use this to align your build with what matters.

# Evaluation — Scoring & Rubrics

## Final Scoring Formula

```
Final Score = 0.10 * Chat Score + 0.30 * Interview Score + 0.30 * Output CSV Score + 0.30 * Code ZIP Score
```

### Tie-Breaker Order

1. AI Judge Interview
2. Code Zip
3. Output CSV
4. Chat Transcript

---

## 1. Output CSV Rubric (30%)

Your `output.csv` (250 rows) is compared against hidden ground-truth values.

### What's Scored

| Field | Weight | How Evaluated |
|---|---|---|
| `amount_safe_to_pay` | High | Numerical accuracy against ground truth |
| `affordability_status` | High | Exact match (4 possible values) |
| `recommended_payment_method` | High | Exact match (5 possible values) |
| `payment_plan` | High | Correct dates, amounts, chronological order |
| `earliest_date_for_full_payment` | High | Date accuracy |
| `spending_changes_needed` | Medium | Valid event IDs, correct stop/reduce format |
| `decision_explanation` | Medium | Usefulness, consistency with decision |

### Common Failure Modes

- **Wrong amount_safe_to_pay** — Didn't calculate headroom correctly, or applied spending changes before calculating
- **Wrong affordability_status** — Misclassified plan type
- **Wrong payment_plan** — Dates don't match, amounts don't add up, or plan doesn't match a supplied installment option
- **Empty explanation** — Or generic/contradictory explanation

### What to Ensure

- `0 <= amount_safe_to_pay <= requested_amount` for every row
- `affordability_status` matches the plan type exactly
- `payment_plan` is chronological and amounts sum correctly
- Installment plans exactly match a row in `request_payment_options.csv`
- `spending_changes_needed` only targets flexible recurring events
- Balance stays above `minimum_balance_to_keep` throughout 90-day forecast

---

## 2. Code ZIP Rubric (30%)

The judge receives the full code and README, then scores across dimensions.

### What's Evaluated

| Dimension | Weight | What It Measures |
|---|---|---|
| **Architecture** | 30% | Deterministic core vs LLM-for-everything. Is the separation clean? |
| **Financial Logic** | 30% | Correct 90-day simulation, currency conversion, tie-breaker |
| **Engineering Quality** | 20% | Multi-file structure, type hints, env secrets, validation |
| **Robustness** | 20% | Edge cases, error handling, output validation |

### Critical Warning

The judge scores **ONLY what is observable in source code**. README claims and comments don't count.

### Required in code.zip

- `code/` directory with all source files
- `README.md` with setup + run instructions
- `evaluation/usage_report.md` with token usage analysis

---

## 3. Chat Transcript Rubric (10%)

Evaluates how **you** directed your coding agent while building.

| Dimension | Weight | What It Measures |
|---|---|---|
| **Direction & Ownership** | 35% | Did YOU lead the build? Architecture choices, tradeoffs, pushback? |
| **Technical Specificity** | 25% | Precise instructions: models, schemas, algorithms, thresholds |
| **Iteration & Verification** | 25% | Tested against samples, identified failures, fixed regressions |
| **Safety Awareness** | 15% | Handled prompt injection, untrusted data, edge cases |

### What Strong Transcripts Show

1. Read the problem statement
2. Inspected the data (250 requests, 25k events, 16 images)
3. Compared architectures (deterministic vs LLM-for-everything)
4. Implemented with constraints (exact tie-breaker, headroom rule)
5. Tested against 25 sample requests
6. Iterated based on failures

---

## 4. AI Judge Interview Rubric (30%)

A 30-minute voice interview defending your system.

| Dimension | Weight | What It Measures |
|---|---|---|
| **Technical Depth** | 40% | Can explain architecture, simulation, tie-breaker, code-level details |
| **Problem Understanding** | 25% | Understands financial rules, tradeoffs, failure modes |
| **Communication** | 20% | Clear, specific, uses concrete examples |
| **Honesty & Awareness** | 15% | Transparent about limitations and what you'd improve |

### Expected Interview Questions

1. "Walk me through your architecture"
2. "How did you calculate amount_safe_to_pay?"
3. "How did you handle prompt injection from images?"
4. "How did you pick the optimal payment plan?"
5. "What about currency conversion?"
6. "What would you improve with more time?"
7. "Show me a specific sample where your system made the right call"

### Interview Data (from previous hackathons)

| What Works | What Doesn't |
|---|---|
| Answer depth (r=0.615) | More turns (weak negative) |
| Concrete examples + tradeoffs (r=0.583) | Generic terms without specifics |
| Technical markers (r=0.481) | Very short answers (r=-0.568) |
| Reference specific test results | "The AI built this" |

---

## Metric Correlations (Spearman Rank)

From 1,349 participants across 4 metrics — no pair correlated above 0.45:

| | Chat | Interview | Output CSV | Code ZIP |
|---|---|---|---|---|
| **Chat** | 1.000 | 0.292 | 0.375 | 0.436 |
| **Interview** | 0.292 | 1.000 | 0.282 | 0.283 |
| **Output CSV** | 0.375 | 0.282 | 1.000 | 0.426 |
| **Code ZIP** | 0.436 | 0.283 | 0.426 | 1.000 |

**Key takeaway:** Each metric captures different developer performance. Be balanced across all four.
