"""
forecaster.py — 90-day balance projection

Projects the user's balance forward day by day using recurring income/expenses,
pending payments, and confirmed events. Returns the minimum balance during
the forecast and the date it occurs.
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


def forecast_90_days(
    current_balance,
    min_balance,
    request_date,
    recurring_expenses_monthly,
    income_schedule,
    pending_debits,
    spending_changes=None,
):
    """
    Forecast balance for 90 days from request_date.
    
    Args:
        current_balance: Available balance on request_date
        min_balance: Minimum balance to keep
        request_date: The request evaluation date
        recurring_expenses_monthly: dict of {category: monthly_amount}
        income_schedule: list of {date, amount} sorted by date
        pending_debits: list of pending debit events
        spending_changes: dict of {event_id: new_amount} or {event_id: 0} for stop
    
    Returns:
        dict with:
            - min_balance_during_forecast: the lowest projected balance
            - min_balance_date: date when minimum occurs
            - daily_balances: list of (date, balance) for each day
            - is_safe: whether balance stays above min_balance
    """
    start = parse_date(request_date) if isinstance(request_date, str) else request_date
    end = start + timedelta(days=90)
    
    # Build daily balance projection
    daily = {}
    balance = current_balance
    
    # Pre-compute monthly expense total (adjusted for spending changes)
    monthly_expense_total = 0
    for cat, amount in recurring_expenses_monthly.items():
        # Check if this category is being reduced/stopped
        adjusted = False
        if spending_changes:
            for evt_id, new_amt in spending_changes.items():
                # This is a simplified check - in reality we'd need to match category
                pass
        monthly_expense_total += amount
    
    # Adjust for spending changes
    if spending_changes:
        for evt_id, new_amt in spending_changes.items():
            if new_amt == 0:
                # Stopping an expense - subtract its monthly amount
                # We need to know the category... simplified approach:
                pass
    
    # Build income lookup by date
    income_by_date = defaultdict(float)
    for inc in income_schedule:
        if inc["date"] and start <= inc["date"] <= end:
            income_by_date[inc["date"]] += inc["amount"]
    
    # Build pending debit schedule
    pending_by_date = defaultdict(float)
    for pd in pending_debits:
        pd_date = parse_date(pd.get("settlement_date") or pd.get("event_date"))
        if pd_date and start <= pd_date <= end:
            amount = parse_float(pd.get("amount", "0"))
            pending_by_date[pd_date] += amount
    
    # Day-by-day forecast
    min_bal = balance
    min_bal_date = start
    daily_balances = []
    
    current = start
    days_in_month = 30  # approximate
    
    while current <= end:
        # Add income if this is a pay date
        if current in income_by_date:
            balance += income_by_date[current]
        
        # Subtract pending debits
        if current in pending_by_date:
            balance -= pending_by_date[current]
        
        # Subtract daily recurring expenses (monthly / 30)
        day_expense = monthly_expense_total / days_in_month
        balance -= day_expense
        
        # Track minimum
        if balance < min_bal:
            min_bal = balance
            min_bal_date = current
        
        daily_balances.append((current, balance))
        current += timedelta(days=1)
    
    return {
        "min_balance_during_forecast": min_bal,
        "min_balance_date": min_bal_date,
        "daily_balances": daily_balances,
        "is_safe": min_bal >= min_balance,
    }


def can_afford_payment(
    current_balance,
    min_balance,
    payment_amount,
    request_date,
    recurring_expenses_monthly,
    income_schedule,
    pending_debits,
    days_to_forecast=90,
):
    """
    Check if making a payment of payment_amount on request_date
    keeps the balance above min_balance for the forecast period.
    """
    start = parse_date(request_date) if isinstance(request_date, str) else request_date
    end = start + timedelta(days=days_to_forecast)
    
    balance_after_payment = current_balance - payment_amount
    
    if balance_after_payment < min_balance:
        return False, balance_after_payment
    
    # Forecast forward
    result = forecast_90_days(
        balance_after_payment,
        min_balance,
        request_date,
        recurring_expenses_monthly,
        income_schedule,
        pending_debits,
    )
    
    return result["is_safe"], result["min_balance_during_forecast"]


def find_earliest_full_payment_date(
    current_balance,
    min_balance,
    requested_amount,
    request_date,
    desired_completion_date,
    recurring_expenses_monthly,
    income_schedule,
    pending_debits,
):
    """
    Find the earliest date when the user can safely pay the full amount.
    Searches from request_date to desired_completion_date.
    """
    start = parse_date(request_date) if isinstance(request_date, str) else request_date
    end = parse_date(desired_completion_date) if isinstance(desired_completion_date, str) else desired_completion_date
    
    if not end:
        end = start + timedelta(days=90)
    
    # Try each day
    current = start
    while current <= end:
        # Simulate paying full amount on this date
        # Project balance from request_date to current, then subtract payment
        balance = current_balance
        
        # Add income between request_date and current
        for inc in income_schedule:
            if inc["date"] and start <= inc["date"] <= current:
                balance += inc["amount"]
        
        # Subtract recurring expenses between request_date and current
        days_elapsed = (current - start).days
        balance -= (recurring_expenses_monthly_total(recurring_expenses_monthly) / 30) * days_elapsed
        
        # Subtract pending debits between request_date and current
        for pd in pending_debits:
            pd_date = parse_date(pd.get("settlement_date") or pd.get("event_date"))
            if pd_date and start <= pd_date <= current:
                balance -= parse_float(pd.get("amount", "0"))
        
        # Check if we can afford full payment on this date
        balance_after = balance - requested_amount
        if balance_after >= min_balance:
            return current
        
        current += timedelta(days=1)
    
    return None  # Cannot afford within forecast period


def recurring_expenses_monthly_total(expenses_dict):
    """Sum all monthly recurring expenses."""
    return sum(expenses_dict.values())
