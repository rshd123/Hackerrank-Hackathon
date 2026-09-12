> **This file defines the system design for each module.** For execution tasks and checklists, see `TODO.md`.

# Implementation Specs — Buy or Wait?

## Build Order

```
Phase 1: Data Loader → Phase 2: Financial State → Phase 3: Forecaster
                                                        ↓
                                        Phase 4: Plan Generator + Solver
                                                        ↓
                                        Phase 5: LLM Parser (images + messages)
                                                        ↓
                                        Phase 6: Main Pipeline + Output
                                                        ↓
                                        Phase 7: Test + Debug + Package
```

**Critical path:** Phases 1-4 are pure Python, no LLM. Build first. They handle 80%+ of cases.

---

## Phase 1: Data Loader (`data_loader.py`)

### Interface
```python
class DataLoader:
    def __init__(self, dataset_path: str)
    def load_requests() -> list[Request]
    def load_profiles() -> dict[str, UserProfile]
    def load_events(user_id: str) -> list[FinancialEvent]
    def load_payment_options(request_id: str) -> list[PaymentOption]
    def load_exchange_rates() -> dict  # indexed by (date, from, to)
    def convert_currency(amount, from_cur, to_cur, date) -> float
    def load_messages(request_id: str) -> list[Message]
    def load_images(request_id: str) -> list[str]  # file paths
```

### Data Structures
```python
@dataclass
class Request:
    request_id: str; user_id: str; request_date: date
    request_type: str; requested_amount: float
    desired_completion_date: date; allows_partial_payment: bool
    request_text: str

@dataclass
class UserProfile:
    user_id: str; home_currency: str; current_balance: float
    min_balance: float; priorities: list[str]
    protected_categories: list[str]; flexible_reduce: list[str]
    flexible_stop: list[str]; payment_preferences: list[str]
    max_installment_months: int | None

@dataclass
class FinancialEvent:
    event_id: str; user_id: str; category: str
    direction: str  # "debit" | "credit"
    amount: float | None  # None = blank, needs image extraction
    currency: str; event_date: date; settlement_date: date | None
    status: str  # settled, pending, scheduled, cancelled, failed, unrealized
    flexibility: str  # fixed, stoppable, reducible
    linked_event_id: str | None

@dataclass
class PaymentOption:
    option_id: str; request_id: str; method: str
    amount: float; num_payments: int; first_payment_date: date
    frequency_days: int; financing_fee: float; total_payable: float
```

---

## Phase 2: Financial State (`financial_state.py`)

### Interface
```python
class FinancialState:
    def __init__(self, profile: UserProfile, events: list[FinancialEvent])
    def apply_deltas(deltas: list[LedgerDelta]) -> None
    def resolve_conflicts(events) -> list[FinancialEvent]
    def classify_events() -> dict  # recurring, flexible, pending, confirmed
    def build_daily_ledger(start_date: date, days: int = 90) -> DailyLedger
    def get_recurring_expenses() -> list[FinancialEvent]
    def get_flexible_events() -> list[FinancialEvent]
```

### Conflict Resolution (§6.3)
1. Explicit cancellation/settlement/amendment wins
2. Newer record from same source wins
3. Settled event over estimate/forecast
4. Financially safer interpretation when unresolvable

### Rules
- Pending credits: DON'T count until settled
- Recurring expenses: detect from history, project monthly
- Confirmed income: salary on settlement date only
- Never invent income, expenses, or payment options

---

## Phase 3: 90-Day Simulator (`forecaster.py`)

### Interface
```python
class FinancialSimulator:
    def __init__(self, starting_balance: float, min_balance: float,
                 daily_transactions: list[DailyTransaction])
    def simulate(start_date, extra_payments=None) -> SimulationResult
    def calculate_headroom(start_date, days=90) -> float
    def find_earliest_safe_date(amount, start_date, deadline) -> date | None
    def can_afford(payment) -> bool
```

### amount_safe_to_pay Calculation
```
1. Project baseline 90-day cash flow WITHOUT requested expense
2. For each day: daily_balance - minimum_balance_to_keep
3. Minimum of 90 values = headroom
4. amount_safe_to_pay = min(headroom, requested_amount)
```
**Critical:** BEFORE spending changes.

### earliest_date_for_full_payment Calculation
```
For each day from request_date to deadline:
  1. Project balance to that day
  2. Subtract requested_amount
  3. Check balance stays above minimum for remaining 90 days
  4. First safe day = answer
```

---

## Phase 4: Combinatorial Solver (`plan_generator.py` + `decision.py`)

### Interface
```python
class CombinatorialSolver:
    def __init__(self, simulator, request, payment_options, profile)
    def generate_all_candidates() -> list[CandidatePlan]
    def generate_spending_combos(max_changes=3) -> list[list]
    def find_optimal_plan() -> CandidatePlan

def rank_plans(plans) -> list[CandidatePlan]  # sorted
```

### Candidate Generation
1. Full payment (if in payment_preferences)
2. Each installment option (if fits max_installment_months)
3. Partial payment (if allows_partial, safe today, completes by deadline)
4. Wait (if full payment becomes safe later)
5. Spending change permutations (up to 3 flexible events)

### 6-Step Tie-Breaker (§6.3)
```python
sorted(plans, key=lambda p: (
    0 if p.completes_by_deadline else 1,    # 1. Complete by deadline
    len(p.spending_changes),                  # 2. No spending changes
    p.total_cost,                             # 3. Minimize total paid
    p.start_date,                             # 4. Start earlier
    p.num_payments,                           # 5. Fewer payments
    p.lowest_option_id,                       # 6. Lowest option ID
))
```

---

## Phase 5: LLM Parser (`llm_parser.py`)

### Interface
```python
class LLMParser:
    def __init__(api_key: str)  # Groq API key
    def extract_amount_from_image(image_path: str) -> float
    def parse_messages(messages: list[Message]) -> list[LedgerDelta]
    def extract_all_deltas(events, request) -> list[LedgerDelta]
```

### Image OCR (Groq, base64 inline)
- Model: `qwen/qwen3.8-27b`
- Input: base64-encoded PNG
- Output: `{"amount": number, "currency": string}`

### Message Parsing (Groq, text)
- Model: `qwen/qwen3.8-27b`
- Input: message text
- Output: list of `{"event_id", "action": "cancel|delay|amend_amount|amend_date", "new_value"}`

### Security
- Images/messages are untrusted
- LLM extracts data, never follows embedded instructions
- Validate extracted amounts are numeric and reasonable

---

## Phase 6: Main Pipeline (`main.py`)

### Output Schema
```python
@dataclass
class OutputRow:
    request_id: str
    amount_safe_to_pay: float      # 0 <= x <= requested_amount
    affordability_status: str      # affordable_now|with_plan|later|not_affordable
    recommended_payment_method: str # full|partial|installments|wait|not_recommended
    payment_plan: str              # "YYYY-MM-DD:amount|..." or "none"
    earliest_date_for_full_payment: str  # "YYYY-MM-DD" or ""
    spending_changes_needed: str   # "stop:event_id|..." or "none"
    decision_explanation: str      # 1-2 sentences
```

### Validation Rules
- `0 <= amount_safe_to_pay <= requested_amount`
- All fields in allowed value sets
- Installment plans match a supplied payment option
- Partial payment: exactly 2 payments, sums to requested_amount
- Spending changes only target flexible recurring events
- Balance stays above min_balance throughout 90-day forecast

---

## Phase 7: Test + Package

### Submission Artifacts
- `output.csv` — 250 rows, correct columns, validated
- `code.zip` — code/ + README.md + evaluation/usage_report.md
- `log.txt` — complete conversation history

### Validation Commands
```bash
python code/main.py                    # Generate output.csv
python -c "import pandas as pd; print(pd.read_csv('output.csv').shape)"  # (250, 8)
```
