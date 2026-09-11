# HackerRank Orchestrate Agent

AI support triage agent that handles tickets across HackerRank, Anthropic, and Visa.

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Process all tickets
python main.py

# Process single ticket
python main.py --ticket <id>

# Run test suite
python main.py --test
```

## Project Structure

```
├── agent/                  # Core agent code
│   ├── core.py            # Main pipeline
│   ├── rag.py             # Document retrieval
│   ├── schemas.py         # Pydantic models
│   ├── classifier.py      # Ticket classification
│   ├── guardrails.py      # Security checks
│   └── router.py          # Reply/escalate decisions
├── knowledge_base/         # 774 markdown documents
├── data/                   # Input tickets
├── output/                 # Agent output CSV
├── config/                 # Settings
├── tests/                  # Test suite
├── scripts/                # Batch runners
├── transcripts/            # AI tool transcripts
└── main.py                # Entry point
```

## Architecture

1. **Security Gate** — Deterministic checks for injection/jailbreak/fraud
2. **Classification** — Platform, category, intent, urgency
3. **RAG Retrieval** — BM25 + semantic search + reranker
4. **Routing** — Reply with grounded context or escalate with justification
5. **Output** — Structured CSV with status, justification, urgency
