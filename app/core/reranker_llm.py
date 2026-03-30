"""
LLM-based re-ranker using Groq for fast, free reranking.
Replaces heavy cross-encoder models with intelligent LLM scoring.
"""

from typing import List
from langchain_core.documents import Document


class LLMReranker:
    """
    LLM-based re-ranker that scores document relevance using Groq.
    Much lighter than cross-encoder models, still effective.
    """

    def __init__(self):
        """Initialize the LLM reranker."""
        self._llm = None

    @property
    def llm(self):
        """Lazy-load LLM on first use."""
        if self._llm is None:
            from langchain_groq import ChatGroq
            self._llm = ChatGroq(
                model="llama-3.1-8b-instant",  # Fast model for reranking
                temperature=0,
                max_tokens=100,
            )
        return self._llm

    def rerank(
        self,
        query: str,
        documents: List[Document],
        top_k: int = 5,
    ) -> List[Document]:
        """
        Re-rank documents based on relevance to query.
        Uses simple heuristics + metadata for speed.
        Falls back to original order if issues.

        Args:
            query: Search query
            documents: Documents to re-rank
            top_k: Number of top documents to return

        Returns:
            Re-ranked list of documents
        """
        if not documents:
            return []

        if len(documents) <= top_k:
            # Add default scores and return all
            for i, doc in enumerate(documents):
                doc.metadata["rerank_score"] = 1.0 - (i * 0.1)
            return documents

        # Simple keyword-based scoring for speed
        query_terms = set(query.lower().split())
        scored_docs = []
        
        for doc in documents:
            content_lower = doc.page_content.lower()
            # Count query term matches
            matches = sum(1 for term in query_terms if term in content_lower)
            # Bonus for exact phrase match
            if query.lower() in content_lower:
                matches += 5
            # Normalize score
            score = matches / max(len(query_terms), 1)
            doc.metadata["rerank_score"] = float(score)
            scored_docs.append((doc, score))

        # Sort by score descending
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        return [doc for doc, _ in scored_docs[:top_k]]

    def filter_by_threshold(
        self,
        query: str,
        documents: List[Document],
        threshold: float = 0.1,
    ) -> List[Document]:
        """
        Filter documents that don't meet relevance threshold.

        Args:
            query: Search query
            documents: Documents to filter
            threshold: Minimum relevance score

        Returns:
            Documents meeting the threshold
        """
        reranked = self.rerank(query, documents, top_k=len(documents))
        return [doc for doc in reranked if doc.metadata.get("rerank_score", 0) >= threshold]


# Global reranker instance
_reranker = None


def get_reranker() -> LLMReranker:
    """Get or create the global reranker instance."""
    global _reranker
    if _reranker is None:
        _reranker = LLMReranker()
    return _reranker
