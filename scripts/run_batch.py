"""
run_batch.py — Batch test runner

Run the agent on all tickets and generate output CSV.
"""

import json
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.core import run_agent
from agent.schemas import TicketInput
from config.settings import TICKETS_PATH, OUTPUT_PATH


def load_tickets() -> list[TicketInput]:
    """Load tickets from JSON."""
    with open(TICKETS_PATH, "r") as f:
        data = json.load(f)
    return [TicketInput(**ticket) for ticket in data]


def save_output(outputs: list, path: str = OUTPUT_PATH):
    """Save agent outputs to CSV."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["ticket_id", "status", "justification", "urgency", "response"])
        writer.writeheader()
        for output in outputs:
            writer.writerow(output.model_dump())

    print(f"Output saved to {path}")


def main():
    """Main entry point for batch processing."""
    print("Loading tickets...")
    tickets = load_tickets()
    print(f"Loaded {len(tickets)} tickets")

    print("Running agent...")
    outputs = run_agent(tickets)

    print("Saving output...")
    save_output(outputs)

    # Summary
    replied = sum(1 for o in outputs if o.status == "replied")
    escalated = sum(1 for o in outputs if o.status == "escalated")
    print(f"\nSummary: {replied} replied, {escalated} escalated")


if __name__ == "__main__":
    main()
