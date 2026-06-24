"""
Application configuration loaded from environment variables.
Uses pydantic-settings for validation and type coercion.

LLM      : Groq  (free tier – no credit card needed)
Embeddings: sentence-transformers (100% local – completely free)
Vector DB : FAISS (local file – completely free)
"""

from __future__ import annotations

from functools import lru_cache
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ----------------------------------------------------------------
    # Groq  (free LLM – https://console.groq.com)
    # ----------------------------------------------------------------
    groq_api_key: str = Field(..., description="Groq API key (free)")
    groq_model: str = Field(default="llama-3.3-70b-versatile")

    # ----------------------------------------------------------------
    # Local embeddings – sentence-transformers (no API, fully free)
    # ----------------------------------------------------------------
    embedding_model: str = Field(default="all-MiniLM-L6-v2")

    # ----------------------------------------------------------------
    # App
    # ----------------------------------------------------------------
    app_env: str = Field(default="development")
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)
    port: int = Field(default=8000)   # Render injects $PORT

    log_level: str = Field(default="INFO")

    # CORS – comma-separated list of allowed origins
    allowed_origins: str = Field(
        default="http://localhost:5173,http://localhost:3000"
    )

    # Storage
    upload_dir: str = Field(default="./uploads")
    max_file_size_mb: int = Field(default=50)

    # RAG
    chunk_size: int = Field(default=1000)
    chunk_overlap: int = Field(default=200)
    top_k_results: int = Field(default=5)

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
