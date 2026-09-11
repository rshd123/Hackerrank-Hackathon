"""
core.py — Main agent pipeline

Ticket in → Classification → RAG retrieval → Routing decision → Output
"""

from agent.classifier import classify_ticket
from agent.rag import retrieve_documents
from agent.router import decide_action
from agent.guardrails import check_security
from agent.schemas import TicketInput, AgentOutput


def process_ticket(ticket: TicketInput) -> AgentOutput:
    """Process a single support ticket through the full agent pipeline."""

    # Step 1: Security gate — deterministic, runs before LLM
    security_result = check_security(ticket)
    if security_result.blocked:
        return AgentOutput(
            ticket_id=ticket.id,
            status="escalated",
            justification=security_result.reason,
            urgency="high",
            response=None,
        )

    # Step 2: Classification — platform, category, intent, urgency
    classification = classify_ticket(ticket)

    # Step 3: RAG retrieval — find relevant docs from corpus
    retrieved = retrieve_documents(ticket, classification)

    # Step 4: Routing decision — reply or escalate
    decision = decide_action(ticket, classification, retrieved)

    # Step 5: Format output
    return AgentOutput(
        ticket_id=ticket.id,
        status=decision.status,
        justification=decision.justification,
        urgency=classification.urgency,
        response=decision.response,
    )


def run_agent(tickets: list[TicketInput]) -> list[AgentOutput]:
    """Process all tickets and return outputs."""
    outputs = []
    for ticket in tickets:
        output = process_ticket(ticket)
        outputs.append(output)
        print(f"Ticket {ticket.id}: {output.status}")
    return outputs
