"""
Persistent document metadata store backed by a JSON file.
In production you'd swap this for a real database (Postgres, SQLite, etc.)
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from app.models.schemas import DocumentMetadata
from app.utils.logger import get_logger

logger = get_logger(__name__)

_STORE_FILE = Path("./uploads/metadata.json")


def _load_store() -> Dict[str, dict]:
    if _STORE_FILE.exists():
        try:
            return json.loads(_STORE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_store(data: Dict[str, dict]) -> None:
    _STORE_FILE.parent.mkdir(parents=True, exist_ok=True)
    _STORE_FILE.write_text(json.dumps(data, default=str, indent=2), encoding="utf-8")


def create_document(
    filename: str,
    file_size: int,
    page_count: int,
    chunk_count: int,
) -> DocumentMetadata:
    """Create and persist a new document record."""
    doc_id = str(uuid.uuid4())
    doc = DocumentMetadata(
        id=doc_id,
        filename=filename,
        file_size=file_size,
        page_count=page_count,
        chunk_count=chunk_count,
        uploaded_at=datetime.now(tz=timezone.utc),
        status="ready",
    )
    store = _load_store()
    store[doc_id] = doc.model_dump()
    _save_store(store)
    logger.info(f"Document created: {doc_id} ({filename})")
    return doc


def get_document(doc_id: str) -> Optional[DocumentMetadata]:
    store = _load_store()
    raw = store.get(doc_id)
    if raw is None:
        return None
    return DocumentMetadata(**raw)


def list_documents() -> List[DocumentMetadata]:
    store = _load_store()
    return [DocumentMetadata(**v) for v in store.values()]


def delete_document(doc_id: str) -> bool:
    store = _load_store()
    if doc_id not in store:
        return False
    del store[doc_id]
    _save_store(store)
    logger.info(f"Document deleted: {doc_id}")
    return True
