"""
Vector store tool for agentic AI pipelines.

Wraps memory.vector_store.VectorStore so it can be:
- Planned
- Executed
- Evaluated
- Swapped between backends
"""

from typing import List, Dict, Any, Optional
from tools.base import Tool



class VectorStoreTool(Tool):
    """
    Agent-facing vector memory tool.
    """

    name = "vector_store"
    description = (
        "Store text embeddings in vector memory and perform similarity search. "
        "Supports add_texts and similarity_search actions."
    )

    def __init__(self, embedding_fn):
        self.store = VectorStore(embedding_fn)

    # ==============================================================
    # Tool Interface
    # ==============================================================

    def run(self, action: str, **kwargs) -> Dict[str, Any]:
        """
        Entry point for agent execution.

        action:
          - add_texts
          - similarity_search
          - count
          - clear
        """

        if action == "add_texts":
            return self._add_texts(**kwargs)

        if action == "similarity_search":
            return self._similarity_search(**kwargs)

        if action == "count":
            return {"count": self.store.count()}

        if action == "clear":
            self.store.clear()
            return {"status": "cleared"}

        raise ValueError(f"Unsupported vector_store action: {action}")

    # ==============================================================
    # Actions
    # ==============================================================

    def _add_texts(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        return self.store.add_texts(
            texts=texts,
            metadatas=metadatas
        )

    def _similarity_search(
        self,
        query: str,
        k: int = 5
    ) -> Dict[str, Any]:
        return self.store.similarity_search(
            query=query,
            k=k
        )
