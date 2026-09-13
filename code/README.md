# Buy or Wait? - HackerRank Orchestrate September 2026

An AI-powered financial decision agent that evaluates whether users can safely afford requested expenses.

## Architecture

```
data_loader.py  ->  financial_state.py  ->  forecaster.py
                                                |
                                    plan_generator.py + decision.py
                                                |
                                          llm_parser.py (optional)
                                                |
                                            main.py -> output.csv
```

## Modules

| Module | Lines | Purpose |
|---|---|---|
| `data_loader.py` | 210 | Load 9 CSVs, typed dataclasses, currency conversion |
| `financial_state.py` | 330 | Event classification, conflict resolution, income projection, daily ledger |
| `forecaster.py` | 220 | 90-day simulator, headroom calc, payment scenario testing |
| `plan_generator.py` | 226 | Combinatorial solver: full, installment, partial, wait candidates |
| `decision.py` | 201 | 6-step tie-breaker ranking engine |
| `llm_parser.py` | 216 | Groq qwen3.8-27b for message parsing + image OCR |
| `main.py` | 195 | End-to-end pipeline, error handling, CSV output |

## How to Run

```bash
# Activate conda environment
conda activate hackerrank

# Install dependencies
pip install -r requirements.txt

# Run (deterministic only, ~1.5s)
python code/main.py --no-llm

# Run with LLM (message parsing + image OCR)
python code/main.py
```

## Output Format

```csv
request_id,amount_safe_to_pay,affordability_status,recommended_payment_method,payment_plan,earliest_date_for_full_payment,spending_changes_needed,decision_explanation
```

## Decision Rules (from challenge spec)

1. **affordable_now:** Full payment safe on request_date, balance stays above minimum
2. **affordable_with_plan:** Installments or partial payment completes by deadline
3. **affordable_later:** Full payment becomes safe after request_date
4. **not_affordable:** No safe option within forecast period

## 6-Step Tie-Breaker

1. Complete by deadline
2. No spending changes
3. Minimize total cost
4. Start earlier
5. Fewer payments
6. Lowest payment_option_id

## Dataset

- 250 requests, 275 profiles, 25,342 events
- 5 currencies: INR, ZAR, IDR, USD, EUR
- 16 images, 215 messages

## Key Design Decisions

- **Deterministic core:** 95% of logic is pure Python, no LLM dependency
- **LLM as extraction layer:** Groq for message parsing and image OCR only
- **Income projection:** Detects weekly/bi-weekly/monthly salary patterns and projects forward
- **Conflict resolution:** Settled > pending, newer > older, safer interpretation
- **Combinatorial solver:** Generates ALL candidates, ranks by exact tie-breaker

## Evaluation

Model: Groq qwen/qwen3.8-27b (free tier)
- ~266 API calls for 250 requests
- ~330K input tokens, ~50K output tokens
- Total cost: $0.00
