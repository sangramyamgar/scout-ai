"""
Hybrid retrieval combining vector search with BM25 for better results.
"""

from typing import List

from langchain_core.documents import Document
from rank_bm25 import BM25Okapi

from app.core.config import ROLES
from app.core.vectorstore import get_vector_store


class HybridRetriever:
    """
    Combines semantic vector search with keyword-based BM25 retrieval.
    This improves recall by capturing both semantic meaning and exact matches.
    """

    def __init__(self, alpha: float = 0.5):
        """
        Initialize hybrid retriever.

        Args:
            alpha: Weight for vector search (1-alpha = BM25 weight)
                   0.5 = equal weight, 0.7 = favor semantic search
        """
        self.alpha = alpha
        self.vector_store = get_vector_store()
        self._bm25_indices = {}  # Cache BM25 indices per collection
        self._doc_cache = {}  # Cache documents for BM25

    def _build_bm25_index(self, documents: List[Document], collection_name: str):
        """Build BM25 index for a set of documents."""
        # Tokenize documents
        tokenized_docs = [doc.page_content.lower().split() for doc in documents]

        # Create BM25 index
        bm25 = BM25Okapi(tokenized_docs)

        self._bm25_indices[collection_name] = bm25
        self._doc_cache[collection_name] = documents

    def _bm25_search(
        self,
        query: str,
        collection_name: str,
        top_k: int = 5,
    ) -> List[tuple[Document, float]]:
        """
        Search using BM25 algorithm.

        Returns:
            List of (document, score) tuples
        """
        if collection_name not in self._bm25_indices:
            return []

        bm25 = self._bm25_indices[collection_name]
        docs = self._doc_cache[collection_name]

        # Tokenize query
        tokenized_query = query.lower().split()

        # Get BM25 scores
        scores = bm25.get_scores(tokenized_query)

        # Combine docs with scores and sort
        doc_scores = [(doc, score) for doc, score in zip(docs, scores)]
        doc_scores.sort(key=lambda x: x[1], reverse=True)

        return doc_scores[:top_k]

    def retrieve(
        self,
        query: str,
        role: str,
        top_k: int = 5,
        use_hybrid: bool = True,
    ) -> List[Document]:
        """
        Retrieve documents using hybrid search.

        Args:
            query: Search query
            role: User's role for RBAC filtering
            top_k: Number of results to return
            use_hybrid: If False, use vector search only

        Returns:
            List of relevant documents
        """
        role_config = ROLES.get(role)
        if not role_config:
            raise ValueError(f"Unknown role: {role}")

        allowed_collections = role_config["collections"]

        # Vector search
        vector_results = self.vector_store.search(
            query=query,
            departments=allowed_collections,
            top_k=top_k * 2,  # Get more for fusion
        )

        if not use_hybrid:
            return vector_results[:top_k]

        # BM25 search across allowed collections
        bm25_results = []
        for collection in allowed_collections:
            results = self._bm25_search(query, collection, top_k)
            bm25_results.extend(results)

        if not bm25_results:
            return vector_results[:top_k]

        # Reciprocal Rank Fusion (RRF) to combine results
        return self._reciprocal_rank_fusion(
            vector_results,
            [doc for doc, _ in bm25_results],
            top_k,
        )

    def _reciprocal_rank_fusion(
        self,
        vector_results: List[Document],
        bm25_results: List[Document],
        top_k: int,
        k: int = 60,
    ) -> List[Document]:
        """
        Combine results using Reciprocal Rank Fusion.

        RRF score = sum(1 / (k + rank)) for each result list

        Args:
            vector_results: Results from vector search
            bm25_results: Results from BM25 search
            top_k: Number of results to return
            k: RRF constant (default 60)

        Returns:
            Fused and re-ranked results
        """
        # Calculate RRF scores
        doc_scores = {}

        # Score vector results
        for rank, doc in enumerate(vector_results):
            doc_key = doc.page_content[:100]  # Use content prefix as key
            score = self.alpha * (1 / (k + rank + 1))
            doc_scores[doc_key] = doc_scores.get(doc_key, 0) + score
            if doc_key not in doc_scores:
                doc_scores[doc_key] = {"score": 0, "doc": doc}
            else:
                doc_scores[doc_key] = {"score": score, "doc": doc}

        # Score BM25 results
        for rank, doc in enumerate(bm25_results):
            doc_key = doc.page_content[:100]
            score = (1 - self.alpha) * (1 / (k + rank + 1))
            if doc_key in doc_scores:
                doc_scores[doc_key]["score"] += score
            else:
                doc_scores[doc_key] = {"score": score, "doc": doc}

        # Sort by combined score
        sorted_docs = sorted(
            doc_scores.values(),
            key=lambda x: x["score"],
            reverse=True,
        )

        return [item["doc"] for item in sorted_docs[:top_k]]

    def index_documents_for_bm25(self, department: str, documents: List[Document]):
        """Add documents to BM25 index for a department."""
        self._build_bm25_index(documents, department)


def get_hybrid_retriever() -> HybridRetriever:
    """Get or create hybrid retriever instance."""
    return HybridRetriever(alpha=0.6)  # Slightly favor semantic search
