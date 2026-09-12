"""
plan_generator.py — Generate and rank payment plans

Tries full payment, installments, partial payment, wait, and not_recommended.
Ranks by: complete by deadline > no changes > min cost > earlier > fewer payments.
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


def try_full_payment(
    requested_amount,
    request_date,
    user_profile,
    recurring_expenses_monthly,
    income_schedule,
    pending_debits,
    can_afford_fn,
    find_earliest_fn,
):
    """Try paying the full amount today."""
    balance = parse_float(user_profile.get("current_available_balance", "0"))
    min_balance = parse_float(user_profile.get("minimum_balance_to_keep", "0"))
    payment_prefs = user_profile.get("payment_methods_user_will_consider", "")
    
    if "full_payment" not in payment_prefs:
        return None
    
    is_safe, min_bal = can_afford_fn(
        balance, min_balance, requested_amount, request_date,
        recurring_expenses_monthly, income_schedule, pending_debits
    )
    
    if is_safe:
        return {
            "method": "full_payment",
            "status": "affordable_now",
            "amount_safe_to_pay": requested_amount,
            "payment_plan": f"{request_date}:{requested_amount}",
            "earliest_date": request_date,
            "spending_changes": "none",
            "total_cost": requested_amount,
            "num_payments": 1,
        }
    return None


def try_installments(
    requested_amount,
    request_date,
    desired_completion_date,
    user_profile,
    payment_options,
    recurring_expenses_monthly,
    income_schedule,
    pending_debits,
    can_afford_fn,
):
    """Try each installment option."""
    balance = parse_float(user_profile.get("current_available_balance", "0"))
    min_balance = parse_float(user_profile.get("minimum_balance_to_keep", "0"))
    payment_prefs = user_profile.get("payment_methods_user_will_consider", "")
    max_months = user_profile.get("max_installment_months", "")
    
    if "installments" not in payment_prefs:
        return None
    
    best = None
    for opt in payment_options:
        if opt.get("payment_method") != "installments":
            continue
        
        num_payments = int(opt.get("number_of_payments", "1"))
        payment_amount = parse_float(opt.get("payment_amount", "0"))
        first_date_str = opt.get("first_payment_date", request_date)
        freq_days = int(opt.get("payment_frequency_days", "30"))
        total_payable = parse_float(opt.get("total_payable_amount", "0"))
        
        # Check max_installment_months
        if max_months:
            max_m = int(max_months)
            total_days = num_payments * freq_days
            if total_days > max_m * 30:
                continue
        
        # Generate payment dates
        plan_dates = []
        current_date = parse_date(first_date_str)
        for i in range(num_payments):
            plan_dates.append(current_date)
            current_date += timedelta(days=freq_days)
        
        # Check if plan completes by desired_completion_date
        if desired_completion_date:
            completion = parse_date(desired_completion_date)
            if plan_dates[-1] > completion:
                continue
        
        # Simulate: can we make all payments while staying above min?
        sim_balance = balance
        all_safe = True
        for pay_date in plan_dates:
            # Add income up to this date
            for inc in income_schedule:
                if inc["date"] and inc["date"] <= pay_date:
                    sim_balance += inc["amount"]
            
            # Subtract recurring expenses up to this date
            days_elapsed = (pay_date - parse_date(request_date)).days
            monthly_total = sum(recurring_expenses_monthly.values())
            sim_balance -= (monthly_total / 30) * days_elapsed
            
            # Make payment
            sim_balance -= payment_amount
            
            if sim_balance < min_balance:
                all_safe = False
                break
        
        if all_safe:
            # Check payment date matches sample format
            plan_str = "|".join(f"{d}:{payment_amount}" for d in plan_dates)
            
            if best is None or total_payable < best["total_cost"]:
                best = {
                    "method": "installments",
                    "status": "affordable_with_plan",
                    "amount_safe_to_pay": payment_amount,
                    "payment_plan": plan_str,
                    "earliest_date": str(plan_dates[-1]),
                    "spending_changes": "none",
                    "total_cost": total_payable,
                    "num_payments": num_payments,
                    "option_id": opt.get("payment_option_id", ""),
                }
    
    return best


def try_partial_payment(
    requested_amount,
    request_date,
    desired_completion_date,
    user_profile,
    recurring_expenses_monthly,
    income_schedule,
    pending_debits,
    can_afford_fn,
    find_earliest_fn,
):
    """Try paying part today and the rest by deadline."""
    balance = parse_float(user_profile.get("current_available_balance", "0"))
    min_balance = parse_float(user_profile.get("minimum_balance_to_keep", "0"))
    payment_prefs = user_profile.get("payment_methods_user_will_consider", "")
    
    if "partial_payment" not in payment_prefs:
        return None
    
    if not desired_completion_date:
        return None
    
    # Find what we can safely pay today
    max_today = 0
    for try_amount in range(int(requested_amount), 0, -100):
        is_safe, _ = can_afford_fn(
            balance, min_balance, try_amount, request_date,
            recurring_expenses_monthly, income_schedule, pending_debits
        )
        if is_safe:
            max_today = try_amount
            break
    
    if max_today <= 0 or max_today >= requested_amount:
        return None
    
    remaining = requested_amount - max_today
    
    # Check if we can pay remaining by deadline
    earliest_rest = find_earliest_fn(
        balance, min_balance, remaining, request_date,
        desired_completion_date, recurring_expenses_monthly,
        income_schedule, pending_debits
    )
    
    if earliest_rest and earliest_rest <= parse_date(desired_completion_date):
        return {
            "method": "partial_payment",
            "status": "affordable_with_plan",
            "amount_safe_to_pay": max_today,
            "payment_plan": f"{request_date}:{max_today}|{earliest_rest}:{remaining}",
            "earliest_date": str(earliest_rest),
            "spending_changes": "none",
            "total_cost": requested_amount,
            "num_payments": 2,
        }
    return None


def try_wait(
    requested_amount,
    request_date,
    desired_completion_date,
    user_profile,
    recurring_expenses_monthly,
    income_schedule,
    pending_debits,
    find_earliest_fn,
):
    """Wait until full payment becomes safe."""
    payment_prefs = user_profile.get("payment_methods_user_will_consider", "")
    
    if "full_payment" not in payment_prefs:
        return None
    
    earliest = find_earliest_fn(
        parse_float(user_profile.get("current_available_balance", "0")),
        parse_float(user_profile.get("minimum_balance_to_keep", "0")),
        requested_amount,
        request_date,
        desired_completion_date or (parse_date(request_date) + timedelta(days=90)).isoformat(),
        recurring_expenses_monthly,
        income_schedule,
        pending_debits,
    )
    
    if earliest:
        return {
            "method": "wait",
            "status": "affordable_later",
            "amount_safe_to_pay": 0,
            "payment_plan": f"{earliest}:{requested_amount}",
            "earliest_date": str(earliest),
            "spending_changes": "none",
            "total_cost": requested_amount,
            "num_payments": 1,
        }
    return None


def rank_plans(plans):
    """Rank plans by priority rules."""
    if not plans:
        return None
    
    def sort_key(p):
        # 1. Complete by deadline (affordable_now/with_plan > later > not)
        status_rank = {
            "affordable_now": 0,
            "affordable_with_plan": 1,
            "affordable_later": 2,
            "not_affordable": 3,
        }
        # 2. No spending changes needed
        changes = 0 if p["spending_changes"] == "none" else 1
        # 3. Minimize total cost
        cost = p["total_cost"]
        # 4. Earlier start
        earliest = p.get("earliest_date", "9999-99-99")
        # 5. Fewer payments
        num_pay = p["num_payments"]
        
        return (status_rank.get(p["status"], 3), changes, cost, earliest, num_pay)
    
    return sorted(plans, key=sort_key)[0]
