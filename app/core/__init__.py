"""Core modules for Scout."""

from app.core.config import get_settings, ROLES, GROQ_RATE_LIMITS
from app.core.vectorstore import get_vector_store, initialize_vector_store
from app.core.llm import get_llm_service
from app.core.retrieval import get_hybrid_retriever
from app.core.reranker_llm import get_reranker  # Use lightweight LLM reranker

__all__ = [
    "get_settings",
    "ROLES",
    "GROQ_RATE_LIMITS",
    "get_vector_store",
    "initialize_vector_store",
    "get_llm_service",
    "get_hybrid_retriever",
    "get_reranker",
]