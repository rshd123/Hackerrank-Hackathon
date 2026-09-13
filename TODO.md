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

- [x] Create `code/data_loader.py`
- [x] Define data structures: `Request`, `UserProfile`, `FinancialEvent`, `PaymentOption`
- [x] Implement `DataLoader.__init__(dataset_path)`
- [x] Implement `load_requests()` → 250 rows
- [x] Implement `load_profiles()` → dict by user_id
- [x] Implement `load_events(user_id)` → list of FinancialEvent
- [x] Implement `load_payment_options(request_id)` → list of PaymentOption
- [x] Implement `load_exchange_rates()` → index by (date, from, to)
- [x] Implement `convert_currency(amount, from_cur, to_cur, date)` → float
- [x] Implement `load_messages(request_id)` → list of Message
- [x] Implement `load_images(request_id)` → list of Image (paths)
- [x] Test: load all data, verify row counts match expected
- [x] Test: currency conversion matches manual calculation

**Done when:** `python -c "from code.data_loader import DataLoader; d = DataLoader('dataset/'); print(len(d.load_requests()), 'requests loaded')"` prints 250.

---

## Phase 2: Financial State (`code/financial_state.py`)

**Goal:** Reconstruct user's daily ledger from events.

- [x] Create `code/financial_state.py`
- [x] Define `LedgerDelta` dataclass (event_id, action, new_value)
- [x] Define `DailyLedger` dataclass (list of daily balances)
- [x] Implement `FinancialState.__init__(profile, events)`
- [x] Implement `apply_deltas(deltas)` → modifies events in-place
- [x] Implement `resolve_conflicts(events)` → filtered events
- [x] Implement `classify_events()` → recurring, flexible, pending, confirmed
- [x] Implement `build_daily_ledger(start_date, days=90)` → DailyLedger
- [x] Implement `get_recurring_expenses()` → list
- [x] Implement `get_flexible_events()` → list
- [x] Test: pending credits excluded from ledger
- [x] Test: recurring events appear monthly
- [x] Test: balance starts at current_balance

**Done when:** Build a ledger for any user and verify daily balances are correct by manual inspection.

---

## Phase 3: 90-Day Simulator (`code/forecaster.py`)

**Goal:** Project daily balance, calculate headroom, find safe dates.

- [x] Create `code/forecaster.py`
- [x] Define `ForecastResult` dataclass (safe, daily_balances)
- [x] Implement `Forecaster.__init__(state, request)`
- [x] Implement `calculate_headroom()` → float
- [x] Implement `find_earliest_full_payment_date()` → date | None
- [x] Implement `test_full_payment_now()` → PaymentScenario
- [x] Implement `test_installment_option()` → PaymentScenario
- [x] Implement `test_partial_payment()` → PaymentScenario
- [x] Test: headroom = min(balance - min_balance) across 90 days
- [x] Test: headroom capped at requested_amount
- [x] Test: earliest_date is first day where full payment is safe
- [x] Test: balance never falls below min_balance in safe simulations

**Done when:** For sample request_001, headroom and earliest_date match manual calculation.

---

## Phase 4: Combinatorial Solver (`code/plan_generator.py` + `code/decision.py`)

**Goal:** Generate ALL candidates, simulate, rank, return optimal.

- [x] Create `code/plan_generator.py`
- [x] Define `CandidatePlan` base class (payments, spending_changes, total_cost, etc.)
- [x] Define `FullPaymentPlan`, `InstallmentPlan`, `PartialPaymentPlan`, `WaitPlan`
- [x] Implement `CombinatorialSolver.__init__(simulator, request, options, profile)`
- [x] Implement `generate_all_candidates()` → list[CandidatePlan]
- [x] Implement `generate_spending_combos(max_changes=3)` → list of combos
- [x] Create `code/decision.py`
- [x] Implement `rank_plans(plans)` → sorted by 6-step tie-breaker
- [x] Implement `find_optimal_plan()` → CandidatePlan
- [x] Test: generates candidates for all payment methods user considers
- [x] Test: unsafe plans are filtered out
- [x] Test: ranked order matches exact tie-breaker hierarchy
- [x] Test: on sample_requests.csv, optimal plan matches expected

**Done when:** For all 25 sample requests, `find_optimal_plan()` returns a safe plan.

---

## Phase 5: LLM Parser (`code/llm_parser.py`)

**Goal:** Extract amounts from images, parse messages into deltas.

- [x] Create `code/llm_parser.py`
- [x] Define `LLMParser.__init__(api_key)`
- [x] Implement `extract_amount_from_image(image_path)` → float
- [x] Implement `parse_messages(messages)` → list[LedgerDelta]
- [x] Implement `extract_request_info(request_text)` → dict
- [x] Implement base64 encoding for images
- [x] Implement JSON parsing with code block handling
- [x] Test: message cancel delta
- [x] Test: message amend_amount with clean numeric extraction
- [x] Test: message amend_date
- [x] Test: no-delta message returns empty
- [x] Test: request text parsing
- [x] Test: batch message parsing

**Done when:** Can extract a numerical amount from image_07.png via Groq API.

---

## Phase 6: Main Pipeline (`code/main.py`)

**Goal:** Orchestrate everything, write output.csv.

- [x] Create `code/main.py`
- [x] Implement `process_request()` → Decision
- [x] Implement `decision_to_row()` → dict
- [x] Implement `main()` → loads data, processes 250 requests, writes CSV
- [x] LLM parser integration (optional, --no-llm flag)
- [x] Run against all 250 requests → no crashes
- [x] Verify output.csv has 250 rows, correct columns
- [x] Verify status distribution: 104 affordable_now, 101 affordable_with_plan, 45 not_affordable
- [x] Verify amount_safe_to_pay is between 0 and requested_amount

**Done when:** `python code/main.py` produces a valid `output.csv` with 250 rows.

---

## Phase 7: Test, Debug, Package

**Goal:** Validate against samples, fix issues, create submission artifacts.

- [x] Run stress test: 2762 assertions, all pass
- [x] Error handling: fallback to not_recommended on any exception
- [x] LLM timeout handling: --no-llm flag, graceful degradation
- [x] Verify output.csv: 250 rows, 8 columns, no NaN in required fields
- [x] Verify status distribution: 104 affordable_now, 101 with_plan, 45 not_affordable
- [x] Create `code.zip` (10 files, 20KB)
- [x] Write `code/README.md` with setup + run instructions
- [x] Write `code/evaluation/usage_report.md` with token tracking
- [x] Verify `log.txt`: 459 lines, complete conversation history
- [x] Final run: `python code/main.py --no-llm` -> output.csv validated

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
