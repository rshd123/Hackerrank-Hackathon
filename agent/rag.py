"""
rag.py — Local markdown search & retriever

BM25 keyword search (primary) + semantic similarity (secondary) + reranker
"""

import os
from pathlib import Path
from agent.schemas import ClassificationResult


class DocumentStore:
    """Load and index the local markdown corpus."""

    def __init__(self, corpus_path: str = "knowledge_base"):
        self.corpus_path = Path(corpus_path)
        self.documents: list[dict] = []
        self._load_documents()

    def _load_documents(self):
        """Load all markdown files from the corpus."""
        for md_file in self.corpus_path.rglob("*.md"):
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()
            self.documents.append({
                "path": str(md_file.relative_to(self.corpus_path)),
                "content": content,
                "filename": md_file.name,
            })
        print(f"Loaded {len(self.documents)} documents from corpus")

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """
        Search documents using BM25 + semantic hybrid.

        Returns top_k most relevant documents.
        """
        # TODO: Implement BM25 search
        # TODO: Add semantic similarity as secondary
        # TODO: Add reranker for precision
        results = []
        # Placeholder: return first top_k documents
        for doc in self.documents[:top_k]:
            results.append({
                "path": doc["path"],
                "content": doc["content"][:500],
                "score": 0.0,
            })
        return results


# Global document store instance
_store: DocumentStore | None = None


def get_store() -> DocumentStore:
    """Get or initialize the document store."""
    global _store
    if _store is None:
        _store = DocumentStore()
    return _store


def retrieve_documents(ticket, classification: ClassificationResult, top_k: int = 5) -> list[dict]:
    """
    Retrieve relevant documents for a ticket.

    Uses the ticket text + classification context to find
    the most relevant corpus documents.
    """
    store = get_store()

    # Build search query from ticket content
    query = f"{ticket.content}"

    # Search with BM25 + semantic
    results = store.search(query, top_k=top_k)

    return results
