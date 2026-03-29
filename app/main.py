"""
Scout AI - Enterprise Knowledge Assistant
Production-grade RAG with RBAC, Guardrails, and Agentic AI
"""

import time
from collections import defaultdict
from datetime import datetime
from typing import Dict, Optional

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel

from app.core.config import ROLES, get_settings

settings = get_settings()

# ============================================
# FastAPI App Setup
# ============================================

app = FastAPI(
    title="Scout AI - Enterprise Knowledge Assistant",
    description="AI-powered internal chatbot with Role-Based Access Control",
    version="1.0.0",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",   # Local development
        "http://localhost:5173",   # Vite dev server
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "https://*.pages.dev",     # Cloudflare Pages
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBasic()

# ============================================
# User Database (In production, use a real DB)
# Maps API usernames to credentials for backend auth
# Frontend uses professional email/password pairs
# ============================================

users_db: Dict[str, Dict[str, str]] = {
    # Engineering
    "Tony": {"password": "password123", "role": "engineering"},
    "Peter": {"password": "pete123", "role": "engineering"},
    # Marketing
    "Bruce": {"password": "securepass", "role": "marketing"},
    "Sid": {"password": "sidpass123", "role": "marketing"},
    # Finance
    "Sam": {"password": "financepass", "role": "finance"},
    "Maria": {"password": "maria123", "role": "finance"},
    # HR
    "Natasha": {"password": "hrpass123", "role": "hr"},
    "Carol": {"password": "carol123", "role": "hr"},
    # C-Level (Full Access)
    "Nick": {"password": "director123", "role": "c_level"},
    "Pepper": {"password": "ceo123", "role": "c_level"},
    # Regular Employee
    "Happy": {"password": "employee123", "role": "employee"},
    "Scott": {"password": "emp123", "role": "employee"},
}

# ============================================
# Rate Limiting (In-memory for demo)
# ============================================

request_counts: Dict[str, list] = defaultdict(list)


def check_rate_limit(username: str) -> bool:
    """Check if user has exceeded daily request limit."""
    today = datetime.now().strftime("%Y-%m-%d")
    user_requests = request_counts[username]

    # Filter to today's requests
    today_requests = [ts for ts in user_requests if ts.startswith(today)]
    request_counts[username] = today_requests

    return len(today_requests) < settings.max_requests_per_user_per_day


def record_request(username: str):
    """Record a request for rate limiting."""
    request_counts[username].append(datetime.now().isoformat())


# ============================================
# Request/Response Models
# ============================================


class ChatRequest(BaseModel):
    """Chat request body."""

    message: str
    include_sources: bool = True


class ChatResponse(BaseModel):
    """Chat response body."""

    response: str
    sources: list = []
    metadata: dict = {}


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    timestamp: str


# ============================================
# Authentication
# ============================================


def authenticate(credentials: HTTPBasicCredentials = Depends(security)) -> dict:
    """Authenticate user and return user info."""
    username = credentials.username
    password = credentials.password

    user = users_db.get(username)
    if not user or user["password"] != password:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    if not check_rate_limit(username):
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Maximum {settings.max_requests_per_user_per_day} requests per day.",
        )

    return {"username": username, "role": user["role"]}


# ============================================
# Endpoints
# ============================================


@app.get("/health", response_model=HealthResponse)
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/login")
def login(user: dict = Depends(authenticate)):
    """Login endpoint - validates credentials and returns user info."""
    role_config = ROLES.get(user["role"], {})
    return {
        "message": f"Welcome {user['username']}!",
        "role": user["role"],
        "role_name": role_config.get("name", user["role"]),
        "access": role_config.get("collections", []),
    }


@app.get("/roles")
def get_roles():
    """Get available roles and their permissions (public endpoint)."""
    return {
        role: {
            "name": config["name"],
            "description": config["description"],
            "access": config["collections"],
        }
        for role, config in ROLES.items()
    }


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, user: dict = Depends(authenticate)):
    """
    Main chat endpoint - processes questions using RAG pipeline.

    Requires authentication. Applies RBAC based on user role.
    """
    from app.agents.rag_pipeline import run_query

    # Record request for rate limiting
    record_request(user["username"])

    # Run the RAG pipeline
    result = run_query(
        query=request.message,
        role=user["role"],
        user_id=user["username"],
    )

    # Format response
    response = ChatResponse(
        response=result.get("response", "Error processing request"),
        sources=result.get("sources", []) if request.include_sources else [],
        metadata={
            **result.get("metadata", {}),
            "user": user["username"],
            "role": user["role"],
        },
    )

    return response


@app.get("/usage")
def get_usage(user: dict = Depends(authenticate)):
    """Get user's API usage statistics."""
    from app.core.llm import get_llm_service

    today = datetime.now().strftime("%Y-%m-%d")
    today_requests = [
        ts for ts in request_counts[user["username"]] if ts.startswith(today)
    ]

    # Get LLM usage stats
    try:
        llm_stats = get_llm_service().get_usage_stats()
    except Exception:
        llm_stats = {"error": "LLM service not initialized"}

    return {
        "user": user["username"],
        "requests_today": len(today_requests),
        "max_requests_per_day": settings.max_requests_per_user_per_day,
        "remaining_requests": settings.max_requests_per_user_per_day - len(today_requests),
        "llm_usage": llm_stats,
    }


@app.get("/collections")
def get_collections(user: dict = Depends(authenticate)):
    """Get vector store collection statistics (admin/debug endpoint)."""
    from app.core.vectorstore import get_vector_store

    try:
        store = get_vector_store()
        stats = store.get_collection_stats()

        # Filter to only show collections user has access to
        role_config = ROLES.get(user["role"], {})
        allowed = role_config.get("collections", [])

        if user["role"] != "c_level":
            stats = {k: v for k, v in stats.items() if k in allowed}

        return {"collections": stats, "accessible": allowed}
    except Exception as e:
        return {"error": str(e), "collections": {}}


# ============================================
# Startup Event
# ============================================


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    print("🚀 Starting Scout...")
    print(f"📊 Environment: {settings.environment}")
    print(f"🔑 Groq API Key: {'Set' if settings.groq_api_key else 'NOT SET'}")

    # Note: Vector store initialization is done lazily or via CLI script