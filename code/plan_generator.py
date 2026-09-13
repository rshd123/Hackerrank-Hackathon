"""
plan_generator.py — Generate ALL candidate payment plans.

Combinatorial solver: generates full_payment, installment, and partial_payment
candidates for every request. Pure deterministic logic — no LLM calls.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional

from code.data_loader import DataLoader, PaymentOption, Request
from code.financial_state import FinancialState
from code.forecaster import Forecaster, ForecastResult, PaymentScenario


@dataclass
class CandidatePlan:
    """A generated candidate payment plan before ranking."""
    request_id: str
    method: str  # full_payment, installments, partial_payment, wait, not_recommended
    option_id: Optional[str] = None
    payment_plan: list[tuple[date, float]] = field(default_factory=list)
    total_cost: float = 0.0
    num_payments: int = 0
    first_payment_date: Optional[date] = None
    final_payment_date: Optional[date] = None
    safe: bool = False
    forecast: Optional[ForecastResult] = None
    spending_changes: list[str] = field(default_factory=list)


class PlanGenerator:
    """Generate all candidate payment plans for a request."""

    def __init__(self, state: FinancialState, request: Request, data_loader: DataLoader):
        self.state = state
        self.request = request
        self.forecaster = Forecaster(state, request)
        self.data_loader = data_loader

        # Load payment options
        self.options = data_loader.load_payment_options(request.request_id)

        # Filter options by user preferences
        self.valid_options = self._filter_options()

    def _filter_options(self) -> list[PaymentOption]:
        """Filter payment options by user preferences and constraints."""
        valid = []
        for opt in self.options:
            # Check method preference
            if opt.method not in self.state.profile.payment_preferences:
                continue

            # Check installment months constraint
            if opt.method == "installments":
                max_months = self.state.profile.max_installment_months
                if max_months is not None:
                    # Convert num_payments to months (assume ~30 days per payment)
                    months = opt.num_payments  # each payment is roughly monthly
                    if months > max_months:
                        continue

            valid.append(opt)
        return valid

    def generate_full_payment_candidates(self) -> list[CandidatePlan]:
        """Generate full payment candidates.

        Only generate if full_payment is in the user's valid_options.
        If the user doesn't accept full_payment as a method, we shouldn't
        recommend it (§6.3: respect user preferences).
        """
        candidates = []

        # Check if full_payment is a valid option for this user
        has_full_payment = any(o.method == "full_payment" for o in self.valid_options)

        if has_full_payment:
            scenario = self.forecaster.test_full_payment_now()
            headroom = self.forecaster.calculate_headroom()

            # Full payment on request_date is safe when the PROJ simulation
            # confirms the balance stays above min for all 90 days.
            full_payment_now_safe = scenario.forecast.safe
            candidates.append(CandidatePlan(
                request_id=self.request.request_id,
                method="full_payment",
                option_id=None,
                payment_plan=[(self.request.request_date, self.forecaster.requested_amount)],
                total_cost=self.forecaster.requested_amount,
                num_payments=1,
                first_payment_date=self.request.request_date,
                final_payment_date=self.request.request_date,
                safe=full_payment_now_safe,
                forecast=scenario.forecast,
            ))

            if not candidates[0].safe:
                earliest = self.forecaster.find_earliest_full_payment_date()
                if earliest and earliest != self.request.request_date:
                    scenario = self.forecaster._simulate_with_payment(
                        self.forecaster._build_base_ledger(),
                        earliest,
                        self.forecaster.requested_amount,
                    )
                    candidates.append(CandidatePlan(
                        request_id=self.request.request_id,
                        method="wait",
                        option_id=None,
                        payment_plan=[(earliest, self.forecaster.requested_amount)],
                        total_cost=self.forecaster.requested_amount,
                        num_payments=1,
                        first_payment_date=earliest,
                        final_payment_date=earliest,
                        safe=scenario.safe,
                        forecast=scenario,
                    ))

        return candidates

    def generate_installment_candidates(self) -> list[CandidatePlan]:
        """Generate installment payment candidates.

        Uses each supplied PaymentOption's first_payment_date and
        payment_frequency_days to build the exact payment schedule.
        §6.3: Validates per-period balance safety.
        """
        candidates = []

        for opt in self.valid_options:
            if opt.method != "installments":
                continue

            scenario = self.forecaster.test_installment_option(opt)

            # Build payment schedule from the supplied option dates
            plan = []
            pay_date = opt.first_payment_date
            for i in range(opt.num_payments):
                plan.append((pay_date, opt.amount))
                if opt.frequency_days:
                    pay_date = pay_date + timedelta(days=opt.frequency_days)
                else:
                    pay_date = pay_date + timedelta(days=30)

            total_cost = opt.amount * opt.num_payments

            candidates.append(CandidatePlan(
                request_id=self.request.request_id,
                method="installments",
                option_id=opt.option_id,
                payment_plan=plan,
                total_cost=total_cost,
                num_payments=opt.num_payments,
                first_payment_date=plan[0][0] if plan else None,
                final_payment_date=plan[-1][0] if plan else None,
                safe=scenario.forecast.safe,
                forecast=scenario.forecast,
            ))

        return candidates

    def generate_partial_payment_candidates(self) -> list[CandidatePlan]:
        """Generate partial payment candidates (if allowed).

        §6.2: partial_payment uses amount_safe_to_pay on request_date,
        then the remainder on a future date when the remaining amount is safe.
        """
        candidates = []

        if not self.request.allows_partial_payment:
            return candidates

        headroom = self.forecaster.calculate_headroom()
        if headroom <= 0:
            # Fallback: use PROJ headroom if PROJ simulation is safe
            proj_scenario = self.forecaster.test_full_payment_now()
            if proj_scenario.forecast.safe:
                proj_headroom = proj_scenario.forecast.min_balance_during - self.forecaster.state.profile.min_balance
                if proj_headroom > 0:
                    headroom = proj_headroom
            if headroom <= 0:
                return candidates  # can't do any payment

        # Cap partial at requested_amount
        partial_amount = min(headroom, self.forecaster.requested_amount)
        remaining = self.forecaster.requested_amount - partial_amount

        if remaining <= 0:
            return candidates  # this is full payment, not partial

        # Find earliest date when the REMAINING amount can be safely paid
        # (not the full amount - the remaining is smaller so it may be safe earlier)
        earliest_second = None
        for day_offset in range(90):
            pay_date = self.request.request_date + timedelta(days=day_offset)
            if pay_date <= self.request.request_date:
                continue
            # Simulate paying the remaining amount on this date
            scenario = self.forecaster.test_partial_payment(
                partial_amount, pay_date, remaining
            )
            if scenario.forecast.safe:
                earliest_second = pay_date
                break

        if earliest_second is None:
            # Try the full payment earliest date as fallback
            earliest_second = self.forecaster.find_earliest_full_payment_date()
            if earliest_second is None:
                return candidates

        # Check if second payment meets deadline
        if self.request.desired_completion_date and earliest_second > self.request.desired_completion_date:
            # Can't meet deadline with partial payment
            return candidates

        scenario = self.forecaster.test_partial_payment(
            partial_amount, earliest_second, remaining
        )
        candidates.append(CandidatePlan(
            request_id=self.request.request_id,
            method="partial_payment",
            payment_plan=[
                (self.request.request_date, partial_amount),
                (earliest_second, remaining),
            ],
            total_cost=self.forecaster.requested_amount,
            num_payments=2,
            first_payment_date=self.request.request_date,
            final_payment_date=earliest_second,
            safe=scenario.forecast.safe,
            forecast=scenario.forecast,
        ))

        return candidates

    def generate_wait_candidate(self) -> CandidatePlan:
        """Generate a 'wait' candidate (recommend waiting)."""
        earliest = self.forecaster.find_earliest_full_payment_date()
        return CandidatePlan(
            request_id=self.request.request_id,
            method="wait",
            payment_plan=[],
            total_cost=0,
            num_payments=0,
            first_payment_date=None,
            final_payment_date=None,
            safe=False,
            forecast=None,
        )

    def generate_not_recommended(self) -> CandidatePlan:
        """Generate a 'not_recommended' candidate (never affordable)."""
        return CandidatePlan(
            request_id=self.request.request_id,
            method="not_recommended",
            payment_plan=[],
            total_cost=0,
            num_payments=0,
            first_payment_date=None,
            final_payment_date=None,
            safe=False,
            forecast=None,
        )

    def generate_all_candidates(self) -> list[CandidatePlan]:
        """Generate ALL candidate payment plans."""
        candidates = []
        candidates.extend(self.generate_full_payment_candidates())
        candidates.extend(self.generate_installment_candidates())
        candidates.extend(self.generate_partial_payment_candidates())
        candidates.append(self.generate_wait_candidate())
        candidates.append(self.generate_not_recommended())
        return candidates
