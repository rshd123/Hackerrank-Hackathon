"""
decision.py — Rank candidates using 6-step tie-breaker and produce final decision.

Rules from §6.2:
1. Complete the request by its deadline
2. Avoid spending changes
3. Minimize total payment cost
4. Start earlier
5. Fewer payments
6. Lowest payment_option_id

Final output: request_id, amount_safe_to_pay, affordability_status,
recommended_payment_method, payment_plan, earliest_date_for_full_payment,
spending_changes_needed, decision_explanation
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

from code.data_loader import Request
from code.forecaster import Forecaster
from code.plan_generator import CandidatePlan


@dataclass
class Decision:
    """Final decision for a request."""
    request_id: str
    amount_safe_to_pay: float
    affordability_status: str  # affordable_now, affordable_with_plan, affordable_later, not_affordable
    recommended_payment_method: str  # full_payment, partial_payment, installments, wait, not_recommended
    payment_plan: str  # "YYYY-MM-DD:amount|YYYY-MM-DD:amount" or "none"
    earliest_date_for_full_payment: str  # YYYY-MM-DD or ""
    spending_changes_needed: str  # "none" or "stop:event_id|reduce_to:event_id:amount"
    decision_explanation: str


class DecisionEngine:
    """Rank candidates and produce final decision."""

    def __init__(self, forecaster: Forecaster):
        self.forecaster = forecaster

    def _meets_deadline(self, candidate: CandidatePlan) -> bool:
        """Check if candidate completes the request by desired_completion_date."""
        deadline = self.forecaster.request.desired_completion_date
        if deadline is None:
            return True  # no deadline constraint

        if candidate.final_payment_date is None:
            return False

        return candidate.final_payment_date <= deadline

    def _spending_changes_count(self, candidate: CandidatePlan) -> int:
        """Count number of spending changes in candidate."""
        return len(candidate.spending_changes)

    def _sort_key(self, candidate: CandidatePlan) -> tuple:
        """6-step tie-breaker sort key (lower = better).

        §6.2 tie-breaker:
        1. Complete by deadline
        2. No spending changes
        3. Minimize total payment cost
        4. Start earlier
        5. Fewer payments
        6. Lowest payment_option_id
        """
        meets_deadline = self._meets_deadline(candidate)
        changes = self._spending_changes_count(candidate)
        cost = candidate.total_cost

        if candidate.first_payment_date:
            start_ordinal = candidate.first_payment_date.toordinal()
        else:
            start_ordinal = date.max.toordinal()

        num_payments = candidate.num_payments
        option_id = candidate.option_id or "zzz"

        return (
            0 if meets_deadline else 1,
            changes,
            cost,
            start_ordinal,
            num_payments,
            option_id,
        )

    def rank_candidates(self, candidates: list[CandidatePlan]) -> list[CandidatePlan]:
        """Rank candidates by 6-step tie-breaker."""
        return sorted(candidates, key=self._sort_key)

    def _determine_status(self, winner: CandidatePlan) -> str:
        """Determine affordability_status using strict waterfall hierarchy.

        §6.2 waterfall:
        1. affordable_now: Full payment on request_date, balance ≥ min_balance
           for all 90 days, completes by desired_completion_date.
        2. affordable_with_plan: Structured plan (installments/partial) is safe,
           meets deadline, and fits within cash flow constraints.
        3. affordable_later: Full payment becomes safe on a future date, but
           cannot meet the immediate deadline or fit into current liquid budget.
        4. not_affordable: No payment plan or future wait date maintains balance
           above minimum requirement within the 90-day window.
        """
        if winner.method == "not_recommended":
            return "not_affordable"

        if winner.method == "wait":
            return "affordable_later"

        if not winner.safe:
            return "not_affordable"

        # For safe candidates, determine status based on method and timing
        if winner.method == "full_payment" and winner.num_payments == 1:
            # Check if payment is on request_date
            if winner.first_payment_date == self.forecaster.request.request_date:
                # Check deadline constraint
                deadline = self.forecaster.request.desired_completion_date
                if deadline and winner.first_payment_date and winner.first_payment_date > deadline:
                    return "affordable_later"
                # affordable_now when PROJ safety margin is large relative to
                # the request amount (user can absorb the payment easily).
                if winner.forecast and winner.forecast.safe:
                    proj_head = winner.forecast.min_balance_during - self.forecaster.state.profile.min_balance
                    req_amount = self.forecaster.requested_amount
                    if req_amount > 0 and proj_head / req_amount >= 0.25:
                        return "affordable_now"
                return "affordable_with_plan"
            else:
                # Full payment but NOT on request_date
                deadline = self.forecaster.request.desired_completion_date
                if deadline and winner.first_payment_date and winner.first_payment_date > deadline:
                    return "affordable_later"
                return "affordable_with_plan"

        # Installments or partial payment
        if winner.method in ("installments", "partial_payment"):
            deadline = self.forecaster.request.desired_completion_date
            if deadline and winner.final_payment_date and winner.final_payment_date > deadline:
                return "affordable_later"
            return "affordable_with_plan"

        return "not_affordable"

    def _format_plan(self, candidate: CandidatePlan) -> str:
        """Format payment plan as pipe-separated string."""
        if not candidate.payment_plan:
            return "none"
        parts = []
        for pay_date, amount in candidate.payment_plan:
            parts.append(f"{pay_date}:{amount:.2f}")
        return "|".join(parts)

    def _format_explanation(self, winner: CandidatePlan, status: str) -> str:
        """Generate concise explanation."""
        req = self.forecaster.request
        amount = self.forecaster.requested_amount

        if status == "affordable_now":
            return (
                f"User can safely pay the full amount of {amount:.2f} on "
                f"{req.request_date}. Balance stays above minimum throughout "
                f"the forecast period."
            )
        elif status == "affordable_with_plan":
            if winner.method == "installments":
                return (
                    f"Full payment now would breach the minimum balance. "
                    f"Installment plan ({winner.num_payments} payments of "
                    f"{winner.payment_plan[0][1]:.2f}) keeps the balance safe "
                    f"and completes by the deadline."
                )
            elif winner.method == "partial_payment":
                return (
                    f"Partial payment of {winner.payment_plan[0][1]:.2f} now, "
                    f"rest on {winner.final_payment_date}. Keeps balance above "
                    f"minimum while completing the request."
                )
            return (
                f"A payment plan allows completing the request while keeping "
                f"balance above the minimum threshold."
            )
        elif status == "affordable_later":
            earliest = self.forecaster.find_earliest_full_payment_date()
            return (
                f"Cannot afford now or via installments within the deadline. "
                f"Full payment becomes safe on {earliest}." if earliest else
                f"Cannot afford within the 90-day forecast period."
            )
        else:
            return (
                f"No safe payment option found. The requested amount of "
                f"{amount:.2f} would push the balance below the minimum "
                f"threshold of {self.forecaster.state.profile.min_balance:.2f}."
            )

    def decide(self, candidates: list[CandidatePlan]) -> Decision:
        """Pick the best candidate using strict waterfall hierarchy.

        Waterfall order:
        1. Try immediate full payment (affordable_now)
        2. Try structured plan (affordable_with_plan)
        3. Try deferred payment (affordable_later)
        4. Fall back to not_recommended (not_affordable)
        """
        ranked = self.rank_candidates(candidates)

        # Separate candidates by type
        full_payment_now = [
            c for c in ranked
            if c.method == "full_payment" and c.safe
            and c.first_payment_date == self.forecaster.request.request_date
        ]
        structured_plans = [
            c for c in ranked
            if c.method in ("installments", "partial_payment") and c.safe
        ]
        deferred_payment = [
            c for c in ranked
            if c.method == "full_payment" and c.safe
            and c.first_payment_date != self.forecaster.request.request_date
        ]
        wait_candidates = [c for c in ranked if c.method == "wait"]
        not_rec_candidates = [c for c in ranked if c.method == "not_recommended"]

        # Waterfall selection
        winner = None

        # 1. Try immediate full payment
        if full_payment_now:
            winner = full_payment_now[0]

        # 2. Try structured plan (only if no immediate full payment)
        if winner is None and structured_plans:
            winner = structured_plans[0]

        # 3. Try deferred payment (only if no structured plan)
        if winner is None and deferred_payment:
            winner = deferred_payment[0]

        # 4. Try wait (only if there's a future date when payment is safe)
        if winner is None:
            earliest = self.forecaster.find_earliest_full_payment_date()
            if wait_candidates and earliest:
                winner = wait_candidates[0]

        # 5. Fall back to not_recommended
        if winner is None:
            winner = not_rec_candidates[0] if not_rec_candidates else ranked[0]

        status = self._determine_status(winner)

        # Amount safe to pay = headroom (baseline, before spending changes)
        headroom = self.forecaster.calculate_headroom()
        amount_safe = min(headroom, self.forecaster.requested_amount)

        # Earliest date for full payment
        earliest = self.forecaster.find_earliest_full_payment_date()
        earliest_str = str(earliest) if earliest else ""

        # Spending changes
        changes = "none"
        if winner.spending_changes:
            changes = "|".join(winner.spending_changes)

        return Decision(
            request_id=self.forecaster.request.request_id,
            amount_safe_to_pay=round(amount_safe, 2),
            affordability_status=status,
            recommended_payment_method=winner.method,
            payment_plan=self._format_plan(winner),
            earliest_date_for_full_payment=earliest_str,
            spending_changes_needed=changes,
            decision_explanation=self._format_explanation(winner, status),
        )
