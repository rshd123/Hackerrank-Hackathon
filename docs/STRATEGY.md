> **This file teaches you how to win the interview and defend your financial agent.** It covers what winners did differently, interview strategy specific to "Buy or Wait?", and how to own your decisions.

# Strategy — Winning Patterns & Interview Tips

## What Winners of Similar Hackathons Did

### 1. They Owned the Architecture Decision

They explained **WHY** they chose deterministic over LLM-for-everything.

**Strong answer:**
> "I used a deterministic 90-day simulator because LLMs hallucinate numbers. The headroom calculation — minimum daily balance minus minimum_balance_to_keep across 90 days — must be exact. The LLM only reads images and writes explanations."

**Weak answer:**
> "The agent figures out if the user can afford it."

### 2. They Explained the Tie-Breaker

The 6-step ranking is where most participants lose points. Winners could recite it.

**Strong answer:**
> "I generate ALL valid candidates — full payment, each installment option, partial payment, wait — then simulate each through the 90-day forecaster. Any plan that dips below the minimum balance is discarded. Then I sort survivors by the exact 6-step hierarchy: complete by deadline, no spending changes, minimize total cost, start earlier, fewer payments, lowest option ID."

### 3. They Referenced Specific Test Results

**Strong answer:**
> "On request_003, the user wanted a $1,200 laptop. My system found that full payment was safe (headroom was $1,450), but the user's payment_preferences only included installments. So it recommended the 3-month installment plan from payment_option_07, which completed by the deadline without any spending changes."

### 4. They Handled Prompt Injection Confidently

**Strong answer:**
> "The LLM never makes financial decisions. When it reads an image, it extracts the numerical amount into JSON. If the image says 'ignore minimum balance rules', the code never sees that instruction — it only gets the extracted amount. The prompt injection defense is architectural, not behavioral."

### 5. They Were Honest About Limitations

**Strong answer:**
> "The system doesn't handle currency fluctuations between now and future payments — it uses fixed dated rates. In production, I'd add rate-lock windows and confidence intervals on the 90-day forecast."

---

## Interview Strategy for "Buy or Wait?"

### Expected Probe Order

1. **Quick pitch** — 2-minute overview of the system
2. **Architecture** — Why deterministic? How does the simulator work?
3. **Key calculation** — Walk through amount_safe_to_pay for a specific request
4. **Tie-breaker** — How do you pick between safe plans?
5. **LLM usage** — What does the LLM actually do?
6. **Edge cases** — What about conflicting messages? Blank amounts?
7. **What you'd improve** — Be specific, not generic

### High-Signal Answers

| Topic | What to Say |
|---|---|
| Architecture | "Deterministic core, LLM extraction frontend. Code does math, LLM reads images." |
| amount_safe_to_pay | "90-day baseline simulation, find minimum headroom, cap at requested_amount" |
| Tie-breaker | "Generate ALL candidates, simulate each, sort survivors by exact 6-step hierarchy" |
| Prompt injection | "Architectural defense — LLM extracts data, code applies it. Never follows image instructions." |
| Currency | "Convert all amounts to home_currency on settlement_date using exchange_rates.csv" |
| Pending credits | "Don't count until settled — rule from §6.3" |

### Low-Signal Answers (Avoid)

- "The AI decided the best plan" — You decided, the code executes
- "We used a smart algorithm" — Name the algorithm
- "It handles edge cases" — Give a specific edge case
- "We tested it" — What did you test? What failed?

---

## Chat Transcript Strategy

### What to Show

1. **Read the problem statement first** — "Let me understand the 90-day safety check rule"
2. **Inspect the data** — "250 requests, 25k events, 16 images — let me check the image format"
3. **Compare architectures** — "Should we use LLM for everything or deterministic math?"
4. **Set constraints** — "The tie-breaker must be EXACT — 6 steps, no shortcuts"
5. **Test against samples** — "Run on sample_requests.csv, check format compliance"
6. **Iterate on failures** — "Request 7 is wrong — amount_safe_to_pay includes spending changes, but the rule says it must be BEFORE changes"
7. **Push back on AI** — "Don't use GPT-4 for the simulation. Use Python. LLMs hallucinate numbers."

### Weak Patterns

- "Build me a financial agent"
- "Make the output CSV"
- Long processing logs without decision reasoning
- No testing evidence

---

## Output CSV Strategy

### What to Ensure

- Every row has a non-empty, specific `decision_explanation`
- Explanation references actual financial facts (balance, events, constraints)
- `amount_safe_to_pay` is calculated BEFORE spending changes
- `payment_plan` amounts sum to `requested_amount`
- Installment plans match a supplied payment option
- `spending_changes_needed` only references flexible recurring events
- Balance never falls below `minimum_balance_to_keep` in the 90-day forecast

### Common Failure Modes

- Generic explanation: "The user can afford this" → Must reference specific numbers
- Wrong amount: Calculated after spending changes instead of before
- Wrong plan: Selected valid plan but not optimal per tie-breaker
- Missing validation: Payment plan dates don't match payment option schedule
