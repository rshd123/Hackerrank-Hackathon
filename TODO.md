> **This is the execution checklist.** Follow this phase by phase. Each task has a checkbox, clear deliverable, and acceptance criteria. Check off as you complete.

# TODO — Build Checklist

## Before You Start

- [ ] Read `problem_statement.md` in full
- [ ] Read `docs/SOLUTION.md` (architecture)
- [ ] Read `docs/IMPLEMENTATION.md` (design specs)
- [ ] Read `docs/DECISIONS.md` (decisions to defend in interview)
- [ ] Verify `.env` has `GROQ_API_KEY`
- [ ] Verify `pip install -r requirements.txt` works
- [ ] Verify all dataset files exist and are readable

---

## Phase 1: Data Loader (`code/data_loader.py`)

**Goal:** Load all CSVs, join them, convert currencies.

- [ ] Create `code/data_loader.py`
- [ ] Define data structures: `Request`, `UserProfile`, `FinancialEvent`, `PaymentOption`
- [ ] Implement `DataLoader.__init__(dataset_path)`
- [ ] Implement `load_requests()` → 250 rows
- [ ] Implement `load_profiles()` → dict by user_id
- [ ] Implement `load_events(user_id)` → list of FinancialEvent
- [ ] Implement `load_payment_options(request_id)` → list of PaymentOption
- [ ] Implement `load_exchange_rates()` → index by (date, from, to)
- [ ] Implement `convert_currency(amount, from_cur, to_cur, date)` → float
- [ ] Implement `load_messages(request_id)` → list of Message
- [ ] Implement `load_images(request_id)` → list of Image (paths)
- [ ] Test: load all data, verify row counts match expected
- [ ] Test: currency conversion matches manual calculation

**Done when:** `python -c "from code.data_loader import DataLoader; d = DataLoader('dataset/'); print(len(d.load_requests()), 'requests loaded')"` prints 250.

---

## Phase 2: Financial State (`code/financial_state.py`)

**Goal:** Reconstruct user's daily ledger from events.

- [ ] Create `code/financial_state.py`
- [ ] Define `LedgerDelta` dataclass (event_id, action, new_value)
- [ ] Define `DailyLedger` dataclass (list of daily balances)
- [ ] Implement `FinancialState.__init__(profile, events)`
- [ ] Implement `apply_deltas(deltas)` → modifies events in-place
- [ ] Implement `resolve_conflicts(events)` → filtered events
- [ ] Implement `classify_events()` → recurring, flexible, pending, confirmed
- [ ] Implement `build_daily_ledger(start_date, days=90)` → DailyLedger
- [ ] Implement `get_recurring_expenses()` → list
- [ ] Implement `get_flexible_events()` → list
- [ ] Test: pending credits excluded from ledger
- [ ] Test: recurring events appear monthly
- [ ] Test: balance starts at current_balance

**Done when:** Build a ledger for any user and verify daily balances are correct by manual inspection.

---

## Phase 3: 90-Day Simulator (`code/forecaster.py`)

**Goal:** Project daily balance, calculate headroom, find safe dates.

- [ ] Create `code/forecaster.py`
- [ ] Define `SimulationResult` dataclass (safe, daily_balances)
- [ ] Implement `FinancialSimulator.__init__(starting_balance, min_balance, transactions)`
- [ ] Implement `simulate(start_date, extra_payments=None)` → SimulationResult
- [ ] Implement `calculate_headroom(start_date, days=90)` → float
- [ ] Implement `find_earliest_safe_date(amount, start_date, deadline)` → date | None
- [ ] Implement `can_afford(payment)` → bool
- [ ] Test: headroom = min(balance - min_balance) across 90 days
- [ ] Test: headroom capped at requested_amount
- [ ] Test: earliest_date is first day where full payment is safe
- [ ] Test: balance never falls below min_balance in safe simulations

**Done when:** For sample request_001, headroom and earliest_date match manual calculation.

---

## Phase 4: Combinatorial Solver (`code/plan_generator.py` + `code/decision.py`)

**Goal:** Generate ALL candidates, simulate, rank, return optimal.

- [ ] Create `code/plan_generator.py`
- [ ] Define `CandidatePlan` base class (payments, spending_changes, total_cost, etc.)
- [ ] Define `FullPaymentPlan`, `InstallmentPlan`, `PartialPaymentPlan`, `WaitPlan`
- [ ] Implement `CombinatorialSolver.__init__(simulator, request, options, profile)`
- [ ] Implement `generate_all_candidates()` → list[CandidatePlan]
- [ ] Implement `generate_spending_combos(max_changes=3)` → list of combos
- [ ] Create `code/decision.py`
- [ ] Implement `rank_plans(plans)` → sorted by 6-step tie-breaker
- [ ] Implement `find_optimal_plan()` → CandidatePlan
- [ ] Test: generates candidates for all payment methods user considers
- [ ] Test: unsafe plans are filtered out
- [ ] Test: ranked order matches exact tie-breaker hierarchy
- [ ] Test: on sample_requests.csv, optimal plan matches expected

**Done when:** For all 25 sample requests, `find_optimal_plan()` returns a safe plan.

---

## Phase 5: LLM Parser (`code/llm_parser.py`)

**Goal:** Extract amounts from images, parse messages into deltas.

- [ ] Create `code/llm_parser.py`
- [ ] Define `LLMParser.__init__(api_key)`
- [ ] Implement `extract_amount_from_image(image_path)` → float
- [ ] Implement `parse_messages(messages)` → list[LedgerDelta]
- [ ] Implement `extract_all_deltas(events, request)` → list[LedgerDelta]
- [ ] Implement base64 encoding for images
- [ ] Implement JSON schema enforcement (response_format)
- [ ] Test: extract amounts from all 16 images → verify numeric
- [ ] Test: parse sample messages → verify delta format
- [ ] Test: Groq API call works with test image

**Done when:** Can extract a numerical amount from image_07.png via Groq API.

---

## Phase 6: Main Pipeline (`code/main.py`)

**Goal:** Orchestrate everything, write output.csv.

- [ ] Create `code/main.py`
- [ ] Implement `build_output_row(request, plan, simulator, parser)` → dict
- [ ] Implement `write_output_csv(rows, path)` → writes CSV
- [ ] Implement `validate_output(df)` → checks all constraints
- [ ] Wire up full pipeline: load → state → extract → simulate → solve → output
- [ ] Run against all 250 requests → verify no crashes
- [ ] Verify output.csv has 250 rows, correct columns
- [ ] Verify `amount_safe_to_pay` is between 0 and requested_amount for all rows
- [ ] Verify no balance dips below min_balance in any recommended plan

**Done when:** `python code/main.py` produces a valid `output.csv` with 250 rows.

---

## Phase 7: Test, Debug, Package

**Goal:** Validate against samples, fix issues, create submission artifacts.

- [ ] Run against 25 sample requests → compare with sample_requests.csv
- [ ] Debug mismatches → update rules in forecaster/solver
- [ ] Verify all 25 sample affordability_status values match
- [ ] Verify all 25 sample recommended_payment_method values match
- [ ] Verify payment_plan format is correct (YYYY-MM-DD:amount|...)
- [ ] Verify spending_changes_needed format is correct
- [ ] Verify decision_explanation is non-empty and specific
- [ ] Create `code.zip` (code/ directory + README.md + evaluation/)
- [ ] Write `code/README.md` with setup + run instructions
- [ ] Write `code/evaluation/usage_report.md` with token tracking
- [ ] Verify `log.txt` has complete conversation history
- [ ] Final run: `python code/main.py` → output.csv → validate

**Done when:** All 3 submission artifacts exist: `output.csv`, `code.zip`, `log.txt`.

---

## Post-Submission

- [ ] Verify submission uploaded to HackerRank
- [ ] Prepare for 30-minute AI judge interview
- [ ] Review `docs/STRATEGY.md` for interview tips
- [ ] Review `docs/DECISIONS.md` for decisions to defend
- [ ] Practice explaining: amount_safe_to_pay, tie-breaker, prompt injection defense

---

## Time Tracker

| Phase | Started | Completed | Hours |
|---|---|---|---|
| Phase 1: Data Loader | | | |
| Phase 2: Financial State | | | |
| Phase 3: Forecaster | | | |
| Phase 4: Solver | | | |
| Phase 5: LLM Parser | | | |
| Phase 6: Main Pipeline | | | |
| Phase 7: Test + Package | | | |
| **Total** | | | |
