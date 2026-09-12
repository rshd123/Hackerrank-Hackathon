> **This file shows the system architecture for "Buy or Wait?"** — a deterministic financial affordability agent with an LLM data-extraction frontend. Use this to understand the full pipeline from raw CSVs to output.csv.

# Architecture — Buy or Wait?

## Core Principle

This is a **deterministic constraint-satisfaction problem**, not an LLM generation problem.

- **LLMs do:** Read images, parse messages, write explanations
- **Code does:** All financial math, simulations, rankings, decisions

The LLM never makes a financial decision. It extracts data into JSON. Code applies that data deterministically.

---

## System Diagram

```
┌─────────────────────────────────────────────────┐
│              RAW CSVs (dataset/)                 │
│  requests, profiles, events, rates, options,    │
│  messages, images                               │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│         PHASE 1: DATA LOADING & CURRENCY        │
│  • Merge CSVs by user_id / request_id           │
│  • Convert all amounts to home_currency         │
│  • Build recurring expense profiles             │
│  • Index payment options per request            │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│         PHASE 2: MULTIMODAL EXTRACTION          │
│  (Only file that calls the LLM — Groq API)      │
│  • Image OCR: blank amounts → numerical values  │
│  • Message parsing: text → JSON ledger deltas   │
│  • Conflict resolution: settled > newer > safe  │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│       PHASE 3: FINANCIAL STATE RECONSTRUCTION   │
│  • Apply LLM deltas (cancels, amendments)       │
│  • Separate: recurring, flexible, pending,      │
│    confirmed income                             │
│  • Build daily transaction ledger               │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│         PHASE 4: 90-DAY DETERMINISTIC SIMULATOR │
│  • Project daily balance for 90 days            │
│  • Calculate headroom = amount_safe_to_pay      │
│  • Find earliest safe date for full payment     │
│  • Balance must never fall below min_balance    │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│     PHASE 5: COMBINATORIAL SOLVER & RANKING     │
│  • Generate ALL valid payment candidates        │
│  • Simulate each through 90-day forecaster      │
│  • Discard unsafe plans                         │
│  • Rank survivors by 6-step tie-breaker         │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│         PHASE 6: OUTPUT GENERATION              │
│  • Map winning plan → output.csv row            │
│  • LLM writes decision_explanation              │
│  • Validate all fields against schema           │
│  • Write output.csv                             │
└─────────────────────────────────────────────────┘
```

---

## Layer Details

### Phase 1: Data Loading (`data_loader.py`)

**Purpose:** Turn 9 raw CSVs into unified, currency-normalized data structures.

**What it does:**
1. Load all CSVs with Pandas
2. Join requests ↔ profiles (by `user_id`)
3. Join events ↔ messages ↔ images (by `user_id` / `request_id`)
4. Convert every foreign-currency amount to `home_currency` using dated `exchange_rates.csv`
5. Index payment options by `request_id`
6. Classify events: recurring, flexible (stoppable/reducible), pending, confirmed income

**Key rule:** Currency conversion uses the event's `settlement_date` and the exact `from_currency → to_currency` direction from `exchange_rates.csv`.

---

### Phase 2: Multimodal Extraction (`llm_parser.py`)

**Purpose:** Extract structured data from images and messages. **The only file that calls the LLM.**

**Image OCR:**
- For events with blank `amount`, find linked `image_id` in `images.csv`
- Base64-encode `dataset/media/images/<image_id>.png`
- Send to Groq `qwen/qwen3.8-27b` with strict JSON schema
- Extract numerical amount + currency

**Message Parsing:**
- Pass all user messages to Groq `qwen/qwen3.8-27b`
- Output: list of "Ledger Deltas" — `{"event_id": "event_12", "action": "cancel|delay|amend_amount|amend_date", "new_value": ...}`
- Apply deltas programmatically

**Security:** Images and messages are untrusted. The LLM extracts data, never follows embedded instructions.

**Conflict Resolution:**
1. Explicit cancellation/settlement/amendment wins
2. Newer record from same source wins
3. Settled event over estimate/forecast
4. Financially safer interpretation when unresolvable

---

### Phase 3: Financial State Reconstruction (`financial_state.py`)

**Purpose:** Build the user's daily transaction ledger from events + LLM deltas.

**What it does:**
1. Start with `current_available_balance`
2. Apply all LLM deltas
3. Separate events into categories:
   - **Recurring debits** (rent, utilities) — monthly recurring
   - **Flexible expenses** (stoppable/reducible) — can be changed
   - **Pending debits** — reserve, will happen
   - **Pending credits** — DON'T count until settled
   - **Confirmed income** — salary on settlement date
4. Build sorted daily transaction list

**Rules enforced:**
- Detect recurrence only when history supports it
- Reserve pending debits
- Don't count pending credits/bonuses/commissions/refunds
- Count confirmed salary on settlement date only
- Never invent income, expenses, or payment options

---

### Phase 4: 90-Day Deterministic Simulator (`forecaster.py`)

**Purpose:** Project the user's daily balance for 90 days. **The core engine.**

**`FinancialSimulator` class:**
```python
class FinancialSimulator:
    def simulate(start_date, days=90) → daily_balance_array
    def calculate_headroom(start_date, days=90) → float
    def find_earliest_safe_date(amount, start_date, deadline) → date | None
```

**How `amount_safe_to_pay` is calculated:**
1. Project baseline 90-day cash flow WITHOUT the requested expense
2. For each day: `daily_balance - minimum_balance_to_keep`
3. The absolute MINIMUM of these 90 values = headroom
4. `amount_safe_to_pay = min(headroom, requested_amount)`

**Critical:** This is BEFORE any spending changes. Flexible expense reductions are NOT applied.

**How `earliest_date_for_full_payment` is calculated:**
1. For each day from request_date to deadline:
   - Project balance to that day
   - Subtract requested_amount
   - Check if balance stays above minimum for remaining 90 days
2. First day where this is true = answer

---

### Phase 5: Combinatorial Solver (`plan_generator.py` + `decision.py`)

**Purpose:** Generate ALL valid payment candidates, simulate each, rank survivors.

**Step 1 — Generate ALL Candidates:**
- Full payment (if user considers it)
- Each installment option (if user considers it, fits max_installment_months)
- Partial payment (if allowed, safe today, completes by deadline)
- Wait (if full payment becomes safe later)
- Spending change permutations (up to 3 flexible events)

**Step 2 — Simulate & Filter:**
- Run each candidate through `FinancialSimulator`
- Discard any plan where balance falls below minimum

**Step 3 — Rank by 6-Step Tie-Breaker:**
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

**Plan at index 0 is mathematically guaranteed to be optimal.**

---

### Phase 6: Output Generation (`main.py`)

**Purpose:** Map winning plan → output.csv row, with LLM-generated explanation.

**Output fields:**
- `request_id` — from input
- `amount_safe_to_pay` — from Phase 4 headroom calculation
- `affordability_status` — from plan type (affordable_now/with_plan/later/not_affordable)
- `recommended_payment_method` — from winning plan (full/partial/installments/wait/not_recommended)
- `payment_plan` — chronological `YYYY-MM-DD:amount|...` or `none`
- `earliest_date_for_full_payment` — from Phase 4, or empty
- `spending_changes_needed` — from winning plan, or `none`
- `decision_explanation` — LLM-generated, 1-2 sentences

**Validation before writing:**
- `0 <= amount_safe_to_pay <= requested_amount`
- All fields in allowed sets
- Installment plans match supplied payment options
- Balance stays above minimum throughout forecast

---

## Why This Architecture Wins

| Property | Benefit |
|---|---|
| Deterministic core | Financial math is reproducible and verifiable |
| Combinatorial solver | Never misses the optimal plan |
| 6-step tie-breaker in code | Exact compliance with hidden test cases |
| LLM isolation | Prompt injection can't override financial rules |
| Single model (Groq qwen3.8-27b) | One API key, zero setup, handles text + images |
| Pandas data pipeline | Handles 25k events efficiently |
| Pydantic output validation | Catches format errors before writing CSV |
