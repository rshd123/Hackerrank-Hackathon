"""
data_loader.py — Load all dataset CSVs into typed data structures.

Handles: requests, profiles, events, payment options, exchange rates, messages, images.
All amounts converted to home_currency using dated exchange rates.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import pandas as pd


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class Request:
    request_id: str
    user_id: str
    request_date: date
    request_type: str
    requested_amount: float
    desired_completion_date: date
    allows_partial_payment: bool
    request_text: str


@dataclass
class UserProfile:
    user_id: str
    home_currency: str
    current_balance: float
    min_balance: float
    priorities: list[str] = field(default_factory=list)
    protected_categories: list[str] = field(default_factory=list)
    flexible_reduce: list[str] = field(default_factory=list)
    flexible_stop: list[str] = field(default_factory=list)
    payment_preferences: list[str] = field(default_factory=list)
    max_installment_months: Optional[int] = None


@dataclass
class FinancialEvent:
    event_id: str
    user_id: str
    event_type: str
    description: str
    category: str
    direction: str  # "debit" | "credit"
    amount: Optional[float]  # None = blank, needs image extraction
    currency: str
    event_date: date
    settlement_date: Optional[date]
    status: str  # settled, pending, scheduled, cancelled, failed, unrealized
    linked_event_id: Optional[str]
    flexibility: str  # fixed, stoppable, reducible
    minimum_allowed_amount: Optional[float] = None


@dataclass
class PaymentOption:
    option_id: str
    request_id: str
    method: str  # full_payment | installments
    amount: float
    num_payments: int
    first_payment_date: date
    frequency_days: Optional[int]
    financing_fee: float
    total_payable: float


@dataclass
class Message:
    message_id: str
    user_id: str
    request_id: Optional[str]
    related_event_id: Optional[str]
    sent_at: datetime
    source_type: str
    message_text: str


@dataclass
class Image:
    image_id: str
    user_id: str
    request_id: Optional[str]
    related_event_id: Optional[str]


# ---------------------------------------------------------------------------
# Data loader
# ---------------------------------------------------------------------------

class DataLoader:
    """Load and index all dataset CSVs. Provides typed accessors."""

    def __init__(self, dataset_path: str | Path):
        self.root = Path(dataset_path)
        self._cache: dict[str, pd.DataFrame] = {}

    # -- internal helpers ---------------------------------------------------

    def _read(self, filename: str) -> pd.DataFrame:
        if filename not in self._cache:
            self._cache[filename] = pd.read_csv(self.root / filename)
        return self._cache[filename]

    def _to_date(self, val) -> date | None:
        if pd.isna(val) or val is None or str(val).strip() == "":
            return None
        return pd.Timestamp(val).date()

    def _to_datetime(self, val) -> datetime | None:
        if pd.isna(val) or val is None or str(val).strip() == "":
            return None
        return pd.Timestamp(val).to_pydatetime()

    def _to_float(self, val) -> float | None:
        if pd.isna(val) or val is None or str(val).strip() == "":
            return None
        return float(val)

    def _to_int(self, val) -> int | None:
        if pd.isna(val) or val is None or str(val).strip() == "":
            return None
        return int(val)

    def _split_pipe(self, val) -> list[str]:
        if pd.isna(val) or val is None or str(val).strip() == "":
            return []
        return [s.strip() for s in str(val).split("|") if s.strip()]

    # -- public loaders -----------------------------------------------------

    def load_requests(self) -> list[Request]:
        df = self._read("requests.csv")
        return [
            Request(
                request_id=row["request_id"],
                user_id=row["user_id"],
                request_date=self._to_date(row["request_date"]),
                request_type=row["request_type"],
                requested_amount=float(row["requested_amount"]),
                desired_completion_date=self._to_date(row["desired_completion_date"]),
                allows_partial_payment=str(row["allows_partial_payment"]).strip().lower() == "true",
                request_text=row["request_text"],
            )
            for _, row in df.iterrows()
        ]

    def load_profiles(self) -> dict[str, UserProfile]:
        df = self._read("financial_profiles.csv")
        profiles = {}
        for _, row in df.iterrows():
            uid = row["user_id"]
            profiles[uid] = UserProfile(
                user_id=uid,
                home_currency=row["home_currency"],
                current_balance=float(row["current_available_balance"]),
                min_balance=float(row["minimum_balance_to_keep"]),
                priorities=self._split_pipe(row.get("financial_priorities")),
                protected_categories=self._split_pipe(row.get("expense_categories_to_protect")),
                flexible_reduce=self._split_pipe(row.get("expense_categories_user_is_willing_to_reduce")),
                flexible_stop=self._split_pipe(row.get("expense_categories_user_is_willing_to_stop")),
                payment_preferences=self._split_pipe(row.get("payment_methods_user_will_consider")),
                max_installment_months=self._to_int(row.get("max_installment_months")),
            )
        return profiles

    def load_events(self, user_id: str | None = None) -> list[FinancialEvent]:
        df = self._read("financial_events.csv")
        if user_id is not None:
            df = df[df["user_id"] == user_id]
        return [
            FinancialEvent(
                event_id=row["event_id"],
                user_id=row["user_id"],
                event_type=row["event_type"],
                description=row["description"],
                category=row["category"],
                direction=row["direction"],
                amount=self._to_float(row["amount"]),
                currency=row["currency"],
                event_date=self._to_date(row["event_date"]),
                settlement_date=self._to_date(row["settlement_date"]),
                status=row["status"],
                linked_event_id=row.get("linked_event_id") or None,
                flexibility=row["flexibility"],
                minimum_allowed_amount=self._to_float(row.get("minimum_allowed_amount")),
            )
            for _, row in df.iterrows()
        ]

    def load_payment_options(self, request_id: str | None = None) -> list[PaymentOption]:
        df = self._read("request_payment_options.csv")
        if request_id is not None:
            df = df[df["request_id"] == request_id]
        return [
            PaymentOption(
                option_id=row["payment_option_id"],
                request_id=row["request_id"],
                method=row["payment_method"],
                amount=float(row["payment_amount"]),
                num_payments=int(row["number_of_payments"]),
                first_payment_date=self._to_date(row["first_payment_date"]),
                frequency_days=self._to_int(row.get("payment_frequency_days")),
                financing_fee=float(row["financing_fee"]),
                total_payable=float(row["total_payable_amount"]),
            )
            for _, row in df.iterrows()
        ]

    def load_exchange_rates(self) -> dict[tuple[str, str, str], float]:
        """Index by (rate_date_str, from_currency, to_currency) → rate."""
        df = self._read("exchange_rates.csv")
        rates = {}
        for _, row in df.iterrows():
            key = (str(row["rate_date"]).strip(), str(row["from_currency"]).strip(), str(row["to_currency"]).strip())
            rates[key] = float(row["rate"])
        return rates

    def load_messages(self, request_id: str | None = None) -> list[Message]:
        df = self._read("messages.csv")
        if request_id is not None:
            df = df[df["request_id"] == request_id]
        return [
            Message(
                message_id=row["message_id"],
                user_id=row["user_id"],
                request_id=row.get("request_id") or None,
                related_event_id=row.get("related_event_id") or None,
                sent_at=self._to_datetime(row["sent_at"]),
                source_type=row["source_type"],
                message_text=row["message_text"],
            )
            for _, row in df.iterrows()
        ]

    def load_images(self, request_id: str | None = None) -> list[Image]:
        df = self._read("images.csv")
        if request_id is not None:
            df = df[df["request_id"] == request_id]
        return [
            Image(
                image_id=row["image_id"],
                user_id=row["user_id"],
                request_id=row.get("request_id") or None,
                related_event_id=row.get("related_event_id") or None,
            )
            for _, row in df.iterrows()
        ]

    # -- currency conversion ------------------------------------------------

    def convert_currency(
        self,
        amount: float,
        from_cur: str,
        to_cur: str,
        target_date: date,
        rates: dict | None = None,
    ) -> float:
        """Convert amount using dated exchange rate. Returns amount in to_cur."""
        if from_cur == to_cur:
            return amount

        if rates is None:
            rates = self.load_exchange_rates()

        date_str = target_date.isoformat()

        # Try exact date match first
        rate = rates.get((date_str, from_cur, to_cur))
        if rate is not None:
            return amount * rate

        # Try fallback: find closest date <= target_date for this currency pair
        candidates = [
            (d, r) for (d, fc, tc), r in rates.items()
            if fc == from_cur and tc == to_cur and d <= date_str
        ]
        if candidates:
            best = max(candidates, key=lambda x: x[0])
            return amount * best[1]

        # Try inverse rate
        inverse = rates.get((date_str, to_cur, from_cur))
        if inverse is not None and inverse != 0:
            return amount / inverse

        raise ValueError(
            f"No exchange rate found for {from_cur}→{to_cur} on or before {date_str}"
        )
