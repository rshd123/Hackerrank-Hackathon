"""
test_tickets.py — Regression test suite

Test all 29 tickets and track regressions.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.core import process_ticket
from agent.schemas import TicketInput


def load_tickets(path: str = "data/input_tickets.json") -> list[TicketInput]:
    """Load tickets from JSON file."""
    with open(path, "r") as f:
        data = json.load(f)
    return [TicketInput(**ticket) for ticket in data]


def test_all_tickets():
    """Run agent on all tickets and report results."""
    tickets = load_tickets()
    results = {"replied": 0, "escalated": 0, "errors": 0}

    for ticket in tickets:
        try:
            output = process_ticket(ticket)
            results[output.status] += 1
            print(f"[PASS] Ticket {ticket.id}: {output.status}")
        except Exception as e:
            results["errors"] += 1
            print(f"[FAIL] Ticket {ticket.id}: {e}")

    print(f"\nResults: {results}")
    return results


if __name__ == "__main__":
    test_all_tickets()
