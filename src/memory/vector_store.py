"""
Vector store abstraction for agentic AI memory.

Supports:
- In-memory vector storage (default)
- Pluggable embedding functions
- Metadata + document tracking
- Planner / Executor friendly interface
"""

from typing import List, Dict, Any, Optional
from uuid import uuid4
import math


class VectorStore:
    """
    Simple vector store for agent memory, RAG, and retrieval.

    This implementation is intentionally minimal and deterministic.
    Swap out the embedding or storage backend without changing agents.
    """

    def __init__(self, embedding_fn):
        """
        embedding_fn: Callable[[str], List[float]]
        """
        self.embedding_fn = embedding_fn
        self.vectors: List[Dict[str, Any]] = []

    # ==============================================================
    # Public API (Agent-facing)
    # ==============================================================

    def add_texts(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Embed and store text documents.
        """
        if metadatas is None:
            metadatas = [{} for _ in texts]

        records = []

        for text, metadata in zip(texts, metadatas):
            embedding = self.embedding_fn(text)

            record = {
                "id": str(uuid4()),
                "text": text,
                "embedding": embedding,
                "metadata": metadata
            }

            self.vectors.append(record)
            records.append(record["id"])

        return {
            "status": "success",
            "stored": len(records),
            "ids": records
        }

    def similarity_search(
        self,
        query: str,
        k: int = 5
    ) -> Dict[str, Any]:
        """
        Return top-k most similar documents to the query.
        """
        query_embedding = self.embedding_fn(query)

        scored = []
        for record in self.vectors:
            score = self._cosine_similarity(
                query_embedding,
                record["embedding"]
            )
            scored.append((score, record))

        scored.sort(key=lambda x: x[0], reverse=True)
        top_k = scored[:k]

        return {
            "query": query,
            "results": [
                {
                    "id": r["id"],
                    "score": score,
                    "text": r["text"],
                    "metadata": r["metadata"]
                }
                for score, r in top_k
            ]
        }

    def count(self) -> int:
        """
        Return number of stored vectors.
        """
        return len(self.vectors)

    def clear(self):
        """
        Clear all stored vectors.
        """
        self.vectors.clear()

    # ==============================================================
    # Internal helpers
    # ==============================================================

    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(b * b for b in v2))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot / (norm1 * norm2)
