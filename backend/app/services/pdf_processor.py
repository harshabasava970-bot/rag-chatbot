"""
PDF text extraction and intelligent chunking service.
Uses PyMuPDF (fitz) for extraction and LangChain text splitters for chunking.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Tuple

import fitz  # PyMuPDF
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from app.utils.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


def extract_text_from_pdf(file_path: str) -> Tuple[str, int]:
    """
    Extract full text from a PDF file.

    Returns:
        (full_text, page_count)
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {file_path}")

    doc = fitz.open(str(path))
    pages_text: List[str] = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")
        if text.strip():
            pages_text.append(f"[Page {page_num + 1}]\n{text}")

    doc.close()
    full_text = "\n\n".join(pages_text)
    page_count = len(pages_text)
    logger.info(f"Extracted {page_count} pages from {path.name}")
    return full_text, page_count


def chunk_document(
    text: str,
    document_id: str,
    filename: str,
) -> List[Document]:
    """
    Split document text into overlapping chunks suitable for embedding.

    Each chunk is a LangChain Document with metadata:
      - document_id
      - filename
      - chunk_index
      - page (extracted from [Page N] markers when present)

    Returns:
        List of LangChain Document objects.
    """
    settings = get_settings()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )

    raw_chunks = splitter.split_text(text)
    documents: List[Document] = []

    for idx, chunk_text in enumerate(raw_chunks):
        # Try to detect page number from the [Page N] marker
        page: int | None = None
        if "[Page " in chunk_text:
            try:
                start = chunk_text.index("[Page ") + 6
                end = chunk_text.index("]", start)
                page = int(chunk_text[start:end])
            except (ValueError, IndexError):
                pass

        documents.append(
            Document(
                page_content=chunk_text,
                metadata={
                    "document_id": document_id,
                    "filename": filename,
                    "chunk_index": idx,
                    "page": page,
                },
            )
        )

    logger.info(f"Created {len(documents)} chunks for document {document_id}")
    return documents
