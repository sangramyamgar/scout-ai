"""
Agentic RAG pipeline using LangGraph and LangChain.
Orchestrates query routing, retrieval, reranking, and response generation.
"""

from typing import Annotated, List, Optional, TypedDict

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langgraph.graph import END, StateGraph

from app.core.config import ROLES
from app.core.llm import get_llm_service
from app.core.reranker import get_reranker
from app.core.vectorstore import get_vector_store
from app.guardrails.safety import get_guardrails


class AgentState(TypedDict):
    """State passed between nodes in the LangGraph RAG pipeline."""

    # Input
    query: str
    role: str
    user_id: str

    # Processing
    sanitized_query: str
    guardrails_result: dict
    retrieved_docs: List[Document]
    reranked_docs: List[Document]

    # Output
    response: str
    sources: List[dict]
    metadata: dict
    error: Optional[str]


# ============================================
# LangGraph Node Functions
# ============================================


def guardrails_node(state: AgentState) -> AgentState:
    """
    Apply guardrails to the input query.
    Checks for prompt injection, out-of-scope queries, and sanitizes input.
    """
    guardrails = get_guardrails()

    sanitized_query, result = guardrails.process_query(state["query"])

    return {
        **state,
        "sanitized_query": sanitized_query,
        "guardrails_result": result,
    }


def should_block(state: AgentState) -> str:
    """Determine if query should be blocked based on guardrails."""
    if state.get("guardrails_result", {}).get("blocked", False):
        return "blocked"
    return "continue"


def blocked_response_node(state: AgentState) -> AgentState:
    """Generate response for blocked queries."""
    reason = state.get("guardrails_result", {}).get(
        "reason", "This query cannot be processed"
    )

    return {
        **state,
        "response": f"I'm sorry, but I cannot process this request. {reason}",
        "sources": [],
        "metadata": {"blocked": True, "reason": reason},
    }


def retrieval_node(state: AgentState) -> AgentState:
    """
    Retrieve relevant documents using LangChain vector store.
    Implements RBAC filtering based on user role.
    """
    vector_store = get_vector_store()

    role = state["role"]
    query = state["sanitized_query"]

    # Get allowed collections for this role
    role_config = ROLES.get(role, ROLES["employee"])
    allowed_collections = role_config["collections"]

    # Retrieve documents using LangChain (RBAC filtered)
    docs = vector_store.search(
        query=query,
        departments=allowed_collections,
        top_k=10,  # Get more for reranking
    )

    return {
        **state,
        "retrieved_docs": docs,
    }


def rerank_node(state: AgentState) -> AgentState:
    """
    Re-rank retrieved documents for better precision.
    Uses cross-encoder model via LangChain-compatible reranker.
    """
    reranker = get_reranker()

    reranked = reranker.rerank(
        query=state["sanitized_query"],
        documents=state["retrieved_docs"],
        top_k=5,
    )

    return {
        **state,
        "reranked_docs": reranked,
    }


def citation_check_node(state: AgentState) -> AgentState:
    """
    Validate that we have enough context to answer.
    If no relevant documents found, prepare a "no information" response.
    """
    docs = state.get("reranked_docs", [])

    if not docs:
        return {
            **state,
            "response": "I don't have enough information to answer this question based on the available documents.",
            "sources": [],
            "metadata": {"no_context": True},
        }

    # Check if top documents are sufficiently relevant
    top_score = docs[0].metadata.get("rerank_score", 0) if docs else 0

    if top_score < -5:  # Cross-encoder can give negative scores for irrelevant
        return {
            **state,
            "response": "I couldn't find relevant information to answer your question. Please try rephrasing or ask about a different topic.",
            "sources": [],
            "metadata": {"low_relevance": True, "top_score": top_score},
        }

    return state


def has_context(state: AgentState) -> str:
    """Check if we have context to generate a response."""
    if state.get("response"):
        return "no_context"
    return "has_context"


def generation_node(state: AgentState) -> AgentState:
    """
    Generate response using LangChain LLM with retrieved context.
    Uses LangChain prompt templates and chain patterns.
    """
    llm_service = get_llm_service()
    guardrails = get_guardrails()

    # Filter PII from context before sending to LLM
    filtered_docs = guardrails.filter_context(state["reranked_docs"])

    # Generate response using LangChain
    result = llm_service.generate_response(
        query=state["sanitized_query"],
        context_docs=filtered_docs,
        role=state["role"],
    )

    # Apply guardrails to response (mask any PII in output)
    if result.get("response"):
        result["response"] = guardrails.process_response(result["response"])

    return {
        **state,
        "response": result.get("response", "Error generating response"),
        "sources": result.get("sources", []),
        "metadata": {
            "model_used": result.get("model_used"),
            "context_docs_count": result.get("context_docs_count"),
            "rate_limited": result.get("rate_limited", False),
            "error": result.get("error", False),
            "fallback_used": result.get("fallback_used", False),
            "guardrails_warnings": state.get("guardrails_result", {}).get("warnings", []),
        },
    }


def build_rag_graph() -> StateGraph:
    """
    Build the RAG pipeline as a LangGraph state machine.

    Flow:
    1. Guardrails check (sanitize, check scope, injection)
    2. If blocked → return blocked response
    3. Retrieve documents with LangChain (RBAC filtered)
    4. Re-rank for precision
    5. Citation check (enough context?)
    6. Generate response with LangChain LLM
    """
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("guardrails", guardrails_node)
    workflow.add_node("blocked_response", blocked_response_node)
    workflow.add_node("retrieval", retrieval_node)
    workflow.add_node("rerank", rerank_node)
    workflow.add_node("citation_check", citation_check_node)
    workflow.add_node("generation", generation_node)

    # Set entry point
    workflow.set_entry_point("guardrails")

    # Add conditional edge after guardrails
    workflow.add_conditional_edges(
        "guardrails",
        should_block,
        {
            "blocked": "blocked_response",
            "continue": "retrieval",
        },
    )

    # Linear flow for main path
    workflow.add_edge("blocked_response", END)
    workflow.add_edge("retrieval", "rerank")
    workflow.add_edge("rerank", "citation_check")

    # Conditional edge after citation check
    workflow.add_conditional_edges(
        "citation_check",
        has_context,
        {
            "no_context": END,
            "has_context": "generation",
        },
    )

    workflow.add_edge("generation", END)

    return workflow.compile()


# Global compiled graph
_rag_pipeline = None


def get_rag_pipeline():
    """Get or create the LangGraph RAG pipeline."""
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = build_rag_graph()
    return _rag_pipeline


def run_query(query: str, role: str, user_id: str = "anonymous") -> dict:
    """
    Run a query through the LangGraph RAG pipeline.

    This is the main entry point for processing user queries.
    It orchestrates:
    1. Guardrails validation
    2. RBAC-filtered retrieval via LangChain
    3. Re-ranking for precision
    4. Citation checking
    5. Response generation via LangChain LLM

    Args:
        query: User's question
        role: User's role for RBAC
        user_id: User identifier for tracking

    Returns:
        Dictionary with response, sources, and metadata
    """
    pipeline = get_rag_pipeline()

    # Initial state
    initial_state = {
        "query": query,
        "role": role,
        "user_id": user_id,
        "sanitized_query": "",
        "guardrails_result": {},
        "retrieved_docs": [],
        "reranked_docs": [],
        "response": "",
        "sources": [],
        "metadata": {},
        "error": None,
    }

    # Run the LangGraph pipeline
    result = pipeline.invoke(initial_state)

    return {
        "response": result.get("response", ""),
        "sources": result.get("sources", []),
        "metadata": result.get("metadata", {}),
    }


# ============================================
# LangChain Chain Builder (Alternative API)
# ============================================


def create_langchain_rag_chain(role: str):
    """
    Create a pure LangChain RAG chain for a specific role.
    This is an alternative to the LangGraph pipeline for simpler use cases.

    Args:
        role: User's role for RBAC filtering

    Returns:
        LangChain runnable chain
    """
    from langchain_groq import ChatGroq
    from app.core.config import get_settings

    settings = get_settings()
    vector_store = get_vector_store()

    # Get role-specific retriever
    role_config = ROLES.get(role, ROLES["employee"])
    departments = role_config["collections"]

    # Create multi-collection retriever
    retriever = vector_store.get_multi_collection_retriever(
        departments=departments,
        search_kwargs={"k": 5},
    )

    # Create LLM
    llm = ChatGroq(
        api_key=settings.groq_api_key,
        model=settings.llm_model,
        temperature=0.1,
    )

    # Create prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an AI assistant for the company.
Answer based only on the provided context. Cite sources as [Source N].
If you can't find the answer, say so.

Context:
{context}"""),
        ("human", "{question}"),
    ])

    # Build the chain
    def format_docs(docs):
        return "\n\n".join([f"[Source {i+1}]: {doc.page_content}" for i, doc in enumerate(docs)])

    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain
