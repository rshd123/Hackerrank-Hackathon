"""
data_loader.py — Load all dataset CSVs into memory

Reads requests, profiles, events, payment options, exchange rates, messages, images.
Joins by user_id, request_id, related_event_id.
"""

import csv
import os
from collections import defaultdict
from pathlib import Path

DATASET_DIR = Path(__file__).parent.parent / "dataset"


def load_csv(filename):
    path = DATASET_DIR / filename
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_all():
    requests = load_csv("requests.csv")
    profiles = {r["user_id"]: r for r in load_csv("financial_profiles.csv")}
    events = load_csv("financial_events.csv")
    payment_options = load_csv("request_payment_options.csv")
    exchange_rates = load_csv("exchange_rates.csv")
    messages = load_csv("messages.csv")
    images = load_csv("images.csv")
    sample_requests = load_csv("sample_requests.csv")

    # Index events by user_id
    events_by_user = defaultdict(list)
    for e in events:
        events_by_user[e["user_id"]].append(e)

    # Index messages by user_id and request_id
    messages_by_user = defaultdict(list)
    messages_by_request = defaultdict(list)
    for m in messages:
        messages_by_user[m["user_id"]].append(m)
        if m.get("request_id"):
            messages_by_request[m["request_id"]].append(m)

    # Index images by user_id and request_id
    images_by_user = defaultdict(list)
    images_by_request = defaultdict(list)
    for img in images:
        images_by_user[img["user_id"]].append(img)
        if img.get("request_id"):
            images_by_request[img["request_id"]].append(img)

    # Index payment options by request_id
    options_by_request = defaultdict(list)
    for opt in payment_options:
        options_by_request[opt["request_id"]].append(opt)

    # Index exchange rates by (date, from, to)
    rates = {}
    for r in exchange_rates:
        key = (r["rate_date"], r["from_currency"], r["to_currency"])
        rates[key] = float(r["rate"])

    return {
        "requests": requests,
        "profiles": profiles,
        "events_by_user": events_by_user,
        "options_by_request": options_by_request,
        "exchange_rates": rates,
        "messages_by_user": messages_by_user,
        "messages_by_request": messages_by_request,
        "images_by_user": images_by_user,
        "images_by_request": images_by_request,
        "sample_requests": sample_requests,
    }
