"""
Configuration settings for Scout.
Uses pydantic-settings for environment variable management.
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Environment
    environment: Literal["development", "staging", "production"] = "development"

    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Groq API
    groq_api_key: str = ""

    # LangSmith (Optional)
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""
    langchain_project: str = "scout-ai"

    # Model Configuration
    llm_model: str = "llama-3.3-70b-versatile"
    embedding_model: str = "all-MiniLM-L6-v2"
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # Vector Store
    chroma_persist_directory: str = "./chroma_db"
    chunk_size: int = 500
    chunk_overlap: int = 100

    # Rate Limiting
    max_requests_per_user_per_day: int = 100

    # AWS (for deployment)
    aws_region: str = "us-east-1"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Groq Rate Limits Reference (Free Tier)
# =====================================
# llama-3.3-70b-versatile: 30 RPM, 1K RPD, 12K TPM, 100K TPD
# llama-3.1-8b-instant:    30 RPM, 14.4K RPD, 6K TPM, 500K TPD
#
# Strategy: Use llama-3.3-70b for quality, fallback to 8b if rate limited

GROQ_RATE_LIMITS = {
    "llama-3.3-70b-versatile": {
        "rpm": 30,
        "rpd": 1000,
        "tpm": 12000,
        "tpd": 100000,
    },
    "llama-3.1-8b-instant": {
        "rpm": 30,
        "rpd": 14400,
        "tpm": 6000,
        "tpd": 500000,
    },
}

# RBAC Role Definitions
ROLES = {
    "engineering": {
        "name": "Engineering",
        "collections": ["engineering", "general"],
        "description": "Access to technical docs and general info",
    },
    "finance": {
        "name": "Finance",
        "collections": ["finance", "general"],
        "description": "Access to financial reports and general info",
    },
    "hr": {
        "name": "Human Resources",
        "collections": ["hr", "general"],
        "description": "Access to HR data and general info",
    },
    "marketing": {
        "name": "Marketing",
        "collections": ["marketing", "general"],
        "description": "Access to marketing reports and general info",
    },
    "c_level": {
        "name": "C-Level Executive",
        "collections": ["engineering", "finance", "hr", "marketing", "general"],
        "description": "Full access to all company data",
    },
    "employee": {
        "name": "Employee",
        "collections": ["general"],
        "description": "Access to general company info only",
    },
}
