"""
Vector store management using LangChain + ChromaDB.
Handles embedding storage and retrieval with RBAC filtering.
Uses AWS Bedrock Titan for embeddings (fast, no model loading).
"""

import os
from typing import List, Optional, Dict

from langchain_chroma import Chroma
from langchain_aws import BedrockEmbeddings
from langchain_core.documents import Document

from app.core.config import ROLES, get_settings

settings = get_settings()


class LangChainVectorStore:
    """
    LangChain-based vector store with RBAC-aware retrieval.
    Uses Chroma as the underlying vector database.
    Uses AWS Bedrock Titan for embeddings.
    Creates separate collections per department for access control.
    """

    def __init__(self, persist_directory: str = None):
        """
        Initialize the vector store.

        Args:
            persist_directory: Directory for persistent storage
        """
        self.persist_directory = persist_directory or settings.chroma_persist_directory
        os.makedirs(self.persist_directory, exist_ok=True)

        # Lazy-load embeddings (don't load until first use)
        self._embeddings = None

        # Store collection instances
        self._collections: Dict[str, Chroma] = {}

    @property
    def embeddings(self):
        """Lazy-load AWS Bedrock embeddings on first access."""
        if self._embeddings is None:
            print("🔄 Initializing AWS Bedrock embeddings...")
            self._embeddings = BedrockEmbeddings(
                model_id="amazon.titan-embed-text-v1",
                region_name="us-east-1",
            )
            print("✅ Bedrock embeddings ready")
        return self._embeddings

    def _get_collection_name(self, department: str) -> str:
        """Get a valid ChromaDB collection name for a department."""
        # ChromaDB requires names to be 3-512 chars, alphanumeric with .-_
        # Prefix with 'dept_' to ensure minimum length
        return f"dept_{department}"

    def _get_collection_path(self, collection_name: str) -> str:
        """Get the persist path for a collection."""
        return os.path.join(self.persist_directory, collection_name)

    def get_or_create_collection(self, department: str) -> Chroma:
        """Get or create a LangChain Chroma collection for a department."""
        collection_name = self._get_collection_name(department)
        
        if department not in self._collections:
            self._collections[department] = Chroma(
                collection_name=collection_name,
                embedding_function=self.embeddings,  # Uses lazy-loaded property
                persist_directory=self._get_collection_path(collection_name),
            )
        return self._collections[department]

    def add_documents(self, department: str, documents: List[Document]) -> int:
        """
        Add documents to a department's collection using LangChain.

        Args:
            department: Department name (collection name)
            documents: List of LangChain Document objects

        Returns:
            Number of documents added
        """
        if not documents:
            return 0

        collection = self.get_or_create_collection(department)

        # Add documents using LangChain's Chroma integration
        collection.add_documents(documents)

        return len(documents)

    def similarity_search(
        self,
        query: str,
        department: str,
        k: int = 5,
    ) -> List[Document]:
        """
        Search within a single department's collection.

        Args:
            query: Search query
            department: Department to search
            k: Number of results

        Returns:
            List of relevant documents
        """
        try:
            collection = self.get_or_create_collection(department)
            results = collection.similarity_search(query, k=k)
            
            # Add collection name to metadata
            for doc in results:
                doc.metadata["collection"] = department
            
            return results
        except Exception as e:
            print(f"  ⚠ Error searching {department}: {e}")
            return []

    def similarity_search_with_score(
        self,
        query: str,
        department: str,
        k: int = 5,
    ) -> List[tuple[Document, float]]:
        """
        Search with relevance scores.

        Args:
            query: Search query
            department: Department to search
            k: Number of results

        Returns:
            List of (document, score) tuples
        """
        try:
            collection = self.get_or_create_collection(department)
            results = collection.similarity_search_with_score(query, k=k)
            
            # Add collection name to metadata
            for doc, score in results:
                doc.metadata["collection"] = department
                doc.metadata["similarity_score"] = score
            
            return results
        except Exception as e:
            print(f"  ⚠ Error searching {department}: {e}")
            return []

    def search(
        self,
        query: str,
        departments: List[str],
        top_k: int = 5,
    ) -> List[Document]:
        """
        Search across multiple department collections (RBAC-filtered).

        Args:
            query: Search query
            departments: List of departments to search (based on user role)
            top_k: Number of results per collection

        Returns:
            List of relevant documents with metadata
        """
        all_results = []

        for dept in departments:
            results = self.similarity_search_with_score(query, dept, k=top_k)
            all_results.extend(results)

        # Sort by score (lower distance = more similar in Chroma)
        all_results.sort(key=lambda x: x[1])

        # Return just documents, limited to top_k total
        return [doc for doc, _ in all_results[:top_k]]

    def search_by_role(
        self,
        query: str,
        role: str,
        top_k: int = 5,
    ) -> List[Document]:
        """
        Search with automatic RBAC filtering based on user role.

        Args:
            query: Search query
            role: User's role (determines which collections to search)
            top_k: Number of results to return

        Returns:
            List of relevant documents the user has access to
        """
        role_config = ROLES.get(role)
        if not role_config:
            raise ValueError(f"Unknown role: {role}")

        allowed_collections = role_config["collections"]
        return self.search(query, allowed_collections, top_k)

    def as_retriever(self, department: str, **kwargs):
        """
        Get a LangChain retriever for a specific department.
        Useful for building LangChain chains and agents.

        Args:
            department: Department collection to retrieve from
            **kwargs: Additional arguments for retriever

        Returns:
            LangChain retriever instance
        """
        collection = self.get_or_create_collection(department)
        return collection.as_retriever(**kwargs)

    def get_multi_collection_retriever(self, departments: List[str], **kwargs):
        """
        Create a retriever that searches across multiple departments.
        Uses LangChain's EnsembleRetriever pattern.

        Args:
            departments: List of departments to search
            **kwargs: Additional arguments for retrievers

        Returns:
            Combined retriever for multiple collections
        """
        from langchain.retrievers import EnsembleRetriever

        retrievers = []
        weights = []

        for dept in departments:
            retriever = self.as_retriever(dept, **kwargs)
            retrievers.append(retriever)
            weights.append(1.0)  # Equal weight for all departments

        if not retrievers:
            raise ValueError("No valid departments to create retriever")

        # Normalize weights
        total = sum(weights)
        weights = [w / total for w in weights]

        return EnsembleRetriever(
            retrievers=retrievers,
            weights=weights,
        )

    def get_collection_stats(self) -> dict:
        """Get statistics about all collections."""
        stats = {}

        for dept in ROLES["c_level"]["collections"]:  # All possible departments
            try:
                collection = self.get_or_create_collection(dept)
                # Get count from underlying Chroma collection
                count = collection._collection.count()
                stats[dept] = {"count": count}
            except Exception:
                stats[dept] = {"count": 0}

        return stats

    def clear_collection(self, department: str):
        """Delete a specific collection."""
        try:
            collection = self.get_or_create_collection(department)
            collection.delete_collection()
            if department in self._collections:
                del self._collections[department]
        except Exception as e:
            print(f"Error clearing collection {department}: {e}")

    def clear_all(self):
        """Delete all collections (use with caution)."""
        for dept in list(self._collections.keys()):
            self.clear_collection(dept)


# Backwards compatible aliases
VectorStore = LangChainVectorStore

# Global vector store instance
_vector_store: Optional[LangChainVectorStore] = None


def get_vector_store() -> LangChainVectorStore:
    """Get or create the global vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = LangChainVectorStore()
    return _vector_store


def initialize_vector_store(data_dir: str = "data") -> LangChainVectorStore:
    """
    Initialize vector store with all department documents.

    Args:
        data_dir: Directory containing department data folders

    Returns:
        Initialized VectorStore instance
    """
    from app.core.ingestion import DocumentIngestionPipeline

    store = get_vector_store()
    pipeline = DocumentIngestionPipeline()

    print("\n📚 Processing documents with LangChain...")

    # Load and index all documents
    all_docs = pipeline.process_all_departments(data_dir)

    print("\n📥 Adding to vector store...")
    for department, documents in all_docs.items():
        count = store.add_documents(department, documents)
        print(f"  ✓ Indexed {count} chunks in '{department}' collection")

    return store


if __name__ == "__main__":
    # Test vector store
    print("🔧 Testing LangChain Vector Store")
    print("=" * 50)

    store = initialize_vector_store()

    print("\n📊 Collection Stats:")
    for name, stats in store.get_collection_stats().items():
        print(f"  {name}: {stats['count']} documents")

    # Test search
    print("\n🔍 Test search (finance role):")
    results = store.search_by_role("What is the gross margin?", "finance", top_k=3)
    for doc in results:
        print(f"  - [{doc.metadata.get('department', 'unknown')}] {doc.page_content[:100]}...")
