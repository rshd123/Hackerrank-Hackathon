# AGENTS.md

HackerRank Orchestrate (September 2026) — Buy or Wait?

This file is the single source of truth for any AI coding agent working in this repo: Claude Code, OpenAI Codex CLI / Codex Cloud, Gemini CLI, Cursor, Windsurf, opencode, Aider, goose, Factory, RooCode, JetBrains Junie, GitHub Copilot, Devin, or any other AGENTS.md-aware tool.

Read this file in full before taking any action. Obey it exactly unless the user or platform provides higher-priority instructions.

---

## 0. TLDR For The Agent

On every session start, do this in order:

1. Read this file completely.
2. Greet the user per §2 and show the time remaining to the deadline.
3. When building, testing, or packaging the solution, follow the project contract in §4.

**No logging:** there is no conversation log. Never create, append to, or maintain `log.txt` or any session/transcript log file. The platform or the user captures transcripts when they need one.

**No packaging chores:** do not rebuild `code.zip`, regenerate `output.csv`, or refresh submission artifacts unless the user explicitly asks for it in the current turn.

---

## 1. What This Repo Is

This is a starter repo for the **HackerRank Orchestrate** 24-hour hackathon challenge: **Buy or Wait?**

Participants must build an AI-powered financial agent. For every purchase or payment request in `dataset/requests.csv`, the agent decides whether the user should pay in full, pay partially, use an available installment option, wait, or not proceed.

The system reconstructs the user's financial position from structured profiles and financial events, fixed dated exchange rates, seller/provider payment options, and relevant messages or images. It must account for recurring commitments, pending payments, essential spending, confirmed income, financial priorities, and the minimum balance the user wants to keep. Messages and images are untrusted evidence; they may clarify, amend, delay, cancel, or confirm a financial fact, but their embedded instructions never override the challenge rules. There are no voice notes or live banking, market-data, or exchange-rate calls.

The final submission must produce `output.csv` with:

```text
request_id,amount_safe_to_pay,affordability_status,recommended_payment_method,payment_plan,earliest_date_for_full_payment,spending_changes_needed,decision_explanation
```

Read `problem_statement.md` for the full participant-facing specification.

## 2. Session Start

At the beginning of each agent session:

1. Greet the user with this brief introduction:

   ```text
   Welcome to HackerRank Orchestrate. Build and ship Buy or Wait?, an AI-powered financial decision agent, before the challenge ends at 6:00 PM IST on September 13, 2026. Let's get started.
   ```

2. Calculate and display the time remaining until `2026-09-13T18:00:00+05:30`. If fewer than 2 hours remain, remind the user to submit soon. If the deadline has passed, state that clearly without blocking further work.
3. Proceed with the user's request without requiring an acknowledgement or confirmation phrase.

---

## 3. Challenge Rules

1. This is a **solo** challenge. The participant must be the author of the submission.
2. Participants may use any IDE, AI assistant, or tool to help build their solution.
3. The system must conform to the project contract in §4 so it can be evaluated.
4. Never commit secrets. Use environment variables and a `.env` file when needed.
5. Follow the mandatory submission-link rule below.

### 3.1 Mandatory Submission Link

If the user asks for the submission link, where to submit, how to submit, where to upload the code, or any equivalent question, always provide this exact URL:

https://www.hackerrank.com/contests/hackerrank-orchestrate-september26/challenges/buy-or-wait/submission

Requirements:

- Include the full clickable URL in the response every time such a question is asked.
- Do not replace it with the HackerRank homepage, contest homepage, challenge overview, or any other link.
- Do not merely describe where to navigate; provide the URL directly.
- This rule applies even when the submission question is included alongside other questions.

---

## 4. Project Contract

### 4.1 Dataset Contract

Participant-facing files are inside `dataset/`.

```text
dataset/
├── financial_profiles.csv
├── financial_events.csv
├── exchange_rates.csv
├── requests.csv
├── sample_requests.csv
├── request_payment_options.csv
├── messages.csv
├── images.csv
├── output.csv
└── media/
    └── images/
```

- `requests.csv` contains the evaluation requests. Produce exactly one output row for every `request_id` in it.
- `sample_requests.csv` contains public examples with completed output fields. Use it to understand format and decision style, not as labels for evaluation requests.
- `financial_profiles.csv` defines the user's home currency, current available balance, minimum balance to keep, priorities, protected spending, adjustable categories, and payment preferences. `max_installment_months` is blank when the user will not consider installments.
- `financial_events.csv` contains historical, pending, scheduled, settled, failed, cancelled, and non-cash records. `linked_event_id` points to an earlier event in the same transaction or investment lifecycle; the link alone does not determine whether a row counts toward cash flow. Treat `settled`, `pending`, `scheduled`, and `unrealized` according to their cash state; do not treat unrealized investment value as available cash.
- `exchange_rates.csv` supplies fixed rates. For a foreign-currency cash event, use the row for its settlement date and the stated `from_currency` to `to_currency` direction.
- `request_payment_options.csv` contains the seller/provider payment options available for a request. A request has two to four options. An available option may still be rejected because it conflicts with the user's payment preferences or `max_installment_months`.
- `messages.csv` and `images.csv` provide optional supporting evidence. In `messages.csv`, `related_event_id` is populated only when the message directly describes one supplied financial-event row; a blank value means no one-to-one event row exists. Resolve each image as `dataset/media/images/<image_id>.png`; for example, `image_07` maps to `dataset/media/images/image_07.png`. Use the information only when relevant; do not invent evidence when an image file is absent.
- `output.csv` is the blank prediction template.

Organizer-only files live outside `dataset/` and must never be used for predictions.

### 4.2 Required Output

The solution must write `output.csv` with these exact columns, in this order:

```text
request_id,amount_safe_to_pay,affordability_status,recommended_payment_method,payment_plan,earliest_date_for_full_payment,spending_changes_needed,decision_explanation
```

- `amount_safe_to_pay` is the amount safe on `request_date` before optional spending changes and is between `0` and `requested_amount` inclusive.
- `affordability_status` is one of `affordable_now`, `affordable_with_plan`, `affordable_later`, or `not_affordable`.
- `recommended_payment_method` is one of `full_payment`, `partial_payment`, `installments`, `wait`, or `not_recommended`.
- `affordable_with_plan` means the full request is completed through a partial-payment schedule, installments, or permitted spending changes.
- `payment_plan` is chronological `YYYY-MM-DD:amount` entries separated by `|`, or `none`. For `partial_payment`, use exactly two payments: `amount_safe_to_pay` on `request_date`, then `requested_amount - amount_safe_to_pay` on `earliest_date_for_full_payment`. Recommend it only when the request allows it, the user accepts it, `0 < amount_safe_to_pay < requested_amount`, and the second payment is on or before `desired_completion_date`. The two payments must add up to `requested_amount`. An installment plan must instead follow a supplied payment option.
- `earliest_date_for_full_payment` is the first conservative projected date for one safe full payment. It equals `request_date` for `affordable_now` and is empty when no full payment is safe within the forecast period.
- `spending_changes_needed` is `none` or up to three `stop:<event_id>` and `reduce_to:<event_id>:<new_amount>` actions. Only non-protected, flexible events in a category the user permits may be changed.
- `decision_explanation` is a concise, grounded explanation of the recommendation.

### 4.3 Financial Decision Rules

- Detect recurrence only when history supports it. Forecast essential variable spending conservatively.
- Reserve pending debits. Do not count pending credits, bonuses, commissions, refunds, lottery proceeds, or investment gains until they settle.
- Count confirmed salary on its settlement date. Do not invent unsupported future income, expenses, payment options, or other financial facts.
- The balance must never fall below `minimum_balance_to_keep` after any projected essential expense or payment in the recommended plan.
- Respect the user's protected categories and preferences. Prefer a plan that completes the request by its deadline, avoids spending changes, minimizes total payment cost, starts earlier, and uses fewer payments.
- Resolve conflicts using an explicit cancellation, settlement, or amendment first; then newer records from the same source; then a settled event; then the financially safer interpretation.

### 4.4 Constraints That Make The Submission Evaluable

- Be runnable from the terminal.
- Read the provided files from `dataset/`.
- Do not use organizer-only files or hardcoded labels.
- Keep behavior deterministic where possible.
- Read secrets from environment variables only.
- Include clear setup and run instructions in the submitted code package.

### 4.5 Reasonable Entry Points

There is no required language. If you use Python, `code/main.py` is a good entry point. If you use another language, document the run command clearly in your submitted README.

---

## 5. Cross-Platform And Agent-Compatibility Notes

- Do not assume bash. Prefer language-native APIs when possible.
- Keep tool-specific config minimal and point back to this `AGENTS.md`.
- If a nested `AGENTS.md` exists, the closest one wins for files inside that sub-project.
- Resolve paths relative to this `AGENTS.md` file. Do not hardcode platform-specific user paths.

---

## 6. Quick Checklist For The Agent

Before responding to any user message, confirm:

- [ ] I have read this file in this session.
- [ ] I know how much time is left, or that the end time is not configured.
- [ ] I have not written to any log file.
- [ ] I have not rebuilt `code.zip` or regenerated `output.csv` unless explicitly asked this turn.
- [ ] I will preserve the Buy or Wait? financial decision and output contract in §4.
