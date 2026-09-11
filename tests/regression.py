"""
regression.py — Regression test suite

Track which tickets break across runs.
Mrinal's winning workflow: "Reproduce → regression test → smallest fix → revert"
"""

import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.core import process_ticket
from agent.schemas import TicketInput

RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)


def load_tickets(path: str = "data/input_tickets.json") -> list[TicketInput]:
    """Load tickets from JSON file."""
    with open(path, "r") as f:
        data = json.load(f)
    return [TicketInput(**ticket) for ticket in data]


def run_and_capture() -> dict:
    """Run agent on all tickets and capture results."""
    tickets = load_tickets()
    results = {}

    for ticket in tickets:
        try:
            output = process_ticket(ticket)
            results[ticket.id] = {
                "status": output.status,
                "justification": output.justification,
                "urgency": output.urgency,
                "response": output.response,
                "error": None,
            }
        except Exception as e:
            results[ticket.id] = {
                "status": "error",
                "justification": None,
                "urgency": None,
                "response": None,
                "error": str(e),
            }

    return results


def save_results(results: dict, tag: str = "latest") -> Path:
    """Save results to a timestamped JSON file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"regression_{tag}_{timestamp}.json"
    filepath = RESULTS_DIR / filename

    with open(filepath, "w") as f:
        json.dump(results, f, indent=2)

    # Also save as latest
    latest_path = RESULTS_DIR / "regression_latest.json"
    with open(latest_path, "w") as f:
        json.dump(results, f, indent=2)

    return filepath


def compare_results(current: dict, previous: dict) -> dict:
    """Compare current results against previous to find regressions."""
    regressions = []
    improvements = []
    unchanged = 0

    for ticket_id, prev in previous.items():
        curr = current.get(ticket_id)
        if not curr:
            regressions.append({
                "ticket": ticket_id,
                "type": "missing",
                "previous": prev["status"],
                "current": "not found",
            })
            continue

        if curr["status"] != prev["status"]:
            if prev["status"] in ("replied", "escalated") and curr["status"] in ("replied", "escalated"):
                regressions.append({
                    "ticket": ticket_id,
                    "type": "status_changed",
                    "previous": prev["status"],
                    "current": curr["status"],
                })
            elif prev["status"] == "error" and curr["status"] != "error":
                improvements.append({
                    "ticket": ticket_id,
                    "type": "error_fixed",
                    "previous": "error",
                    "current": curr["status"],
                })
            else:
                unchanged += 1
        else:
            unchanged += 1

    return {
        "regressions": regressions,
        "improvements": improvements,
        "unchanged": unchanged,
        "total": len(previous),
    }


def load_previous_results() -> dict | None:
    """Load the most recent regression results."""
    latest_path = RESULTS_DIR / "regression_latest.json"
    if not latest_path.exists():
        return None

    with open(latest_path, "r") as f:
        return json.load(f)


def run_regression_test():
    """Full regression test: run, compare, report."""
    print("=" * 60)
    print("REGRESSION TEST")
    print("=" * 60)

    previous = load_previous_results()
    if previous:
        print(f"\nFound previous results ({len(previous)} tickets)")
    else:
        print("\nNo previous results — first run")

    print("\nRunning agent on all tickets...")
    current = run_and_capture()

    filepath = save_results(current, "latest")
    print(f"Results saved to: {filepath}")

    if previous:
        comparison = compare_results(current, previous)

        print(f"\n{'=' * 60}")
        print("COMPARISON RESULTS")
        print(f"{'=' * 60}")
        print(f"Total tickets: {comparison['total']}")
        print(f"Unchanged: {comparison['unchanged']}")
        print(f"Improvements: {len(comparison['improvements'])}")
        print(f"REGRESSIONS: {len(comparison['regressions'])}")

        if comparison["regressions"]:
            print(f"\n{'!' * 60}")
            print("REGRESSIONS DETECTED:")
            print(f"{'!' * 60}")
            for reg in comparison["regressions"]:
                print(f"  Ticket {reg['ticket']}: {reg['previous']} -> {reg['current']}")

        if comparison["improvements"]:
            print(f"\nImprovements:")
            for imp in comparison["improvements"]:
                print(f"  Ticket {imp['ticket']}: {imp['previous']} -> {imp['current']}")

        return len(comparison["regressions"]) > 0
    else:
        replied = sum(1 for r in current.values() if r["status"] == "replied")
        escalated = sum(1 for r in current.values() if r["status"] == "escalated")
        errors = sum(1 for r in current.values() if r["status"] == "error")
        print(f"\nFirst run summary: {replied} replied, {escalated} escalated, {errors} errors")
        return False


if __name__ == "__main__":
    has_regressions = run_regression_test()
    if has_regressions:
        print("\nREGRESSIONS FOUND — Fix before proceeding!")
        sys.exit(1)
    else:
        print("\nNo regressions detected")
        sys.exit(0)
