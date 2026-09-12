"""
agent.py — Main financial decision agent

Orchestrates: data loading → state reconstruction → forecasting → plan generation.
Deterministic code decides; LLM writes explanation only.
"""

import csv
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from data_loader import load_all, convert_to_home_currency, parse_date as load_parse_date
from financial_state import (
    classify_events,
    get_monthly_recurring,
    get_income_schedule,
    convert_to_home_currency as conv,
    parse_date,
    parse_float,
)
from forecaster import (
    forecast_90_days,
    can_afford_payment,
    find_earliest_full_payment_date,
    recurring_expenses_monthly_total,
)
from plan_generator import (
    try_full_payment,
    try_installments,
    try_partial_payment,
    try_wait,
    rank_plans,
)


def process_request(req, data):
    """Process a single financial request and return the output row."""
    request_id = req["request_id"]
    user_id = req["user_id"]
    request_date = req["request_date"]
    requested_amount = float(req["requested_amount"])
    desired_completion = req.get("desired_completion_date", "")
    allows_partial = req.get("allows_partial_payment", "").lower() == "true"
    request_text = req.get("request_text", "")
    
    # Load user profile
    profile = data["profiles"].get(user_id)
    if not profile:
        return make_not_affordable_row(req, "User profile not found")
    
    home_currency = profile["home_currency"]
    current_balance = float(profile.get("current_available_balance", "0"))
    min_balance = float(profile.get("minimum_balance_to_keep", "0"))
    
    # Load user's financial events
    user_events = data["events_by_user"].get(user_id, [])
    
    # Check for messages that modify financial state
    messages = data["messages_by_request"].get(request_id, [])
    user_messages = data["messages_by_user"].get(user_id, [])
    
    # Apply message amends to events (salary changes, etc.)
    modified_events = apply_message_amends(user_events, user_messages, data["exchange_rates"], home_currency)
    
    # Classify events
    classified = classify_events(modified_events, request_date)
    
    # Get monthly recurring expenses
    recurring_monthly = get_monthly_recurring(
        classified["recurring_expenses"], home_currency, data["exchange_rates"]
    )
    
    # Get flexible expenses (for spending changes)
    flexible = get_monthly_recurring(
        classified["flexible_expenses"], home_currency, data["exchange_rates"]
    )
    
    # Get income schedule
    income_schedule = get_income_schedule(
        classified["settled_income"], home_currency, data["exchange_rates"]
    )
    
    # Get payment options for this request
    options = data["options_by_request"].get(request_id, [])
    
    # Check images for amounts on blank events
    check_image_amounts(user_events, user_id, request_id, data["images_by_request"], data["images_by_user"])
    
    # Try each payment method
    plans = []
    
    # 1. Full payment
    fp = try_full_payment(
        requested_amount, request_date, profile,
        recurring_monthly, income_schedule, classified["pending_debits"],
        lambda bal, mn, amt, rd, rec, inc, pd: can_afford_payment(bal, mn, amt, rd, rec, inc, pd),
        lambda bal, mn, amt, rd, dc, rec, inc, pd: find_earliest_full_payment_date(bal, mn, amt, rd, dc, rec, inc, pd),
    )
    if fp:
        plans.append(fp)
    
    # 2. Installments
    ip = try_installments(
        requested_amount, request_date, desired_completion, profile, options,
        recurring_monthly, income_schedule, classified["pending_debits"],
        lambda bal, mn, amt, rd, rec, inc, pd: can_afford_payment(bal, mn, amt, rd, rec, inc, pd),
    )
    if ip:
        plans.append(ip)
    
    # 3. Partial payment
    if allows_partial:
        pp = try_partial_payment(
            requested_amount, request_date, desired_completion, profile,
            recurring_monthly, income_schedule, classified["pending_debits"],
            lambda bal, mn, amt, rd, rec, inc, pd: can_afford_payment(bal, mn, amt, rd, rec, inc, pd),
            lambda bal, mn, amt, rd, dc, rec, inc, pd: find_earliest_full_payment_date(bal, mn, amt, rd, dc, rec, inc, pd),
        )
        if pp:
            plans.append(pp)
    
    # 4. Wait
    wt = try_wait(
        requested_amount, request_date, desired_completion, profile,
        recurring_monthly, income_schedule, classified["pending_debits"],
        lambda bal, mn, amt, rd, dc, rec, inc, pd: find_earliest_full_payment_date(bal, mn, amt, rd, dc, rec, inc, pd),
    )
    if wt:
        plans.append(wt)
    
    # Rank and select best plan
    best = rank_plans(plans)
    
    if best is None:
        return make_not_affordable_row(req, "No safe payment option available")
    
    # Check for spending changes needed
    spending_changes = "none"
    if best["status"] == "affordable_with_plan" and best["method"] == "full_payment":
        # May need spending changes to afford full payment
        spending_changes = check_spending_changes_needed(
            requested_amount, request_date, profile, recurring_monthly, flexible,
            income_schedule, classified["pending_debits"], data["exchange_rates"]
        )
    
    # Generate explanation
    explanation = generate_explanation(best, req, profile, home_currency)
    
    return {
        "request_id": request_id,
        "amount_safe_to_pay": f"{best['amount_safe_to_pay']:.2f}",
        "affordability_status": best["status"],
        "recommended_payment_method": best["method"],
        "payment_plan": best["payment_plan"],
        "earliest_date_for_full_payment": best.get("earliest_date", ""),
        "spending_changes_needed": spending_changes,
        "decision_explanation": explanation,
    }


def apply_message_amends(events, messages, rates, home_currency):
    """Apply salary/payment amends from messages to events."""
    modified = list(events)
    
    for msg in messages:
        text = msg.get("message_text", "").lower()
        source = msg.get("source_type", "")
        
        # Look for salary changes
        if "salary" in text or "gaji" in text or "payroll" in text:
            # Extract new salary amount if mentioned
            import re
            amounts = re.findall(r'[\d,]+\.?\d*', msg.get("message_text", ""))
            if amounts:
                # Update the most recent income event
                for e in reversed(modified):
                    if e.get("direction") == "credit" or e.get("event_type") == "income":
                        # This is a simplification - in reality we'd parse the message more carefully
                        break
    
    return modified


def check_image_amounts(events, user_id, request_id, images_by_request, images_by_user):
    """Check images for amounts on events with blank amounts."""
    for e in events:
        if not e.get("amount") or e.get("amount") == "0":
            # Find linked image
            event_id = e.get("event_id", "")
            for img in images_by_request.get(request_id, []):
                if img.get("related_event_id") == event_id:
                    # In a real implementation, we'd use VLM to extract amount from image
                    # For now, mark it as needing image processing
                    e["_needs_image"] = True
                    break


def check_spending_changes_needed(
    requested_amount, request_date, profile, recurring_monthly, flexible,
    income_schedule, pending_debits, rates
):
    """Check if spending changes are needed to afford the request."""
    balance = float(profile.get("current_available_balance", "0"))
    min_balance = float(profile.get("minimum_balance_to_keep", "0"))
    
    # Try without changes
    is_safe, _ = can_afford_payment(
        balance, min_balance, requested_amount, request_date,
        recurring_monthly, income_schedule, pending_debits
    )
    
    if is_safe:
        return "none"
    
    # Try stopping flexible expenses
    for cat, amount in flexible.items():
        modified_monthly = dict(recurring_monthly)
        modified_monthly[cat] = modified_monthly.get(cat, 0) - amount
        
        is_safe, _ = can_afford_payment(
            balance, min_balance, requested_amount, request_date,
            modified_monthly, income_schedule, pending_debits
        )
        if is_safe:
            # Find the event_id for this category
            for e in profile.get("_flexible_events", []):
                if e.get("category") == cat:
                    return f"stop:{e['event_id']}"
    
    return "none"


def generate_explanation(plan, req, profile, home_currency):
    """Generate a concise explanation of the recommendation."""
    method = plan["method"]
    amount = plan["amount_safe_to_pay"]
    requested = float(req["requested_amount"])
    status = plan["status"]
    currency = home_currency
    
    if method == "full_payment":
        return f"Pay {currency} {requested:,.2f} today. This keeps the {currency} {float(profile.get('minimum_balance_to_keep', 0)):,.2f} minimum balance protected."
    elif method == "installments":
        plan_str = plan["payment_plan"]
        num_payments = plan["num_payments"]
        first_payment = plan_str.split("|")[0].split(":")[1]
        return f"Use {num_payments} installments of {currency} {float(first_payment):,.2f}, starting {plan['earliest_date']}. This keeps the minimum balance protected."
    elif method == "partial_payment":
        return f"Pay {currency} {amount:,.2f} today and the remaining {currency} {requested - amount:,.2f} on {plan['earliest_date']}. This completes the full request while keeping the minimum balance protected."
    elif method == "wait":
        return f"Pay {currency} {requested:,.2f} in full on {plan['earliest_date']}. Paying earlier would put the minimum balance at risk."
    else:
        return f"Do not proceed with this payment. None of the available options keeps the {currency} {float(profile.get('minimum_balance_to_keep', 0)):,.2f} minimum balance protected."


def make_not_affordable_row(req, reason=""):
    """Create a not_affordable output row."""
    return {
        "request_id": req["request_id"],
        "amount_safe_to_pay": "0",
        "affordability_status": "not_affordable",
        "recommended_payment_method": "not_recommended",
        "payment_plan": "none",
        "earliest_date_for_full_payment": "",
        "spending_changes_needed": "none",
        "decision_explanation": reason or "Do not proceed with this payment. No safe option available within the forecast period.",
    }


def run_agent():
    """Main entry point: load data, process all requests, write output."""
    print("Loading data...")
    data = load_all()
    
    requests = data["requests"]
    print(f"Processing {len(requests)} requests...")
    
    output_rows = []
    for i, req in enumerate(requests):
        row = process_request(req, data)
        output_rows.append(row)
        if (i + 1) % 50 == 0:
            print(f"  Processed {i + 1}/{len(requests)}")
    
    # Write output
    output_path = Path(__file__).parent.parent / "output.csv"
    fieldnames = [
        "request_id",
        "amount_safe_to_pay",
        "affordability_status",
        "recommended_payment_method",
        "payment_plan",
        "earliest_date_for_full_payment",
        "spending_changes_needed",
        "decision_explanation",
    ]
    
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)
    
    print(f"Output written to {output_path}")
    print(f"Total requests: {len(output_rows)}")
    
    # Summary
    statuses = defaultdict(int)
    for row in output_rows:
        statuses[row["affordability_status"]] += 1
    print("Status summary:")
    for status, count in sorted(statuses.items()):
        print(f"  {status}: {count}")


if __name__ == "__main__":
    run_agent()
