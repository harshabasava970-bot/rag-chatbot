"""
Application configuration loaded from environment variables.
Uses pydantic-settings for validation and type coercion.
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

    # OpenAI
    openai_api_key: str = Field(..., description="OpenAI secret key")
    openai_model: str = Field(default="gpt-4o-mini")
    openai_embedding_model: str = Field(default="text-embedding-3-small")

    # Pinecone (optional – falls back to FAISS when absent)
    pinecone_api_key: Optional[str] = Field(default=None)
    pinecone_environment: Optional[str] = Field(default=None)
    pinecone_index_name: str = Field(default="rag-documents")

    # App
    app_env: str = Field(default="development")
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)
    port: int = Field(default=8000)  # Render sets $PORT automatically
    log_level: str = Field(default="INFO")

    # CORS
    allowed_origins: str = Field(default="http://localhost:5173,http://localhost:3000")

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

    @property
    def use_pinecone(self) -> bool:
        return bool(self.pinecone_api_key and self.pinecone_environment)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings singleton – import and call this everywhere."""
    return Settings()
