"""
settings.py — Configuration for the agent

Model params, thresholds, paths. All tunable from one place.
"""

import os

# Paths
CORPUS_PATH = os.getenv("CORPUS_PATH", "knowledge_base")
TICKETS_PATH = os.getenv("TICKETS_PATH", "data/input_tickets.json")
OUTPUT_PATH = os.getenv("OUTPUT_PATH", "output/agent_output.csv")

# Model settings
CLASSIFICATION_MODEL = os.getenv("CLASSIFICATION_MODEL", "gpt-4o-mini")
RESPONSE_MODEL = os.getenv("RESPONSE_MODEL", "gpt-4o")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.1"))

# RAG settings
TOP_K = int(os.getenv("TOP_K", "5"))
RERANK_TOP_K = int(os.getenv("RERANK_TOP_K", "3"))

# Urgency thresholds
URGENCY_ESCALATION = ["high", "critical"]

# Platforms
PLATFORMS = ["hackerank", "anthropic", "visa"]

# Categories
CATEGORIES = [
    "billing",
    "technical",
    "security",
    "account",
    "api",
    "general",
]

# Security
ENABLE_INJECTION_DETECTION = True
ENABLE_JAILBREAK_DETECTION = True
ENABLE_FRAUD_DETECTION = True
