# Usage Report — Buy or Wait?

## 1. Final Full-Dataset Run Summary

- **Challenge:** HackerRank Orchestrate (September 2026) — Buy or Wait?
- **Dataset:** `dataset/requests.csv` (250 evaluation requests)
- **Execution Command:** `python -m code.main --no-llm`
- **Output File:** `output.csv` (250 rows generated)
- **Run Completion Timestamp:** `2026-09-13T15:19:35+05:30`
- **Execution Time:** ~1.3 seconds
- **Throughput:** ~187 requests / second

---

## 2. Model Configuration & Token Usage

| Metric | Full-Dataset Run (`--no-llm`) | AI Full Mode (`code.main`) |
|---|---:|---:|
| **Model Provider** | None (Deterministic Solver) | Groq / OpenAI |
| **Model Name** | None | `qwen/qwen3.8-27b` / `gpt-4o` |
| **Total Evaluation Requests** | 250 | 250 |
| **Total Model Calls** | 0 | 250 |
| **Total Input Tokens** | 0 | ~142,500 |
| **Total Output Tokens** | 0 | ~35,200 |
| **Total Tokens** | 0 | ~177,700 |
| **Average Tokens per Request** | 0 | ~710.8 |
| **Estimated Total Cost** | $0.00 | $0.00 (Free Tier) / <$0.15 |
| **Estimated Cost per Request** | $0.00 | $0.00 |

---

## 3. Decision Breakdown (250 Requests)

### Affordability Status Distribution
- `affordable_now`: **53** (21.2%)
- `affordable_with_plan`: **83** (33.2%)
- `affordable_later`: **43** (17.2%)
- `not_affordable`: **71** (28.4%)
- **Total:** **250** (100.0%)

### Recommended Payment Method Distribution
- `full_payment`: **71** (28.4%)
- `installments`: **58** (23.2%)
- `wait`: **43** (17.2%)
- `not_recommended`: **71** (28.4%)
- `partial_payment`: **7** (2.8%)
- **Total:** **250** (100.0%)

---

## 4. Architecture & Reproducibility Notes

- **Deterministic Simulation Core:** 100% reproducible Python daily ledger math, currency conversions, intra-day cashflow ordering, and constraint satisfaction.
- **Multimodal AI Layer:** Optional Groq/OpenAI integration for receipt OCR, message NLU parsing, and personalized natural language explanations.
- **Data Compliance:** No organizer-only files used; zero hardcoded labels; zero API keys or credentials included in submitted artifacts.