"""
Vector store abstraction layer.
Attempts to use Pinecone when credentials are present,
otherwise falls back to a persistent FAISS index on disk.
"""

from __future__ import annotations

import os
import pickle
from pathlib import Path
from typing import List, Optional, Tuple

from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings

from app.utils.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Path for the local FAISS persistence
_FAISS_DIR = Path("./uploads/faiss_index")
_FAISS_DOCS = Path("./uploads/faiss_docs.pkl")


def _get_embeddings() -> OpenAIEmbeddings:
    settings = get_settings()
    return OpenAIEmbeddings(
        openai_api_key=settings.openai_api_key,
        model=settings.openai_embedding_model,
    )


# ---------------------------------------------------------------------------
# Pinecone backend
# ---------------------------------------------------------------------------

def _pinecone_upsert(documents: List[Document]) -> None:
    from pinecone import Pinecone, ServerlessSpec
    from langchain_pinecone import PineconeVectorStore

    settings = get_settings()
    pc = Pinecone(api_key=settings.pinecone_api_key)

    # Create index if it doesn't exist
    existing = [idx.name for idx in pc.list_indexes()]
    if settings.pinecone_index_name not in existing:
        pc.create_index(
            name=settings.pinecone_index_name,
            dimension=1536,  # text-embedding-3-small dimension
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region=settings.pinecone_environment),
        )
        logger.info(f"Created Pinecone index: {settings.pinecone_index_name}")

    PineconeVectorStore.from_documents(
        documents=documents,
        embedding=_get_embeddings(),
        index_name=settings.pinecone_index_name,
    )
    logger.info(f"Upserted {len(documents)} chunks to Pinecone")


def _pinecone_search(query: str, top_k: int, filter_doc_ids: Optional[List[str]] = None):
    from pinecone import Pinecone
    from langchain_pinecone import PineconeVectorStore

    settings = get_settings()
    pc = Pinecone(api_key=settings.pinecone_api_key)
    store = PineconeVectorStore(
        index=pc.Index(settings.pinecone_index_name),
        embedding=_get_embeddings(),
    )

    search_kwargs: dict = {"k": top_k}
    if filter_doc_ids:
        search_kwargs["filter"] = {"document_id": {"$in": filter_doc_ids}}

    return store.similarity_search_with_score(query, **search_kwargs)


def _pinecone_delete(document_id: str) -> None:
    from pinecone import Pinecone

    settings = get_settings()
    pc = Pinecone(api_key=settings.pinecone_api_key)
    index = pc.Index(settings.pinecone_index_name)

    # Fetch all vector IDs that belong to this document
    # Pinecone requires fetching with filter on metadata
    try:
        index.delete(filter={"document_id": {"$eq": document_id}})
        logger.info(f"Deleted Pinecone vectors for document {document_id}")
    except Exception as e:
        logger.warning(f"Pinecone delete failed (may be normal): {e}")


# ---------------------------------------------------------------------------
# FAISS backend
# ---------------------------------------------------------------------------

def _load_faiss_store():
    """Load existing FAISS store from disk, or return None."""
    from langchain_community.vectorstores import FAISS

    if _FAISS_DIR.exists() and _FAISS_DOCS.exists():
        try:
            store = FAISS.load_local(
                str(_FAISS_DIR),
                _get_embeddings(),
                allow_dangerous_deserialization=True,
            )
            logger.debug("Loaded existing FAISS index from disk")
            return store
        except Exception as e:
            logger.warning(f"Could not load FAISS index: {e}")
    return None


def _save_faiss_store(store) -> None:
    _FAISS_DIR.mkdir(parents=True, exist_ok=True)
    store.save_local(str(_FAISS_DIR))


def _faiss_upsert(documents: List[Document]) -> None:
    from langchain_community.vectorstores import FAISS

    existing = _load_faiss_store()
    if existing is None:
        store = FAISS.from_documents(documents, _get_embeddings())
    else:
        store.add_documents(documents)
        store = existing
        store.add_documents(documents)  # add to existing

    _save_faiss_store(store)
    logger.info(f"Upserted {len(documents)} chunks to FAISS")


def _faiss_search(query: str, top_k: int, filter_doc_ids: Optional[List[str]] = None):
    store = _load_faiss_store()
    if store is None:
        return []

    results = store.similarity_search_with_score(query, k=top_k * 3)

    if filter_doc_ids:
        results = [
            (doc, score)
            for doc, score in results
            if doc.metadata.get("document_id") in filter_doc_ids
        ]

    return results[:top_k]


def _faiss_delete(document_id: str) -> None:
    """Rebuild the FAISS index excluding the deleted document."""
    from langchain_community.vectorstores import FAISS

    store = _load_faiss_store()
    if store is None:
        return

    # Get all docstore entries
    all_docs_dict = store.docstore._dict  # internal dict {id: Document}
    remaining = [
        doc for doc in all_docs_dict.values()
        if doc.metadata.get("document_id") != document_id
    ]

    if not remaining:
        import shutil
        shutil.rmtree(str(_FAISS_DIR), ignore_errors=True)
        _FAISS_DOCS.unlink(missing_ok=True)
        logger.info(f"FAISS index cleared (was last document)")
        return

    new_store = FAISS.from_documents(remaining, _get_embeddings())
    _save_faiss_store(new_store)
    logger.info(f"Rebuilt FAISS index without document {document_id}")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_vector_store_type() -> str:
    settings = get_settings()
    return "pinecone" if settings.use_pinecone else "faiss"


def upsert_documents(documents: List[Document]) -> None:
    """Embed and store a list of LangChain Document chunks."""
    settings = get_settings()
    if settings.use_pinecone:
        _pinecone_upsert(documents)
    else:
        _faiss_upsert(documents)


def similarity_search(
    query: str,
    top_k: int = 5,
    filter_doc_ids: Optional[List[str]] = None,
) -> List[Tuple[Document, float]]:
    """
    Run a semantic similarity search.

    Returns:
        List of (Document, similarity_score) tuples sorted by relevance.
    """
    settings = get_settings()
    if settings.use_pinecone:
        results = _pinecone_search(query, top_k, filter_doc_ids)
    else:
        results = _faiss_search(query, top_k, filter_doc_ids)

    # Normalise scores to [0, 1]  (FAISS returns L2 distance, Pinecone cosine)
    normalised = []
    for doc, score in results:
        if settings.use_pinecone:
            # Pinecone cosine similarity already in [0, 1]
            norm_score = float(score)
        else:
            # FAISS L2 distance → convert to similarity
            norm_score = float(1 / (1 + score))
        normalised.append((doc, norm_score))

    return sorted(normalised, key=lambda x: x[1], reverse=True)


def delete_document_vectors(document_id: str) -> None:
    """Remove all vector embeddings associated with a document."""
    settings = get_settings()
    if settings.use_pinecone:
        _pinecone_delete(document_id)
    else:
        _faiss_delete(document_id)
