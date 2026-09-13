"""
financial_state.py — Reconstruct a user's daily financial ledger.

Takes user profile + events, converts currencies, detects recurring patterns,
projects 90-day daily balance. No LLM calls — pure deterministic logic.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional

from code.data_loader import DataLoader, FinancialEvent, UserProfile


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class LedgerDelta:
    """LLM-extracted amendment to the ledger."""
    event_id: str
    action: str  # cancel | delay | amend_amount | amend_date
    new_value: Optional[str] = None


@dataclass
class RecurringPattern:
    """Detected recurring expense pattern."""
    category: str
    description: str
    flexibility: str
    amounts: list[float] = field(default_factory=list)
    day_of_month: Optional[int] = None
    avg_amount: float = 0.0


@dataclass
class DailyTransaction:
    """One day's net cash flow."""
    date: date
    income: float = 0.0
    expenses: float = 0.0
    net: float = 0.0


@dataclass
class DailyLedger:
    """90-day daily balance projection."""
    start_balance: float
    min_balance: float
    daily_transactions: list[DailyTransaction] = field(default_factory=list)

    @property
    def end_balance(self) -> float:
        if not self.daily_transactions:
            return self.start_balance
        return self.daily_transactions[-1].balance

    def balances(self) -> list[float]:
        """Return running balance for each day."""
        bal = self.start_balance
        result = [bal]
        for dt in self.daily_transactions:
            bal += dt.net
            result.append(bal)
        return result


# ---------------------------------------------------------------------------
# Financial state reconstruction
# ---------------------------------------------------------------------------

class FinancialState:
    """Reconstruct a user's financial position from events."""

    def __init__(
        self,
        profile: UserProfile,
        events: list[FinancialEvent],
        data_loader: DataLoader,
    ):
        self.profile = profile
        self.home_currency = profile.home_currency
        self.data_loader = data_loader
        self.rates = data_loader.load_exchange_rates()

        # Convert all event amounts to home currency
        self.events = [self._convert_event(e) for e in events]

        # Apply conflict resolution
        self.events = self._resolve_conflicts(self.events)

        # Classify
        self.recurring = []        # fixed recurring debits
        self.flexible = []         # stoppable/reducible debits
        self.pending_debits = []   # pending future debits
        self.pending_credits = []  # pending credits (don't count)
        self.confirmed_income = [] # settled/scheduled credits

        self._classify_events()

        # Detect recurring patterns
        self.patterns = self._detect_recurring_patterns()

    def _convert_event(self, e: FinancialEvent) -> FinancialEvent:
        """Convert event amount to home currency."""
        if e.amount is None:
            return e  # blank amount — will be filled by LLM extraction

        convert_date = e.settlement_date or e.event_date
        if convert_date is None:
            return e

        converted = self.data_loader.convert_currency(
            e.amount, e.currency, self.home_currency, convert_date, self.rates
        )
        # Return new event with converted amount and home currency
        return FinancialEvent(
            event_id=e.event_id,
            user_id=e.user_id,
            event_type=e.event_type,
            description=e.description,
            category=e.category,
            direction=e.direction,
            amount=converted,
            currency=self.home_currency,
            event_date=e.event_date,
            settlement_date=e.settlement_date,
            status=e.status,
            linked_event_id=e.linked_event_id,
            flexibility=e.flexibility,
            minimum_allowed_amount=e.minimum_allowed_amount,
        )

    def _resolve_conflicts(self, events: list[FinancialEvent]) -> list[FinancialEvent]:
        """Apply §6.3 conflict resolution rules.

        Only remove true duplicates and lifecycle conflicts:
        1. Cancelled/failed events are dropped.
        2. Events with None/zero amounts are dropped.
        3. linked_event_id pairs: keep both sides (refund + purchase are
           separate cash flows). Only drop if two debits link to the same
           source — keep the newer settled one.
        4. Same-user+category+date: if one is settled and one is pending,
           drop the pending (it was superseded by the settled version).
        Never treat same category + same month as a duplicate — multiple
        grocery or transport transactions in a month are legitimate.
        """
        # Separate income from expenses
        income_events = [e for e in events if e.direction == "credit" or e.event_type == "income"]
        expense_events = [e for e in events if e.direction == "debit" and e.event_type != "income"]

        # Step 1: Drop cancelled, failed, and zero/NaN amount events
        expense_events = [
            e for e in expense_events
            if e.status not in ("cancelled", "failed")
            and e.amount is not None and e.amount > 0
        ]

        # Step 2: Handle linked_event_id pairs
        linked_map: dict[str, list[FinancialEvent]] = defaultdict(list)
        for e in expense_events:
            lid = e.linked_event_id
            if lid is not None and not (isinstance(lid, float) and math.isnan(lid)):
                linked_map[lid].append(e)

        events_to_drop: set[str] = set()
        for source_id, linked_events in linked_map.items():
            debits = [e for e in linked_events if e.direction == "debit"]
            if len(debits) > 1:
                # Multiple debits linked to same source — keep newest settled
                debits.sort(key=lambda e: (
                    0 if e.status == "settled" else 1,
                    -(e.event_date.toordinal() if e.event_date else 0),
                ))
                for e in debits[1:]:
                    events_to_drop.add(e.event_id)

        # Step 3: Same-user+category+date: settled supersedes pending
        by_key: dict[str, list[FinancialEvent]] = defaultdict(list)
        for e in expense_events:
            if e.event_id in events_to_drop:
                continue
            key = f"{e.user_id}:{e.category}:{e.event_date}"
            by_key[key].append(e)

        for group_events in by_key.values():
            if len(group_events) <= 1:
                continue
            has_settled = any(e.status == "settled" for e in group_events)
            if has_settled:
                for e in group_events:
                    if e.status in ("pending", "scheduled"):
                        events_to_drop.add(e.event_id)

        # Build final list
        resolved = [e for e in expense_events if e.event_id not in events_to_drop]

        # Add all income events back (don't deduplicate)
        resolved.extend(income_events)

        return resolved

    def _classify_events(self):
        """Separate events into categories for forecasting."""
        for e in self.events:
            if e.status in ("cancelled", "failed"):
                continue
            if e.amount is None or e.amount == 0:
                continue

            if e.status == "pending":
                if e.direction == "debit":
                    self.pending_debits.append(e)
                elif e.direction == "credit":
                    self.pending_credits.append(e)
                continue

            if e.direction == "credit" or e.event_type == "income":
                self.confirmed_income.append(e)
            elif e.direction == "debit":
                if e.flexibility in ("stoppable", "reducible"):
                    self.flexible.append(e)
                else:
                    self.recurring.append(e)

    def _detect_recurring_patterns(self) -> list[RecurringPattern]:
        """Detect monthly recurring expense patterns from settled history.

        Aggregates events by (category, year-month) before detecting frequency,
        so categories with multiple transactions per month (groceries, transport)
        are correctly identified as monthly recurring.
        """
        from collections import defaultdict

        # Group settled events by category
        by_category: dict[str, list[FinancialEvent]] = defaultdict(list)
        for e in self.recurring:
            if e.status == "settled" and e.event_date is not None and e.amount is not None:
                by_category[e.category].append(e)

        patterns = []
        for category, cat_events in by_category.items():
            if len(cat_events) < 2:
                continue

            # Aggregate by month: total amount per (category, year-month)
            monthly_totals: dict[tuple[int, int], float] = defaultdict(float)
            monthly_events: dict[tuple[int, int], list[FinancialEvent]] = defaultdict(list)
            for e in cat_events:
                key = (e.event_date.year, e.event_date.month)
                monthly_totals[key] += e.amount
                monthly_events[key].append(e)

            if len(monthly_totals) < 2:
                continue

            # Sort months and compute gaps between months
            sorted_months = sorted(monthly_totals.keys())
            month_gaps = []
            for i in range(len(sorted_months) - 1):
                y1, m1 = sorted_months[i]
                y2, m2 = sorted_months[i + 1]
                gap_days = (date(y2, m2, 1) - date(y1, m1, 1)).days
                month_gaps.append(gap_days)

            avg_gap = sum(month_gaps) / len(month_gaps) if month_gaps else 0

            # Check if months appear roughly monthly (25-40 days between months)
            if 25 <= avg_gap <= 40:
                amounts = [e.amount for e in cat_events if e.amount is not None]
                # Use the day-of-month from the most recent month's last event
                last_month_events = monthly_events[sorted_months[-1]]
                last_month_events.sort(key=lambda e: e.event_date.day)
                day_of_month = last_month_events[-1].event_date.day

                # Average monthly total (sum of all transactions in a month)
                monthly_avg = sum(monthly_totals.values()) / len(monthly_totals)

                patterns.append(RecurringPattern(
                    category=category,
                    description=cat_events[-1].description,
                    flexibility=cat_events[-1].flexibility,
                    amounts=amounts,
                    day_of_month=day_of_month,
                    avg_amount=monthly_avg,
                ))

        return patterns

    def apply_deltas(self, deltas: list[LedgerDelta]):
        """Apply LLM-extracted amendments to events."""
        delta_map = {d.event_id: d for d in deltas}

        new_events = []
        for e in self.events:
            if e.event_id in delta_map:
                d = delta_map[e.event_id]
                if d.action == "cancel":
                    continue  # skip this event
                elif d.action == "amend_amount" and d.new_value:
                    e = FinancialEvent(
                        event_id=e.event_id, user_id=e.user_id,
                        event_type=e.event_type, description=e.description,
                        category=e.category, direction=e.direction,
                        amount=float(d.new_value), currency=e.currency,
                        event_date=e.event_date, settlement_date=e.settlement_date,
                        status=e.status, linked_event_id=e.linked_event_id,
                        flexibility=e.flexibility,
                        minimum_allowed_amount=e.minimum_allowed_amount,
                    )
                elif d.action == "amend_date" and d.new_value:
                    from datetime import datetime
                    new_date = datetime.strptime(d.new_value, "%Y-%m-%d").date()
                    e = FinancialEvent(
                        event_id=e.event_id, user_id=e.user_id,
                        event_type=e.event_type, description=e.description,
                        category=e.category, direction=e.direction,
                        amount=e.amount, currency=e.currency,
                        event_date=new_date, settlement_date=new_date,
                        status=e.status, linked_event_id=e.linked_event_id,
                        flexibility=e.flexibility,
                        minimum_allowed_amount=e.minimum_allowed_amount,
                    )
            new_events.append(e)

        self.events = new_events
        # Re-classify
        self.recurring.clear()
        self.flexible.clear()
        self.pending_debits.clear()
        self.pending_credits.clear()
        self.confirmed_income.clear()
        self._classify_events()
        self.patterns = self._detect_recurring_patterns()

    def build_daily_ledger(self, start_date: date, days: int = 90, include_income_projection: bool = True) -> DailyLedger:
        """Build 90-day daily transaction ledger.
        
        Args:
            include_income_projection: If True, project recurring income forward.
                If False, only count confirmed income events in the window.
                Used for headroom calculation (§6.3: do not invent unsupported income).
        """
        ledger = DailyLedger(
            start_balance=self.profile.current_balance,
            min_balance=self.profile.min_balance,
        )

        # Detect income patterns and project forward
        income_by_date: dict[date, float] = defaultdict(float)

        # First: add confirmed income on settlement dates in the window
        for e in self.confirmed_income:
            d = e.settlement_date or e.event_date
            if d and e.amount is not None and start_date <= d < start_date + timedelta(days=days):
                income_by_date[d] += e.amount

        # Second: detect recurring income pattern and project forward
        # §6.3: only count confirmed income on its settlement date; project
        # forward ONLY if last known income is within a reasonable window
        # (45 days) of the forecast start, to avoid虚构 future income from
        # stale salary data.
        if include_income_projection:
            income_events_sorted = sorted(
                [e for e in self.confirmed_income if e.event_date is not None and e.amount is not None],
                key=lambda e: e.event_date,
            )

            # Project income forward only when there are 2+ income events
            # that prove a recurring pattern. §6.3: "Do not invent unsupported
            # future income." A single income event is not evidence of recurrence.
            if len(income_events_sorted) >= 2:
                dates = [e.event_date for e in income_events_sorted]
                amounts = [e.amount for e in income_events_sorted]

                # Identify the dominant salary amount (mode) to exclude one-off bonuses.
                from collections import Counter
                rounded_amounts = [round(a / 1000) * 1000 for a in amounts]
                amount_counts = Counter(rounded_amounts)
                dominant_amount = amount_counts.most_common(1)[0][0]

                # Filter to only events matching the dominant salary amount
                salary_indices = [i for i, a in enumerate(amounts) if round(a / 1000) * 1000 == dominant_amount]
                salary_dates = [dates[i] for i in salary_indices]
                salary_amounts = [amounts[i] for i in salary_indices]

                if len(salary_indices) < 2:
                    salary_dates = dates
                    salary_amounts = amounts

                avg_amount = sum(salary_amounts) / len(salary_amounts)

                # Detect frequency pattern from gaps between salary events.
                gaps = sorted([(salary_dates[i+1] - salary_dates[i]).days for i in range(len(salary_dates)-1)])
                median_gap = gaps[len(gaps) // 2]

                freq_days = None
                if 5 <= median_gap <= 9:
                    freq_days = 7
                elif 12 <= median_gap <= 16:
                    freq_days = 14
                elif 25 <= median_gap <= 35:
                    freq_days = 30

                if freq_days and avg_amount > 0:
                    last_salary_date = salary_dates[-1]
                    days_since_last = (start_date - last_salary_date).days

                    # Only project if last salary is within 45 days of forecast start
                    if days_since_last <= 45:
                        if freq_days == 30:
                            # Monthly: project on same day-of-month as last salary
                            proj_day = last_salary_date.day
                            proj_month = last_salary_date.month + 1
                            proj_year = last_salary_date.year
                            if proj_month > 12:
                                proj_month = 1
                                proj_year += 1
                            while True:
                                try:
                                    proj_date = date(proj_year, proj_month, min(proj_day, 28))
                                except ValueError:
                                    proj_date = date(proj_year, proj_month, 28)
                                if proj_date >= start_date + timedelta(days=days):
                                    break
                                if proj_date >= start_date:
                                    if proj_date not in income_by_date or income_by_date[proj_date] == 0:
                                        income_by_date[proj_date] += avg_amount
                                proj_month += 1
                                if proj_month > 12:
                                    proj_month = 1
                                    proj_year += 1
                        else:
                            # Weekly/bi-weekly: project from last_salary_date + freq_days
                            proj_date = last_salary_date + timedelta(days=freq_days)
                            while proj_date < start_date + timedelta(days=days):
                                if proj_date >= start_date:
                                    if proj_date not in income_by_date or income_by_date[proj_date] == 0:
                                        income_by_date[proj_date] += avg_amount
                                proj_date += timedelta(days=freq_days)

        # Build pending debit schedule
        pending_by_date: dict[date, float] = defaultdict(float)
        for e in self.pending_debits:
            d = e.settlement_date or e.event_date
            if d and e.amount is not None:
                pending_by_date[d] += e.amount

        # Build recurring expense schedule (project patterns forward)
        recurring_by_date: dict[date, float] = defaultdict(float)
        for pattern in self.patterns:
            if pattern.day_of_month is None:
                continue
            for day_offset in range(days):
                d = start_date + timedelta(days=day_offset)
                if d.day == pattern.day_of_month:
                    recurring_by_date[d] += pattern.avg_amount

        # Also add one-time settled expenses that fall in the forecast window
        # (not part of recurring patterns)
        pattern_categories = {p.category for p in self.patterns}
        for e in self.recurring:
            if e.category not in pattern_categories and e.event_date:
                if start_date <= e.event_date < start_date + timedelta(days=days):
                    if e.amount is not None:
                        recurring_by_date[e.event_date] += e.amount

        # Build daily transactions
        for day_offset in range(days):
            d = start_date + timedelta(days=day_offset)
            income = income_by_date.get(d, 0.0)
            expenses = recurring_by_date.get(d, 0.0) + pending_by_date.get(d, 0.0)

            ledger.daily_transactions.append(DailyTransaction(
                date=d,
                income=income,
                expenses=expenses,
                net=income - expenses,
            ))

        return ledger

    def get_recurring_expenses(self) -> list[RecurringPattern]:
        return self.patterns

    def get_flexible_events(self) -> list[FinancialEvent]:
        return self.flexible
