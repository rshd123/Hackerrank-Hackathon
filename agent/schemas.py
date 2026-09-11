"""
schemas.py — Pydantic JSON schemas

Structured output models for classification, routing, and final output.
"""

from pydantic import BaseModel, Field
from typing import Optional


class TicketInput(BaseModel):
    """Input ticket from the evaluation bank."""
    id: str
    content: str
    platform: Optional[str] = None


class ClassificationResult(BaseModel):
    """Output from the classification layer."""
    platform: str = Field(description="Platform: hackerank, anthropic, visa, or unknown")
    category: str = Field(description="Category: billing, technical, security, general, etc.")
    intent: str = Field(description="Intent: information, action, escalation, complaint")
    urgency: str = Field(description="Urgency: low, medium, high, critical")


class SecurityResult(BaseModel):
    """Output from the security gate."""
    blocked: bool = Field(description="Whether ticket was blocked by security")
    reason: Optional[str] = Field(default=None, description="Reason for blocking")
    threat_type: Optional[str] = Field(default=None, description="Type of threat detected")


class RetrievedDocument(BaseModel):
    """A retrieved document from the corpus."""
    path: str
    content: str
    score: float


class RoutingDecision(BaseModel):
    """Output from the routing engine."""
    status: str = Field(description="replied or escalated")
    justification: str = Field(description="Grounded justification from corpus")
    response: Optional[str] = Field(default=None, description="Response text if replied")


class AgentOutput(BaseModel):
    """Final output for a single ticket."""
    ticket_id: str
    status: str = Field(description="replied or escalated")
    justification: str = Field(description="Grounded justification from corpus")
    urgency: str = Field(description="low, medium, high, critical")
    response: Optional[str] = Field(default=None, description="Response text if replied")
