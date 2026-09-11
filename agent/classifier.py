"""
classifier.py — Platform, category, intent, urgency detection

Uses LLM with structured JSON output for classification.
"""

from agent.schemas import TicketInput, ClassificationResult


def classify_ticket(ticket: TicketInput) -> ClassificationResult:
    """
    Classify a ticket into platform, category, intent, and urgency.

    Uses LLM with structured output + schema validation.
    """
    # TODO: Implement LLM-based classification
    # TODO: Add schema validation for structured output
    # TODO: Handle edge cases (unknown platform, ambiguous intent)

    # Placeholder — will be replaced with actual LLM call
    return ClassificationResult(
        platform="unknown",
        category="general",
        intent="information",
        urgency="medium",
    )
