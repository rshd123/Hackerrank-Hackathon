"""
router.py — Reply vs escalate decision engine

Deterministic routing with LLM-assisted response generation.
Deterministic gates override LLM for fraud/unauthorized access.
"""

from agent.schemas import (
    TicketInput,
    ClassificationResult,
    RoutingDecision,
)


def decide_action(
    ticket: TicketInput,
    classification: ClassificationResult,
    retrieved_docs: list[dict],
) -> RoutingDecision:
    """
    Decide whether to reply directly or escalate.

    Routing rules:
    - Reply if: grounded answer available + low/medium urgency + no risk flags
    - Escalate if: no grounded answer OR high urgency OR risk detected OR
      sensitive topic OR out of scope
    """
    # TODO: Implement LLM-assisted response generation
    # TODO: Add schema validation for response
    # TODO: Ground response in retrieved documents

    # Check urgency — high/critical always escalates
    if classification.urgency in ("high", "critical"):
        return RoutingDecision(
            status="escalated",
            justification=f"High urgency ({classification.urgency}) ticket requires human review",
            response=None,
        )

    # Check if we have retrieved documents (grounded answer)
    if not retrieved_docs:
        return RoutingDecision(
            status="escalated",
            justification="No relevant information found in knowledge base",
            response=None,
        )

    # Check platform-specific escalation rules
    if classification.platform == "visa" and classification.category == "security":
        return RoutingDecision(
            status="escalated",
            justification="Visa security tickets require human agent review",
            response=None,
        )

    # Default: reply with grounded context
    # TODO: Generate actual response using LLM + retrieved context
    justification = _build_justification(retrieved_docs)

    return RoutingDecision(
        status="replied",
        justification=justification,
        response="placeholder response",
    )


def _build_justification(retrieved_docs: list[dict]) -> str:
    """Build a grounded justification from retrieved documents."""
    if not retrieved_docs:
        return "No relevant documentation found"

    # Reference specific documents in justification
    sources = [doc["path"] for doc in retrieved_docs[:3]]
    return f"Based on documentation: {', '.join(sources)}"
