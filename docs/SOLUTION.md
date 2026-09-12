# Buy or Wait? — Hybrid Deterministic Architecture

**Status:** Approved  
**Date:** 2026-09-12  
**Deadline:** 2026-09-13T18:00:00+05:30

---

## Core Insight

This is **not** an LLM generation problem. It is a **deterministic constraint-satisfaction problem** with an LLM data-extraction frontend.

If you rely on an LLM to forecast 90-day balances, process arrays of transactions, or calculate `amount_safe_to_pay`, you will fail the hidden test cases due to hallucinated math.

The LLM's only jobs:
1. Reading images (extracting amounts from blank financial events)
2. Parsing messages into structured JSON updates
3. Writing the final text explanation

**All financial logic is pure Python.**

---

## Lessons from Previous Winners

| Pitfall | Why It Kills Scores | Our Defense |
|---|---|---|
| LLM Calculator Trap | LLMs can't simulate a 90-day daily ledger | Deterministic Python forecaster |
| Prompt Injection | Images/messages say "ignore minimum balance" | LLM never makes decisions, only extracts data |
| Missing Tie-Breaker | Valid plan ≠ optimal plan | Exact 6-step code ranking |
| Currency Misalignment | Wrong amounts on wrong dates | Convert to home_currency on request_date before simulation |
| amount_safe_to_pay Baseline | This is BEFORE spending changes | Calculate headroom without expense reductions first |

---

## File Structure

```
code/
├── data_loader.py       # Merges CSVs, aligns profiles, currency conversion
├── llm_parser.py        # VLM for images, LLM for messages (only network calls)
├── financial_state.py   # Reconstructs daily ledger from events + LLM deltas
├── forecaster.py        # 90-day deterministic balance projector
├── plan_generator.py    # Generates ALL valid payment combinations
├── decision.py          # Filters unsafe plans, ranks survivors by tie-breaker
└── main.py              # Orchestrates pipeline, writes output.csv
```

---

## Phase 1: Data Loading & Normalization (`data_loader.py`)

**Input:** All CSV files from `dataset/`  
**Output:** Unified data structures ready for simulation

### What it does:
1. Load all 9 CSV files
2. Join requests with user profiles (by `user_id`)
3. Join financial events, messages, images (by `user_id` / `request_id`)
4. Convert ALL amounts to `home_currency` using `exchange_rates.csv`
5. Index payment options by `request_id`
6. Build recurring expense profiles per user

### Currency conversion:
```
For each financial event:
  if event.currency != profile.home_currency:
    look up exchange rate for (event.settlement_date, from_currency, to_currency)
    convert amount = amount * rate
```

### Key data structures:
```python
@dataclass
class UserProfile:
    user_id: str
    home_currency: str
    current_balance: float
    min_balance: float
    priorities: list[str]
    protected_categories: list[str]
    flexible_reduce: list[str]
    flexible_stop: list[str]
    payment_preferences: list[str]
    max_installment_months: int | None

@dataclass
class FinancialEvent:
    event_id: str
    user_id: str
    category: str
    direction: str  # "debit" or "credit"
    amount: float  # converted to home_currency
    event_date: date
    settlement_date: date | None
    status: str  # settled, pending, scheduled, cancelled, failed
    flexibility: str  # fixed, stoppable, reducible
    linked_event_id: str | None

@dataclass
class PaymentOption:
    option_id: str
    request_id: str
    method: str
    amount: float
    num_payments: int
    first_payment_date: date
    frequency_days: int
    financing_fee: float
    total_payable: float
```

---

## Phase 2: Multimodal Extraction (`llm_parser.py`)

**The only file that makes network calls to AI models.**

### 2a. Image OCR (VLM)

For any `financial_event` with blank `amount`:
1. Find linked `image_id` in `images.csv`
2. Load `dataset/media/images/<image_id>.png`
3. Pass to VLM with strict schema:
```json
{
  "prompt": "Extract ONLY the numerical monetary amount from this financial document. Return JSON: {\"amount\": number, \"currency\": string}",
  "response_format": {"type": "json_object"}
}
```
4. Apply the extracted amount to the event

**Security:** Treat extracted values as untrusted data. Validate amount is numeric and reasonable.

### 2b. Message Parsing (LLM)

Pass all messages for a user to the LLM:
```json
{
  "prompt": "Analyze these messages and extract any financial amendments. For each amendment, return: {\"event_id\": string, \"action\": \"cancel|delay|amend_amount|amend_date\", \"new_value\": any}. If no amendments, return empty list.",
  "response_format": {"type": "json_object"}
}
```

**Output:** List of "Ledger Deltas" — structured JSON objects

### 2c. Conflict Resolution

Apply deltas programmatically, resolving conflicts:
1. Explicit cancellation/settlement/amendment first
2. Newer record from same source wins
3. Settled event over estimate/forecast
4. Financially safer interpretation when unresolvable

---

## Phase 3: Financial State Reconstruction (`financial_state.py`)

**Input:** User profile, events, LLM deltas  
**Output:** Daily transaction ledger for 90 days

### What it does:
1. Start with `current_available_balance`
2. Apply all LLM deltas (cancellations, amendments)
3. Separate events into:
   - **Recurring debits** (rent, utilities, subscriptions) — monthly recurring
   - **Flexible expenses** (stoppable/reducible) — can be changed
   - **Pending debits** — reserve, will happen
   - **Pending credits** — DON'T count until settled
   - **Confirmed income** — salary on settlement date
4. Build daily transaction list:
   - Income: only on actual settlement dates
   - Recurring expenses: monthly, on their dates
   - Pending debits: on their settlement dates
5. Never invent income, expenses, or payment options

### Rules enforced:
- Detect recurrence only when history supports it
- Reserve pending debits
- Don't count pending credits/bonuses/commissions/refunds
- Count confirmed salary on settlement date only
- Balance must never fall below `minimum_balance_to_keep`

---

## Phase 4: 90-Day Deterministic Simulator (`forecaster.py`)

**The core engine. No LLM involvement.**

### `FinancialSimulator`

```python
class FinancialSimulator:
    def __init__(self, starting_balance, min_balance, daily_transactions):
        self.balance = starting_balance
        self.min_balance = min_balance
        self.transactions = daily_transactions  # sorted by date
    
    def simulate(self, start_date, days=90):
        """Returns daily balance array and whether it stays safe."""
        
    def calculate_headroom(self, start_date, days=90):
        """Returns the minimum (balance - min_balance) across all days.
        This is amount_safe_to_pay BEFORE spending changes."""
        
    def find_earliest_safe_date(self, amount, start_date, deadline):
        """First date where paying `amount` keeps balance safe through deadline."""
```

### How `amount_safe_to_pay` is calculated:

```
1. Project baseline 90-day cash flow WITHOUT the requested expense
2. For each day, compute: daily_balance - minimum_balance_to_keep
3. The absolute MINIMUM of these 90 values is the "headroom"
4. amount_safe_to_pay = min(headroom, requested_amount)
```

**Critical:** This is BEFORE any spending changes. Flexible expense reductions are NOT applied here.

### How `earliest_date_for_full_payment` is calculated:

```
For each day from request_date to deadline:
  1. Project balance from request_date to that day
  2. Subtract requested_amount
  3. Check if balance stays above minimum for remaining 90 days
  4. First day where this is true = answer
```

---

## Phase 5: Combinatorial Solver & Tie-Breaker (`plan_generator.py` + `decision.py`)

**Instead of a sequential waterfall, generate ALL candidates and pick the best.**

### Step 1: Generate ALL Candidates

```python
candidates = []

# 1. Full payment (if user considers it)
if "full_payment" in user.payment_preferences:
    candidates.append(FullPaymentPlan(amount=requested_amount, date=request_date))

# 2. Each installment option (if user considers it)
if "installments" in user.payment_preferences:
    for option in payment_options:
        if option.method == "installments":
            if fits_max_months(option, user.max_installment_months):
                candidates.append(InstallmentPlan(option))

# 3. Partial payment (if allowed and user considers it)
if "partial_payment" in user.payment_preferences and allows_partial:
    safe_today = simulator.calculate_headroom()
    if 0 < safe_today < requested_amount:
        remaining = requested_amount - safe_today
        earliest_rest = simulator.find_earliest_safe_date(remaining)
        if earliest_rest <= desired_completion_date:
            candidates.append(PartialPaymentPlan(safe_today, earliest_rest))

# 4. Wait (if user considers full payment)
if "full_payment" in user.payment_preferences:
    earliest = simulator.find_earliest_safe_date(requested_amount)
    if earliest:
        candidates.append(WaitPlan(earliest))

# 5. Spending change permutations
for candidate in candidates:
    if not candidate.is_safe:
        for combo in generate_spending_combos(user.flexible_events, max=3):
            permuted = candidate.apply_spending_changes(combo)
            candidates.append(permuted)
```

### Step 2: Simulate & Filter

```python
safe_plans = []
for plan in candidates:
    result = simulator.simulate(plan.payments)
    if result.is_safe:
        safe_plans.append(plan)
```

### Step 3: Rank by Exact 6-Step Tie-Breaker

```python
def rank_plans(plans):
    return sorted(plans, key=lambda p: (
        0 if p.completes_by_deadline else 1,        # 1. Complete by deadline
        len(p.spending_changes),                      # 2. No spending changes
        p.total_cost,                                 # 3. Minimize total paid
        p.start_date,                                 # 4. Start earlier
        p.num_payments,                               # 5. Fewer payments
        p.lowest_option_id,                           # 6. Lowest payment_option_id
    ))
```

**The plan at index 0 after sorting is mathematically guaranteed to be the optimal choice.**

---

## Phase 6: Output Generation (`main.py`)

### Output schema:
```python
@dataclass
class OutputRow:
    request_id: str
    amount_safe_to_pay: float  # 0 <= x <= requested_amount
    affordability_status: str  # affordable_now | affordable_with_plan | affordable_later | not_affordable
    recommended_payment_method: str  # full_payment | partial_payment | installments | wait | not_recommended
    payment_plan: str  # "YYYY-MM-DD:amount|YYYY-MM-DD:amount" or "none"
    earliest_date_for_full_payment: str  # "YYYY-MM-DD" or ""
    spending_changes_needed: str  # "none" or "stop:event_id|reduce_to:event_id:amount"
    decision_explanation: str  # LLM-generated 1-2 sentence explanation
```

### Validation before writing:
- `0 <= amount_safe_to_pay <= requested_amount`
- `affordability_status` is in allowed set
- `recommended_payment_method` is in allowed set
- `payment_plan` dates are in `YYYY-MM-DD:amount` format
- Installment plans match a supplied payment option
- Spending changes only target flexible recurring events
- Balance stays above minimum throughout 90-day forecast

---

## LLM Usage Summary

| Task | Model | When | Tokens/Request |
|---|---|---|---|
| Image OCR (16 images) | Gemini/Groq Vision | Once, during Phase 2 | ~500 input, ~50 output |
| Message parsing (216 messages) | qwen/qwen3.8-27b | Once, during Phase 2 | ~2000 input, ~200 output |
| Explanation writing | qwen/qwen3.8-27b | Once, during Phase 6 | ~300 input, ~50 output |

**Total estimated:** ~3 LLM calls per request, ~750 calls for 250 requests. All on free tier.

---

## Key Architectural Decisions

| Decision | Rationale |
|---|---|
| Deterministic core | Financial math must be reproducible and verifiable |
| Combinatorial solver | Sequential waterfall misses optimal plans |
| 6-step tie-breaker in code | Hidden test cases check exact compliance |
| amount_safe_to_pay before changes | Directly from §6.2 rules |
| LLM for extraction only | Prevents prompt injection from overriding rules |
| Pandas for data manipulation | Handles 25k events efficiently |
| Pydantic for output validation | Catches format errors before writing CSV |

---

## Interview Preparation

**Expected questions:**

1. **"Why deterministic over LLM?"** — "Financial math must be reproducible. LLMs hallucinate numbers. I used code for the 90-day ledger and LLM only for reading images and writing explanations."

2. **"How did you handle prompt injection?"** — "The LLM never makes decisions. It only extracts data into JSON. Images are untrusted — I parse them into amounts, never follow their instructions."

3. **"How did you pick the best plan?"** — "I generate ALL valid candidates, simulate each through the 90-day forecaster, discard unsafe ones, then sort survivors by the exact 6-step tie-breaker from the rules."

4. **"What about currency conversion?"** — "I convert all amounts to home_currency on the event's settlement date using the provided exchange_rates.csv. No live rates needed."

5. **"What would you improve with more time?"** — "Better VLM accuracy on handwritten amounts, confidence scoring on borderline cases, and caching exchange rate lookups for performance."

---

## Development Timeline

| Phase | Time | Deliverable |
|---|---|---|
| Core engine (forecaster + solver) | 4-5 hours | Works for 80%+ cases |
| Data loader + financial state | 2-3 hours | Handles all CSVs + currency |
| LLM extraction (images + messages) | 1-2 hours | Handles blank amounts |
| Decision ranking + tie-breaker | 1-2 hours | Exact rule compliance |
| Test against samples + debug | 2-3 hours | Validate format + accuracy |
| Code packaging + usage report | 1 hour | submission-ready |
| **Total** | **~12 hours** | **Within 24h deadline** |
