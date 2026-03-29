"""
LLM integration using LangChain with Groq Cloud (free inference).
Implements RAG chain with rate limiting and fallback handling.
"""

import time
from typing import List, Optional

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_groq import ChatGroq

from app.core.config import GROQ_RATE_LIMITS, get_settings

settings = get_settings()


# LangChain Prompt Templates
RAG_SYSTEM_PROMPT = """You are Scout, an AI knowledge assistant for the company. Your role is to help employees find comprehensive information from company documents.

IMPORTANT RULES:
1. Only answer based on the provided context. Do not make up information.
2. If the context doesn't contain enough information, say "I couldn't find relevant information to answer your question. Please try rephrasing or ask about a different topic."
3. Provide detailed, thorough answers - aim for at least 2-3 paragraphs when the context supports it.
4. Structure your answers clearly with key points, numbers, and specific details from the documents.
5. Be professional and helpful.
6. The user has '{role}' access level - only provide information appropriate for their role.

FORMATTING GUIDELINES:
- Use clear paragraphs to organize information
- Include specific numbers, percentages, and dates when available
- Highlight key takeaways
- Don't use [Source N] references in your response

CONTEXT:
{context}

Remember: Provide comprehensive, well-structured answers using all relevant information from the context."""

RAG_USER_PROMPT = "{question}"


class LangChainLLMService:
    """
    LangChain-based LLM service using Groq Cloud with rate limiting.

    Groq Free Tier Limits (llama-3.3-70b-versatile):
    - 30 requests per minute (RPM)
    - 1,000 requests per day (RPD)
    - 12,000 tokens per minute (TPM)
    - 100,000 tokens per day (TPD)
    """

    def __init__(self):
        self.primary_model = settings.llm_model
        self.fallback_model = "llama-3.1-8b-instant"
        self._llm_available = False

        # Track usage for rate limiting
        self._request_timestamps = []
        self._daily_requests = 0
        self._last_reset_day = time.strftime("%Y-%m-%d")

        # Initialize LangChain components
        self._init_llm()
        if self._llm_available:
            self._init_chains()

    def _init_llm(self):
        """Initialize the Groq LLM using LangChain."""
        api_key = settings.groq_api_key
        
        # Check if API key is set and not a placeholder
        if not api_key or api_key in ["your_groq_api_key_here", "", "YOUR_API_KEY"]:
            print("⚠️  WARNING: GROQ_API_KEY not set or is placeholder!")
            print("   Get a free key at: https://console.groq.com/keys")
            print("   Add it to your .env file and restart the server")
            self._llm_available = False
            return
        
        self._llm_available = True

        # Primary LLM (larger, higher quality)
        self.llm = ChatGroq(
            api_key=api_key,
            model=self.primary_model,
            temperature=0.1,
            max_tokens=2048,
        )

        # Fallback LLM (smaller, higher rate limits)
        self.fallback_llm = ChatGroq(
            api_key=api_key,
            model=self.fallback_model,
            temperature=0.1,
            max_tokens=2048,
        )

    def _init_chains(self):
        """Initialize LangChain chains for RAG."""
        # RAG prompt template
        self.rag_prompt = ChatPromptTemplate.from_messages([
            ("system", RAG_SYSTEM_PROMPT),
            ("human", RAG_USER_PROMPT),
        ])

        # Simple QA prompt for general questions
        self.simple_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant for the company. Answer questions professionally and concisely."),
            ("human", "{question}"),
        ])

    def _format_context(self, documents: List[Document]) -> tuple[str, List[dict]]:
        """Format documents into context string with source tracking."""
        context_parts = []
        sources = []

        for i, doc in enumerate(documents, 1):
            context_parts.append(f"[Source {i}]: {doc.page_content}")
            sources.append({
                "index": i,
                "department": doc.metadata.get("department", "unknown"),
                "filename": doc.metadata.get("filename", "unknown"),
                "chunk": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
            })

        return "\n\n".join(context_parts), sources

    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits."""
        current_time = time.time()
        current_day = time.strftime("%Y-%m-%d")

        # Reset daily counter if new day
        if current_day != self._last_reset_day:
            self._daily_requests = 0
            self._last_reset_day = current_day

        # Clean old timestamps (older than 1 minute)
        self._request_timestamps = [
            ts for ts in self._request_timestamps if current_time - ts < 60
        ]

        limits = GROQ_RATE_LIMITS.get(self.primary_model, GROQ_RATE_LIMITS["llama-3.3-70b-versatile"])

        # Check RPM and RPD
        if len(self._request_timestamps) >= limits["rpm"]:
            return False
        if self._daily_requests >= limits["rpd"]:
            return False

        return True

    def _record_request(self):
        """Record a request for rate limiting."""
        self._request_timestamps.append(time.time())
        self._daily_requests += 1

    def create_rag_chain(self, role: str):
        """
        Create a LangChain RAG chain for a specific role.

        Args:
            role: User's role for context

        Returns:
            LangChain runnable chain
        """
        # Create the RAG chain
        chain = (
            self.rag_prompt
            | self.llm
            | StrOutputParser()
        )

        return chain

    def generate_response(
        self,
        query: str,
        context_docs: List[Document],
        role: str,
        chat_history: Optional[List] = None,
    ) -> dict:
        """
        Generate a response using LangChain RAG chain.

        Args:
            query: User's question
            context_docs: Retrieved documents for context
            role: User's role (for personalization)
            chat_history: Optional conversation history

        Returns:
            Dictionary with response, sources, and metadata
        """
        # Check if LLM is available
        if not self._llm_available:
            return {
                "response": "⚠️ LLM service not available. Please set GROQ_API_KEY in your .env file. Get a free key at https://console.groq.com/keys",
                "sources": [],
                "error": True,
                "llm_unavailable": True,
            }
        
        # Check rate limits
        if not self._check_rate_limit():
            return {
                "response": "I'm currently rate limited. Please try again in a minute.",
                "sources": [],
                "rate_limited": True,
            }

        # Format context from documents
        context, sources = self._format_context(context_docs)

        if not context:
            return {
                "response": "I don't have enough information to answer this question based on the available documents.",
                "sources": [],
                "no_context": True,
            }

        try:
            # Create and invoke the RAG chain
            self._record_request()

            # Use LangChain chain
            chain = self.create_rag_chain(role)

            response_text = chain.invoke({
                "context": context,
                "role": role,
                "question": query,
            })

            return {
                "response": response_text,
                "sources": sources,
                "model_used": self.primary_model,
                "context_docs_count": len(context_docs),
            }

        except Exception as e:
            error_str = str(e).lower()

            # Handle rate limiting with fallback
            if "rate" in error_str or "429" in error_str:
                try:
                    # Try fallback model
                    fallback_chain = (
                        self.rag_prompt
                        | self.fallback_llm
                        | StrOutputParser()
                    )

                    response_text = fallback_chain.invoke({
                        "context": context,
                        "role": role,
                        "question": query,
                    })

                    return {
                        "response": response_text,
                        "sources": sources,
                        "model_used": self.fallback_model,
                        "context_docs_count": len(context_docs),
                        "fallback_used": True,
                    }

                except Exception as e2:
                    return {
                        "response": f"Service temporarily unavailable: {str(e2)}",
                        "sources": [],
                        "error": True,
                    }
            else:
                return {
                    "response": f"Error generating response: {str(e)}",
                    "sources": [],
                    "error": True,
                }

    def is_available(self) -> bool:
        """Check if LLM is configured and available."""
        return self._llm_available

    def get_usage_stats(self) -> dict:
        """Get current usage statistics."""
        limits = GROQ_RATE_LIMITS.get(self.primary_model, GROQ_RATE_LIMITS["llama-3.3-70b-versatile"])
        return {
            "requests_this_minute": len(self._request_timestamps),
            "requests_today": self._daily_requests,
            "rpm_limit": limits["rpm"],
            "rpd_limit": limits["rpd"],
            "remaining_rpm": max(0, limits["rpm"] - len(self._request_timestamps)),
            "remaining_rpd": max(0, limits["rpd"] - self._daily_requests),
            "model": self.primary_model,
        }


# Backwards compatible alias
LLMService = LangChainLLMService

# Global LLM service instance
_llm_service: Optional[LangChainLLMService] = None


def get_llm_service() -> LangChainLLMService:
    """Get or create the global LLM service instance."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LangChainLLMService()
    return _llm_service
