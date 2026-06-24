"""
RAG pipeline — Groq LLM (free) + local FAISS + sentence-transformers.

Flow:
  1. Embed query locally (sentence-transformers, free)
  2. Retrieve top-K chunks from FAISS (local, free)
  3. Build context-aware prompt with conversation history
  4. Generate answer via Groq API (free tier)
  5. Return answer + source citations
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from langchain.schema import Document
from langchain_groq import ChatGroq
from langchain.schema.messages import HumanMessage, AIMessage, SystemMessage

from app.models.schemas import ChatMessage, SourceChunk
from app.services.vector_store import similarity_search
from app.utils.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

_SYSTEM_PROMPT = """\
You are an intelligent document assistant. Your job is to answer questions
based ONLY on the provided context documents.

Rules:
- Base your answer exclusively on the context below.
- If the answer is not in the context, say "I couldn't find relevant \
information in the uploaded documents." Do NOT make up information.
- Cite the source document and page number when available \
(e.g. [Source: filename.pdf, Page 3]).
- Be concise but complete. Use bullet points for lists.
- Maintain a helpful, professional tone.

Context:
{context}
"""


def _build_context(chunks: List[Tuple[Document, float]]) -> str:
    parts = []
    for i, (doc, score) in enumerate(chunks, start=1):
        meta     = doc.metadata
        filename = meta.get("filename", "unknown")
        page     = meta.get("page")
        page_str = f", Page {page}" if page else ""
        parts.append(
            f"[{i}] Source: {filename}{page_str} (relevance: {score:.2f})\n"
            f"{doc.page_content}"
        )
    return "\n\n---\n\n".join(parts)


def _convert_history(history: List[ChatMessage]):
    msgs = []
    for m in history:
        if m.role == "user":
            msgs.append(HumanMessage(content=m.content))
        else:
            msgs.append(AIMessage(content=m.content))
    return msgs


def run_rag_pipeline(
    query: str,
    conversation_history: List[ChatMessage],
    document_ids: Optional[List[str]] = None,
    top_k: int = 5,
) -> Tuple[str, List[SourceChunk]]:
    """
    Execute the full RAG pipeline.

    Returns:
        (answer_text, source_chunks)
    """
    settings = get_settings()

    # ── 1. Retrieve ──────────────────────────────────────────────────
    logger.info(f"Retrieving top-{top_k} chunks for: {query[:80]}...")
    results = similarity_search(query, top_k=top_k, filter_doc_ids=document_ids)

    if not results:
        return (
            "I couldn't find any relevant information in the uploaded documents. "
            "Please upload a PDF first, then ask your question.",
            [],
        )

    # ── 2. Build context ─────────────────────────────────────────────
    context = _build_context(results)

    # ── 3. Build messages ────────────────────────────────────────────
    system_msg   = SystemMessage(content=_SYSTEM_PROMPT.format(context=context))
    history_msgs = _convert_history(conversation_history[-10:])
    human_msg    = HumanMessage(content=query)
    messages     = [system_msg] + history_msgs + [human_msg]

    # ── 4. Call Groq (free) ──────────────────────────────────────────
    llm = ChatGroq(
        groq_api_key=settings.groq_api_key,
        model_name=settings.groq_model,
        temperature=0.2,
        max_tokens=1024,
    )

    logger.info(f"Calling Groq model: {settings.groq_model}")
    response = llm.invoke(messages)
    answer   = response.content

    # ── 5. Format citations ──────────────────────────────────────────
    sources: List[SourceChunk] = []
    seen: set = set()
    for doc, score in results:
        meta  = doc.metadata
        doc_id = meta.get("document_id", "")
        key   = f"{doc_id}_{meta.get('chunk_index', 0)}"
        if key in seen:
            continue
        seen.add(key)
        sources.append(
            SourceChunk(
                document_id=doc_id,
                filename=meta.get("filename", "unknown"),
                page=meta.get("page"),
                content=doc.page_content[:300],
                score=round(score, 4),
            )
        )

    logger.info(f"Answer generated with {len(sources)} source citations")
    return answer, sources
