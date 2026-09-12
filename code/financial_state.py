"""
financial_state.py — Reconstruct a user's financial position

Separates recurring from one-time events, reserves pending debits,
counts confirmed salary on settlement date, handles exchange rates.
"""

from datetime import datetime, timedelta
from collections import defaultdict
import math


def parse_date(s):
    if not s:
        return None
    return datetime.strptime(s, "%Y-%m-%d").date()


def parse_float(s):
    if not s:
        return 0.0
    return float(s.replace(",", ""))


def get_exchange_rate(rates, from_curr, to_curr, date_str):
    """Get exchange rate for a currency pair on a given date."""
    if from_curr == to_curr:
        return 1.0
    # Try exact date first, then fallback to nearest earlier date
    keys = sorted(rates.keys())
    # Find the rate for this date or the most recent one before it
    best_rate = None
    best_date = None
    for (rate_date, fc, tc), rate in rates.items():
        if fc == from_curr and tc == to_curr and rate_date <= date_str:
            if best_date is None or rate_date > best_date:
                best_date = rate_date
                best_rate = rate
    return best_rate


def convert_to_home_currency(amount, from_currency, home_currency, rates, date_str):
    """Convert amount to home currency using exchange rates."""
    if from_currency == home_currency:
        return amount
    rate = get_exchange_rate(rates, from_currency, home_currency, date_str)
    if rate is None:
        # Try reverse
        rate = get_exchange_rate(rates, home_currency, from_currency, date_str)
        if rate is None:
            return amount  # fallback
        return amount / rate
    return amount * rate


def classify_events(events, request_date_str):
    """Classify events into categories for forecasting."""
    recurring_expenses = []  # fixed recurring debits
    flexible_expenses = []   # stoppable/reducible debits
    pending_debits = []      # pending future debits
    pending_credits = []     # pending credits (don't count yet)
    settled_income = []      # confirmed salary payments
    one_time = []            # one-time settled expenses
    
    for e in events:
        status = e.get("status", "")
        direction = e.get("direction", "")
        flexibility = e.get("flexibility", "")
        event_type = e.get("event_type", "")
        amount = parse_float(e.get("amount", "0"))
        event_date = e.get("event_date", "")
        settlement_date = e.get("settlement_date", event_date)
        category = e.get("category", "")
        
        if status == "cancelled" or status == "failed":
            continue
        if amount == 0:
            continue
            
        if status == "pending":
            if direction == "debit":
                pending_debits.append(e)
            elif direction == "credit":
                pending_credits.append(e)
            continue
            
        if status in ("settled", "scheduled"):
            if direction == "credit" or event_type == "income":
                settled_income.append(e)
            elif direction == "debit":
                if flexibility in ("stoppable", "reducible"):
                    flexible_expenses.append(e)
                else:
                    recurring_expenses.append(e)
    
    return {
        "recurring_expenses": recurring_expenses,
        "flexible_expenses": flexible_expenses,
        "pending_debits": pending_debits,
        "pending_credits": pending_credits,
        "settled_income": settled_income,
    }


def get_monthly_recurring(events, home_currency, rates):
    """Calculate monthly recurring expense total from settled events."""
    monthly = defaultdict(float)
    for e in events:
        amount = convert_to_home_currency(
            parse_float(e.get("amount", "0")),
            e.get("currency", home_currency),
            home_currency,
            rates,
            e.get("settlement_date", e.get("event_date", "")),
        )
        category = e.get("category", "other")
        monthly[category] += amount
    return monthly


def get_income_schedule(events, home_currency, rates):
    """Extract confirmed salary/income schedule."""
    income = []
    for e in events:
        amount = convert_to_home_currency(
            parse_float(e.get("amount", "0")),
            e.get("currency", home_currency),
            home_currency,
            rates,
            e.get("settlement_date", e.get("event_date", "")),
        )
        date = e.get("settlement_date") or e.get("event_date")
        if date:
            income.append({"date": parse_date(date), "amount": amount, "event": e})
    return sorted(income, key=lambda x: x["date"] or datetime.max.date())


def get_next_income_after(income_schedule, after_date):
    """Get the next income payment after a given date."""
    for inc in income_schedule:
        if inc["date"] and inc["date"] > after_date:
            return inc
    return None
