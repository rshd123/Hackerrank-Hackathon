"""
main.py — End-to-end pipeline: load data -> process requests -> write output.csv

For each request in requests.csv:
1. Load profile, events, messages, images
2. Reconstruct financial state
3. Parse messages/images via LLM (if relevant)
4. Apply deltas to financial state
5. Generate all payment candidates
6. Rank and decide
7. Write output row

Usage:
    python code/main.py              # Full pipeline with LLM
    python code/main.py --no-llm     # Deterministic only (fast, ~1.5s)
"""

from __future__ import annotations

import csv
import os
import sys
import time
import traceback
from datetime import date, datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from code.data_loader import DataLoader, Message
from code.financial_state import FinancialState, LedgerDelta
from code.forecaster import Forecaster
from code.plan_generator import PlanGenerator
from code.decision import DecisionEngine, Decision


def process_request(
    request,
    state: FinancialState,
    data_loader: DataLoader,
    llm_parser,
    messages: list[Message],
    images: list,
) -> Decision:
    """Process a single request through the full pipeline.
    Falls back to deterministic-only if LLM fails."""

    deltas = []

    # Parse messages via LLM (if available)
    if llm_parser and messages:
        try:
            raw_deltas = llm_parser.parse_messages(messages)
            for d in raw_deltas:
                if d.get("event_id") and d.get("action") in ("cancel", "amend_amount", "amend_date"):
                    deltas.append(LedgerDelta(
                        event_id=d["event_id"],
                        action=d["action"],
                        new_value=d.get("new_value"),
                    ))
        except Exception:
            pass  # LLM failure is non-fatal

    # Parse images via LLM (if available)
    if llm_parser and images:
        for img in images:
            try:
                full_path = str(Path("dataset") / "media" / "images" / f"{img.image_id}.png")
                if os.path.exists(full_path):
                    result = llm_parser.extract_amount_from_image(full_path)
                    if result and img.related_event_id:
                        for e in state.events:
                            if e.event_id == img.related_event_id and e.amount is None:
                                deltas.append(LedgerDelta(
                                    event_id=img.related_event_id,
                                    action="amend_amount",
                                    new_value=str(result["amount"]),
                                ))
            except Exception:
                pass  # LLM failure is non-fatal

    # Apply deltas
    if deltas:
        state.apply_deltas(deltas)

    # Generate candidates
    forecaster = Forecaster(state, request)
    generator = PlanGenerator(state, request, data_loader)
    candidates = generator.generate_all_candidates()

    # Decide
    engine = DecisionEngine(forecaster)
    decision = engine.decide(candidates)

    return decision


def decision_to_row(decision: Decision) -> dict:
    """Convert Decision to output CSV row dict."""
    return {
        "request_id": decision.request_id,
        "amount_safe_to_pay": decision.amount_safe_to_pay,
        "affordability_status": decision.affordability_status,
        "recommended_payment_method": decision.recommended_payment_method,
        "payment_plan": decision.payment_plan,
        "earliest_date_for_full_payment": decision.earliest_date_for_full_payment,
        "spending_changes_needed": decision.spending_changes_needed,
        "decision_explanation": decision.decision_explanation,
    }


def main():
    dataset_path = "dataset"
    output_path = "output.csv"

    print("Loading data...")
    data_loader = DataLoader(dataset_path)

    requests = data_loader.load_requests()
    profiles = data_loader.load_profiles()

    # Load all events indexed by user_id
    print("Loading events...")
    all_events = {}
    for req in requests:
        uid = req.user_id
        if uid not in all_events:
            all_events[uid] = data_loader.load_events(uid)

    # Load messages and images for each request
    print("Loading messages and images...")
    all_messages = {}
    all_images = {}
    for req in requests:
        rid = req.request_id
        all_messages[rid] = data_loader.load_messages(rid)
        all_images[rid] = data_loader.load_images(rid)

    # Initialize LLM parser if API key available and not disabled
    llm_parser = None
    use_llm = "--no-llm" not in sys.argv
    api_key = os.environ.get("GROQ_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if api_key and use_llm:
        try:
            from code.llm_parser import LLMParser
            llm_parser = LLMParser(api_key=api_key)
            print("LLM parser initialized (Groq qwen/qwen3.8-27b)")
        except Exception as e:
            print(f"WARNING: LLM parser init failed: {e} -- running deterministic only")
    else:
        print("LLM parser disabled (--no-llm or no API key)")

    # Process each request
    print(f"Processing {len(requests)} requests...")
    results = []
    start_time = time.time()
    error_count = 0

    for i, req in enumerate(requests):
        uid = req.user_id
        profile = profiles.get(uid)
        if not profile:
            print(f"  WARNING: No profile for {uid}, skipping {req.request_id}")
            error_count += 1
            continue

        events = all_events.get(uid, [])
        messages = all_messages.get(req.request_id, [])
        images = all_images.get(req.request_id, [])

        try:
            # Build financial state (fresh copy for each request)
            state = FinancialState(profile, events, data_loader)

            # Process
            decision = process_request(req, state, data_loader, llm_parser, messages, images)
            results.append(decision_to_row(decision))

        except Exception as e:
            error_count += 1
            # Fallback: not_recommended with zero safe amount
            results.append({
                "request_id": req.request_id,
                "amount_safe_to_pay": 0,
                "affordability_status": "not_affordable",
                "recommended_payment_method": "not_recommended",
                "payment_plan": "none",
                "earliest_date_for_full_payment": "",
                "spending_changes_needed": "none",
                "decision_explanation": f"Error processing request: {str(e)[:100]}",
            })

        if (i + 1) % 25 == 0 or i == len(requests) - 1:
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            print(f"  [{i+1}/{len(requests)}] {rate:.1f} req/s - "
                  f"Last: {req.request_id} -> {decision.affordability_status}")

    # Write output
    print(f"\nWriting {output_path}...")
    fieldnames = [
        "request_id", "amount_safe_to_pay", "affordability_status",
        "recommended_payment_method", "payment_plan",
        "earliest_date_for_full_payment", "spending_changes_needed",
        "decision_explanation",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    # Summary
    elapsed = time.time() - start_time
    print(f"\nDone in {elapsed:.1f}s")
    print(f"Output: {output_path} ({len(results)} rows)")
    if error_count:
        print(f"Errors: {error_count} requests had issues")

    # Status distribution
    status_counts = {}
    for r in results:
        s = r["affordability_status"]
        status_counts[s] = status_counts.get(s, 0) + 1
    print("Status distribution:", status_counts)

    # Method distribution
    method_counts = {}
    for r in results:
        m = r["recommended_payment_method"]
        method_counts[m] = method_counts.get(m, 0) + 1
    print("Method distribution:", method_counts)

    # LLM usage
    if llm_parser:
        usage = llm_parser.get_usage()
        print(f"LLM usage: {usage['calls']} calls, "
              f"{usage['input_tokens']} in, {usage['output_tokens']} out")


if __name__ == "__main__":
    main()
