"""
guardrails.py — Deterministic security gate

Prompt injection, jailbreak, fraud detection.
Runs BEFORE the LLM to catch adversarial inputs.
"""

import re
from agent.schemas import TicketInput, SecurityResult


# Known prompt injection patterns
INJECTION_PATTERNS = [
    r"ignore (?:all |any )?(?:previous|prior|above) (?:instructions|prompts)",
    r"you are now (?:a |an )?",
    r"act as (?:a |an )?",
    r"pretend (?:you are|to be)",
    r"disregard (?:all |any )?(?:previous|prior)",
    r"system (?:prompt|message)",
    r"<\|system\|>",
    r"\[system\]",
    r"ADMIN OVERRIDE",
    r"DAN mode",
    r"jailbreak",
    r"bypass (?:safety|security|filter)",
]

# Known jailbreak patterns
JAILBREAK_PATTERNS = [
    r"do anything now",
    r"developer mode",
    r"unrestricted mode",
    r"no (?:rules|restrictions|limitations)",
    r"you have no (?:rules|restrictions)",
]

# Fraud/unauthorized access keywords
FRAUD_KEYWORDS = [
    "unauthorized access",
    "account takeover",
    "stolen card",
    "fraud",
    "phishing",
    "identity theft",
    "compromised account",
    "hack",
    "exploit",
]


def check_injection(text: str) -> bool:
    """Check for prompt injection patterns."""
    text_lower = text.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text_lower):
            return True
    return False


def check_jailbreak(text: str) -> bool:
    """Check for jailbreak patterns."""
    text_lower = text.lower()
    for pattern in JAILBREAK_PATTERNS:
        if re.search(pattern, text_lower):
            return True
    return False


def check_fraud(text: str) -> bool:
    """Check for fraud/unauthorized access indicators."""
    text_lower = text.lower()
    for keyword in FRAUD_KEYWORDS:
        if keyword in text_lower:
            return True
    return False


def check_security(ticket: TicketInput) -> SecurityResult:
    """
    Run deterministic security checks on ticket.

    This runs BEFORE the LLM to catch adversarial inputs.
    The LLM cannot override these decisions.
    """
    content = ticket.content

    # Check for prompt injection
    if check_injection(content):
        return SecurityResult(
            blocked=True,
            reason="Prompt injection detected in ticket content",
            threat_type="injection",
        )

    # Check for jailbreak attempts
    if check_jailbreak(content):
        return SecurityResult(
            blocked=True,
            reason="Jailbreak attempt detected in ticket content",
            threat_type="jailbreak",
        )

    # Check for fraud/unauthorized access
    if check_fraud(content):
        return SecurityResult(
            blocked=False,  # Don't block, but flag for escalation
            reason="Fraud or unauthorized access indicators detected",
            threat_type="fraud",
        )

    return SecurityResult(blocked=False)
