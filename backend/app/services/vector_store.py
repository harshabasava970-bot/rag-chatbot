"""
Vector store — uses FAISS (local file) + sentence-transformers embeddings.
100% free. No API keys. No internet needed for embeddings.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import List, Optional, Tuple

from langchain.schema import Document
from langchain_community.embeddings import HuggingFaceEmbeddings

from app.utils.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

_FAISS_DIR  = Path("./uploads/faiss_index")
_EMBEDDINGS: Optional[HuggingFaceEmbeddings] = None   # lazy singleton


def _get_embeddings() -> HuggingFaceEmbeddings:
    """
    Load the sentence-transformers model once and reuse it.
    'all-MiniLM-L6-v2' is small (22 MB), fast, and produces
    384-dim embeddings — perfect for local RAG.
    """
    global _EMBEDDINGS
    if _EMBEDDINGS is None:
        settings = get_settings()
        logger.info(f"Loading embedding model: {settings.embedding_model}")
        _EMBEDDINGS = HuggingFaceEmbeddings(
            model_name=settings.embedding_model,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        logger.info("Embedding model loaded ✓")
    return _EMBEDDINGS


def _load_store():
    """Load existing FAISS index from disk, or return None."""
    from langchain_community.vectorstores import FAISS

    if _FAISS_DIR.exists():
        try:
            store = FAISS.load_local(
                str(_FAISS_DIR),
                _get_embeddings(),
                allow_dangerous_deserialization=True,
            )
            logger.debug("FAISS index loaded from disk")
            return store
        except Exception as e:
            logger.warning(f"Could not load FAISS index: {e}")
    return None


def _save_store(store) -> None:
    _FAISS_DIR.mkdir(parents=True, exist_ok=True)
    store.save_local(str(_FAISS_DIR))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_vector_store_type() -> str:
    return "faiss"


def upsert_documents(documents: List[Document]) -> None:
    """Embed and store a list of LangChain Document chunks."""
    from langchain_community.vectorstores import FAISS

    existing = _load_store()
    if existing is None:
        store = FAISS.from_documents(documents, _get_embeddings())
    else:
        existing.add_documents(documents)
        store = existing

    _save_store(store)
    logger.info(f"Upserted {len(documents)} chunks to FAISS")


def similarity_search(
    query: str,
    top_k: int = 5,
    filter_doc_ids: Optional[List[str]] = None,
) -> List[Tuple[Document, float]]:
    """
    Run semantic similarity search.
    Returns list of (Document, score) sorted by relevance descending.
    """
    store = _load_store()
    if store is None:
        return []

    # Fetch extra results when filtering so we still get top_k after filter
    fetch_k = top_k * 4 if filter_doc_ids else top_k
    results = store.similarity_search_with_score(query, k=fetch_k)

    if filter_doc_ids:
        results = [
            (doc, score)
            for doc, score in results
            if doc.metadata.get("document_id") in filter_doc_ids
        ]

    # Convert L2 distance → similarity score in [0, 1]
    normalised = [
        (doc, float(1 / (1 + score)))
        for doc, score in results
    ]
    return sorted(normalised, key=lambda x: x[1], reverse=True)[:top_k]


def delete_document_vectors(document_id: str) -> None:
    """Rebuild FAISS index without the deleted document's chunks."""
    from langchain_community.vectorstores import FAISS

    store = _load_store()
    if store is None:
        return

    remaining = [
        doc for doc in store.docstore._dict.values()
        if doc.metadata.get("document_id") != document_id
    ]

    if not remaining:
        shutil.rmtree(str(_FAISS_DIR), ignore_errors=True)
        logger.info("FAISS index cleared (no documents left)")
        return

    new_store = FAISS.from_documents(remaining, _get_embeddings())
    _save_store(new_store)
    logger.info(f"Rebuilt FAISS index — removed document {document_id}")
