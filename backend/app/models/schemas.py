"""
Pydantic schemas for request/response validation.
All API models are defined here for clean separation of concerns.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Document models
# ---------------------------------------------------------------------------

class DocumentMetadata(BaseModel):
    """Metadata stored alongside each document."""
    id: str
    filename: str
    file_size: int  # bytes
    page_count: int
    chunk_count: int
    uploaded_at: datetime
    status: str = "ready"  # ready | processing | error


class DocumentListResponse(BaseModel):
    """Response payload for GET /documents."""
    documents: List[DocumentMetadata]
    total: int


class UploadResponse(BaseModel):
    """Response payload for POST /upload."""
    document_id: str
    filename: str
    page_count: int
    chunk_count: int
    message: str = "Document processed successfully"


class DeleteResponse(BaseModel):
    """Response payload for DELETE /documents/{id}."""
    document_id: str
    message: str = "Document deleted successfully"


# ---------------------------------------------------------------------------
# Chat models
# ---------------------------------------------------------------------------

class ChatMessage(BaseModel):
    """A single message in the conversation history."""
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str


class SourceChunk(BaseModel):
    """A retrieved context chunk returned alongside the answer."""
    document_id: str
    filename: str
    page: Optional[int] = None
    content: str
    score: float = Field(..., ge=0.0, le=1.0)


class ChatRequest(BaseModel):
    """Request payload for POST /chat."""
    query: str = Field(..., min_length=1, max_length=4096)
    conversation_history: List[ChatMessage] = Field(default_factory=list)
    document_ids: Optional[List[str]] = None  # None = search all documents
    top_k: int = Field(default=5, ge=1, le=20)


class ChatResponse(BaseModel):
    """Response payload for POST /chat."""
    answer: str
    sources: List[SourceChunk]
    conversation_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    """Response payload for GET /health."""
    status: str
    version: str
    vector_store: str  # "pinecone" | "faiss"
    openai_connected: bool
    document_count: int
