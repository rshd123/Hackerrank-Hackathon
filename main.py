"""
main.py — Entry point for the agent

Usage:
    python main.py                  # Process all tickets
    python main.py --ticket <id>    # Process single ticket
    python main.py --test           # Run test suite
"""

import argparse
import json
import sys

from agent.core import process_ticket, run_agent
from agent.schemas import TicketInput


def main():
    parser = argparse.ArgumentParser(description="HackerRank Orchestrate Agent")
    parser.add_argument("--ticket", type=str, help="Process a single ticket by ID")
    parser.add_argument("--test", action="store_true", help="Run test suite")
    parser.add_argument("--input", type=str, default="data/input_tickets.json", help="Input tickets file")
    parser.add_argument("--output", type=str, default="output/agent_output.csv", help="Output file path")
    args = parser.parse_args()

    if args.test:
        from tests.test_tickets import test_all_tickets
        test_all_tickets()
        return

    # Load tickets
    with open(args.input, "r") as f:
        data = json.load(f)
    tickets = [TicketInput(**t) for t in data]

    if args.ticket:
        # Process single ticket
        ticket = next((t for t in tickets if t.id == args.ticket), None)
        if not ticket:
            print(f"Ticket {args.ticket} not found")
            sys.exit(1)
        output = process_ticket(ticket)
        print(json.dumps(output.model_dump(), indent=2))
    else:
        # Process all tickets
        outputs = run_agent(tickets)

        # Save output CSV
        import csv
        from pathlib import Path
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["ticket_id", "status", "justification", "urgency", "response"])
            writer.writeheader()
            for output in outputs:
                writer.writerow(output.model_dump())
        print(f"\nOutput saved to {args.output}")


if __name__ == "__main__":
    main()
