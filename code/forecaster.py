"""
forecaster.py — 90-day deterministic simulator.

Uses DailyLedger from financial_state to simulate payment scenarios.
Calculates headroom, earliest safe date, and tests all payment options.
Pure deterministic logic — no LLM calls.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional

from code.data_loader import DataLoader, FinancialEvent, PaymentOption, Request
from code.financial_state import FinancialState, DailyLedger, DailyTransaction


@dataclass
class ForecastResult:
    """Result of simulating a payment scenario."""
    safe: bool
    min_balance_during: float = 0.0
    min_balance_date: Optional[date] = None
    daily_balances: list[float] = field(default_factory=list)
    final_balance: float = 0.0


@dataclass
class PaymentScenario:
    """A candidate payment plan with simulation results."""
    request_id: str
    method: str  # full_payment, installments, partial_payment
    option_id: Optional[str] = None
    payment_plan: list[tuple[date, float]] = field(default_factory=list)
    total_cost: float = 0.0
    forecast: Optional[ForecastResult] = None
    spending_changes: list[str] = field(default_factory=list)


class Forecaster:
    """Simulate payment scenarios against a user's daily ledger."""

    def __init__(self, state: FinancialState, request: Request):
        self.state = state
        self.request = request
        self.request_date = request.request_date
        self.home_currency = state.home_currency
        # requested_amount is already in the user's home currency
        self.requested_amount = request.requested_amount

    def _build_base_ledger(self, days: int = 90) -> DailyLedger:
        """Build the baseline daily ledger (no new payment)."""
        return self.state.build_daily_ledger(self.request_date, days)

    def _build_base_ledger_no_income_projection(self, days: int = 90) -> DailyLedger:
        """Build baseline ledger WITHOUT income projection for headroom."""
        return self.state.build_daily_ledger(self.request_date, days, include_income_projection=False)

    def _clone_ledger(self, ledger: DailyLedger) -> DailyLedger:
        """Deep clone a ledger for simulation."""
        return deepcopy(ledger)

    def _simulate_with_payment(
        self,
        ledger: DailyLedger,
        payment_date: date,
        payment_amount: float,
    ) -> ForecastResult:
        """Simulate paying payment_amount on payment_date.
        Returns whether the balance stays above min_balance."""
        balance = ledger.start_balance
        min_bal = balance
        min_bal_date = self.request_date
        daily_balances = [balance]

        for dt in ledger.daily_transactions:
            # Apply income and expenses before checking payment day
            balance += dt.net

            # Apply payment on the payment date
            if dt.date == payment_date:
                balance -= payment_amount
                daily_balances.append(balance)
                if balance < min_bal:
                    min_bal = balance
                    min_bal_date = dt.date
                continue

            daily_balances.append(balance)
            if balance < min_bal:
                min_bal = balance
                min_bal_date = dt.date

        return ForecastResult(
            safe=min_bal >= self.state.profile.min_balance,
            min_balance_during=min_bal,
            min_balance_date=min_bal_date,
            daily_balances=daily_balances,
            final_balance=balance,
        )

    def _simulate_installments(
        self,
        option: PaymentOption,
    ) -> ForecastResult:
        """Simulate paying an installment option over its term.

        Uses the exact payment schedule from the PaymentOption:
        - first_payment_date: when the first installment is due
        - frequency_days: days between each payment
        - amount: per-payment amount
        - num_payments: total number of payments
        """
        balance = self.state.profile.current_balance
        min_bal = balance
        min_bal_date = self.request_date
        daily_balances = [balance]

        # Build installment schedule from the supplied option
        installment_amount = option.amount
        installment_dates = []
        pay_date = option.first_payment_date
        for i in range(option.num_payments):
            installment_dates.append((pay_date, installment_amount))
            if option.frequency_days:
                pay_date = pay_date + timedelta(days=option.frequency_days)
            else:
                pay_date = pay_date + timedelta(days=30)

        date_idx = 0
        for dt in self._build_base_ledger().daily_transactions:
            balance += dt.net

            # Check if any installment falls on this date
            while date_idx < len(installment_dates) and installment_dates[date_idx][0] <= dt.date:
                pd, pa = installment_dates[date_idx]
                if pd == dt.date:
                    balance -= pa
                date_idx += 1

            daily_balances.append(balance)
            if balance < min_bal:
                min_bal = balance
                min_bal_date = dt.date

        return ForecastResult(
            safe=min_bal >= self.state.profile.min_balance,
            min_balance_during=min_bal,
            min_balance_date=min_bal_date,
            daily_balances=daily_balances,
            final_balance=balance,
        )

    def _simulate_partial_payment(
        self,
        partial_amount: float,
        second_payment_date: date,
        second_payment_amount: float,
    ) -> ForecastResult:
        """Simulate paying partial now, rest later."""
        balance = self.state.profile.current_balance
        min_bal = balance
        min_bal_date = self.request_date
        daily_balances = [balance]

        for dt in self._build_base_ledger().daily_transactions:
            balance += dt.net

            if dt.date == self.request_date:
                balance -= partial_amount
            elif dt.date == second_payment_date:
                balance -= second_payment_amount

            daily_balances.append(balance)
            if balance < min_bal:
                min_bal = balance
                min_bal_date = dt.date

        return ForecastResult(
            safe=min_bal >= self.state.profile.min_balance,
            min_balance_during=min_bal,
            min_balance_date=min_bal_date,
            daily_balances=daily_balances,
            final_balance=balance,
        )

    def calculate_headroom(self) -> float:
        """Calculate max safe payment on request_date (headroom).

        §6.3: "Do not invent unsupported future income."
        Uses the90-day simulation WITHOUT income projection to find the
        minimum balance, then calculates how much can be paid today while
        keeping balance above min_balance throughout the forecast period.
        """
        ledger = self._build_base_ledger_no_income_projection()
        balance = ledger.start_balance
        min_bal = balance

        for dt in ledger.daily_transactions:
            balance += dt.net
            if balance < min_bal:
                min_bal = balance

        # Headroom = how much we can pay NOW without going below min_balance
        headroom = min_bal - self.state.profile.min_balance
        return max(0.0, headroom)

    def find_earliest_full_payment_date(
        self,
        days: int = 90,
    ) -> Optional[date]:
        """Find the earliest date when full payment is safe."""
        ledger = self._build_base_ledger(days)

        for day_offset in range(days):
            pay_date = self.request_date + timedelta(days=day_offset)
            result = self._simulate_with_payment(ledger, pay_date, self.requested_amount)
            if result.safe:
                return pay_date

        return None

    def test_full_payment_now(self) -> PaymentScenario:
        """Test paying full amount on request_date."""
        forecast = self._simulate_with_payment(
            self._build_base_ledger(), self.request_date, self.requested_amount
        )
        return PaymentScenario(
            request_id=self.request.request_id,
            method="full_payment",
            payment_plan=[(self.request_date, self.requested_amount)],
            total_cost=self.requested_amount,
            forecast=forecast,
        )

    def test_installment_option(self, option: PaymentOption) -> PaymentScenario:
        """Test a specific installment payment option."""
        forecast = self._simulate_installments(option)
        total = option.amount * option.num_payments
        return PaymentScenario(
            request_id=self.request.request_id,
            method="installments",
            option_id=option.option_id,
            payment_plan=[],  # filled by plan_generator
            total_cost=total,
            forecast=forecast,
        )

    def test_partial_payment(
        self,
        partial_amount: float,
        second_payment_date: date,
        second_payment_amount: float,
    ) -> PaymentScenario:
        """Test partial payment now, rest on a future date."""
        forecast = self._simulate_partial_payment(
            partial_amount, second_payment_date, second_payment_amount
        )
        return PaymentScenario(
            request_id=self.request.request_id,
            method="partial_payment",
            payment_plan=[
                (self.request_date, partial_amount),
                (second_payment_date, second_payment_amount),
            ],
            total_cost=partial_amount + second_payment_amount,
            forecast=forecast,
        )

    def find_wait_date(
        self,
        days: int = 90,
    ) -> Optional[date]:
        """Find earliest date when user could afford this request (wait scenario).
        Returns None if never affordable within forecast window."""
        return self.find_earliest_full_payment_date(days)
