"""
FastAPI route handlers for all API endpoints.

Endpoints:
  POST   /upload               - Upload and process a PDF
  POST   /chat                 - RAG chat query
  GET    /documents            - List uploaded documents
  DELETE /documents/{doc_id}   - Delete a document
  GET    /health               - Health check
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import List

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    DeleteResponse,
    DocumentListResponse,
    HealthResponse,
    UploadResponse,
)
from app.rag.pipeline import run_rag_pipeline
from app.services.document_store import (
    create_document,
    delete_document,
    get_document,
    list_documents,
)
from app.services.pdf_processor import chunk_document, extract_text_from_pdf
from app.services.vector_store import (
    delete_document_vectors,
    get_vector_store_type,
    upsert_documents,
)
from app.utils.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@router.get("/health", response_model=HealthResponse, tags=["system"])
async def health_check() -> HealthResponse:
    """Return current system health status."""
    from openai import OpenAI

    settings = get_settings()
    openai_ok = False
    try:
        client = OpenAI(api_key=settings.openai_api_key)
        client.models.list()
        openai_ok = True
    except Exception as e:
        logger.warning(f"OpenAI connectivity check failed: {e}")

    docs = list_documents()
    return HealthResponse(
        status="healthy" if openai_ok else "degraded",
        version="1.0.0",
        vector_store=get_vector_store_type(),
        openai_connected=openai_ok,
        document_count=len(docs),
    )


# ---------------------------------------------------------------------------
# Document management
# ---------------------------------------------------------------------------

@router.get("/documents", response_model=DocumentListResponse, tags=["documents"])
async def get_documents() -> DocumentListResponse:
    """List all uploaded and processed documents."""
    docs = list_documents()
    return DocumentListResponse(documents=docs, total=len(docs))


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["documents"],
)
async def upload_document(file: UploadFile = File(...)) -> UploadResponse:
    """
    Upload a PDF file, extract text, chunk it, generate embeddings,
    and store the vectors in the configured vector store.
    """
    settings = get_settings()

    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported.",
        )

    # Read file content
    content = await file.read()
    file_size = len(content)
    max_bytes = settings.max_file_size_mb * 1024 * 1024

    if file_size > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the {settings.max_file_size_mb} MB limit.",
        )

    # Save to uploads directory temporarily
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # We need a doc_id to use as the namespace before writing metadata
    import uuid
    temp_doc_id = str(uuid.uuid4())
    temp_path = upload_dir / f"{temp_doc_id}_{file.filename}"

    try:
        temp_path.write_bytes(content)
        logger.info(f"Saved upload to {temp_path}")

        # Extract text from PDF
        full_text, page_count = extract_text_from_pdf(str(temp_path))

        if not full_text.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Could not extract text from the PDF. The file may be scanned/image-based.",
            )

        # Chunk the document (uses temp_doc_id as the document namespace)
        chunks = chunk_document(full_text, document_id=temp_doc_id, filename=file.filename)

        # Store vectors
        upsert_documents(chunks)

        # Persist document metadata
        doc = create_document(
            filename=file.filename,
            file_size=file_size,
            page_count=page_count,
            chunk_count=len(chunks),
        )

        # Rename temp file to final name
        final_path = upload_dir / f"{doc.id}_{file.filename}"
        shutil.move(str(temp_path), str(final_path))

        return UploadResponse(
            document_id=doc.id,
            filename=doc.filename,
            page_count=doc.page_count,
            chunk_count=doc.chunk_count,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to process uploaded document: {e}")
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}",
        )


@router.delete(
    "/documents/{doc_id}",
    response_model=DeleteResponse,
    tags=["documents"],
)
async def delete_document_endpoint(doc_id: str) -> DeleteResponse:
    """Delete a document and all its associated vector embeddings."""
    doc = get_document(doc_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {doc_id} not found.",
        )

    try:
        # Remove vectors from the vector store
        delete_document_vectors(doc_id)

        # Remove metadata record
        delete_document(doc_id)

        # Remove the uploaded file
        settings = get_settings()
        upload_dir = Path(settings.upload_dir)
        for pdf_file in upload_dir.glob(f"{doc_id}_*"):
            pdf_file.unlink(missing_ok=True)

        return DeleteResponse(document_id=doc_id)

    except Exception as e:
        logger.exception(f"Failed to delete document {doc_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}",
        )


# ---------------------------------------------------------------------------
# Chat / RAG
# ---------------------------------------------------------------------------

@router.post("/chat", response_model=ChatResponse, tags=["chat"])
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Accept a user query, retrieve relevant document chunks,
    and return a grounded answer with source citations.
    """
    settings = get_settings()

    try:
        answer, sources = run_rag_pipeline(
            query=request.query,
            conversation_history=request.conversation_history,
            document_ids=request.document_ids,
            top_k=request.top_k or settings.top_k_results,
        )
        return ChatResponse(answer=answer, sources=sources)

    except Exception as e:
        logger.exception(f"RAG pipeline error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate response: {str(e)}",
        )
