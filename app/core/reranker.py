"""
Cross-encoder re-ranker for improved retrieval precision.
Uses sentence-transformers for free, local inference.
"""

from typing import List

from langchain_core.documents import Document
from sentence_transformers import CrossEncoder

from app.core.config import get_settings

settings = get_settings()


class Reranker:
    """
    Cross-encoder re-ranker to improve retrieval precision.
    Re-ranks initial retrieval results based on query-document relevance.
    """

    def __init__(self, model_name: str = None):
        """
        Initialize the re-ranker.

        Args:
            model_name: HuggingFace model name for cross-encoder
        """
        self.model_name = model_name or settings.reranker_model
        self._model = None  # Lazy load

    @property
    def model(self):
        """Lazy-load cross-encoder model on first use."""
        if self._model is None:
            print("🔄 Loading reranker model...")
            self._model = CrossEncoder(self.model_name, max_length=512)
            print("✅ Reranker model loaded")
        return self._model

    def rerank(
        self,
        query: str,
        documents: List[Document],
        top_k: int = 5,
    ) -> List[Document]:
        """
        Re-rank documents based on relevance to query.

        Args:
            query: Search query
            documents: Documents to re-rank
            top_k: Number of top documents to return

        Returns:
            Re-ranked list of documents (most relevant first)
        """
        if not documents:
            return []

        # Create query-document pairs for scoring
        pairs = [(query, doc.page_content) for doc in documents]

        # Get relevance scores
        scores = self.model.predict(pairs)

        # Combine documents with scores
        scored_docs = list(zip(documents, scores))

        # Sort by score (descending)
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        # Add relevance score to metadata and return top_k
        reranked = []
        for doc, score in scored_docs[:top_k]:
            doc.metadata["rerank_score"] = float(score)
            reranked.append(doc)

        return reranked

    def filter_by_threshold(
        self,
        query: str,
        documents: List[Document],
        threshold: float = 0.5,
    ) -> List[Document]:
        """
        Filter documents that don't meet relevance threshold.
        Useful for citation enforcement - only include truly relevant docs.

        Args:
            query: Search query
            documents: Documents to filter
            threshold: Minimum relevance score (0-1)

        Returns:
            Documents meeting the threshold
        """
        if not documents:
            return []

        pairs = [(query, doc.page_content) for doc in documents]
        scores = self.model.predict(pairs)

        filtered = []
        for doc, score in zip(documents, scores):
            if score >= threshold:
                doc.metadata["rerank_score"] = float(score)
                filtered.append(doc)

        # Sort by score
        filtered.sort(key=lambda x: x.metadata["rerank_score"], reverse=True)

        return filtered


# Global reranker instance
_reranker = None


def get_reranker() -> Reranker:
    """Get or create the global reranker instance."""
    global _reranker
    if _reranker is None:
        _reranker = Reranker()
    return _reranker
