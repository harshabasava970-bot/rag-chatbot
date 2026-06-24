"""
RAG (Retrieval-Augmented Generation) pipeline.

Flow:
  1. Embed the user query
  2. Retrieve top-K similar chunks from the vector store
  3. Build a context-aware prompt with conversation history
  4. Generate an answer using OpenAI Chat Completions
  5. Return the answer + source citations
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from langchain.schema import Document
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
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
- If the answer is not in the context, say "I couldn't find relevant information
  in the uploaded documents." Do NOT make up information.
- Cite the source document and page number when available (e.g. [Source: filename.pdf, Page 3]).
- Be concise but complete. Use bullet points for lists.
- Maintain a helpful, professional tone.

Context:
{context}
"""


def _build_context(chunks: List[Tuple[Document, float]]) -> str:
    """Format retrieved chunks into a single context string."""
    parts = []
    for i, (doc, score) in enumerate(chunks, start=1):
        meta = doc.metadata
        filename = meta.get("filename", "unknown")
        page = meta.get("page")
        page_info = f", Page {page}" if page else ""
        parts.append(
            f"[{i}] Source: {filename}{page_info} (relevance: {score:.2f})\n"
            f"{doc.page_content}"
        )
    return "\n\n---\n\n".join(parts)


def _convert_history(history: List[ChatMessage]):
    """Convert our schema messages to LangChain message objects."""
    messages = []
    for msg in history:
        if msg.role == "user":
            messages.append(HumanMessage(content=msg.content))
        else:
            messages.append(AIMessage(content=msg.content))
    return messages


def run_rag_pipeline(
    query: str,
    conversation_history: List[ChatMessage],
    document_ids: Optional[List[str]] = None,
    top_k: int = 5,
) -> Tuple[str, List[SourceChunk]]:
    """
    Execute the full RAG pipeline for a user query.

    Args:
        query:                 The user's question.
        conversation_history:  Prior turns for context.
        document_ids:          If set, restrict retrieval to these documents.
        top_k:                 Number of chunks to retrieve.

    Returns:
        (answer_text, list_of_source_chunks)
    """
    settings = get_settings()

    # ------------------------------------------------------------------
    # 1. Retrieve relevant chunks
    # ------------------------------------------------------------------
    logger.info(f"Retrieving top-{top_k} chunks for query: {query[:80]}...")
    raw_results = similarity_search(query, top_k=top_k, filter_doc_ids=document_ids)

    if not raw_results:
        return (
            "I couldn't find any relevant information in the uploaded documents. "
            "Please make sure you have uploaded documents and try again.",
            [],
        )

    # ------------------------------------------------------------------
    # 2. Build context string
    # ------------------------------------------------------------------
    context = _build_context(raw_results)

    # ------------------------------------------------------------------
    # 3. Build prompt messages
    # ------------------------------------------------------------------
    system_msg = SystemMessage(content=_SYSTEM_PROMPT.format(context=context))
    history_msgs = _convert_history(conversation_history[-10:])  # last 10 turns
    human_msg = HumanMessage(content=query)

    messages = [system_msg] + history_msgs + [human_msg]

    # ------------------------------------------------------------------
    # 4. Call OpenAI
    # ------------------------------------------------------------------
    llm = ChatOpenAI(
        openai_api_key=settings.openai_api_key,
        model=settings.openai_model,
        temperature=0.2,
        max_tokens=1024,
    )

    logger.info(f"Calling OpenAI model: {settings.openai_model}")
    response = llm.invoke(messages)
    answer = response.content

    # ------------------------------------------------------------------
    # 5. Format source citations
    # ------------------------------------------------------------------
    sources: List[SourceChunk] = []
    seen: set = set()
    for doc, score in raw_results:
        meta = doc.metadata
        doc_id = meta.get("document_id", "")
        key = f"{doc_id}_{meta.get('chunk_index', 0)}"
        if key in seen:
            continue
        seen.add(key)
        sources.append(
            SourceChunk(
                document_id=doc_id,
                filename=meta.get("filename", "unknown"),
                page=meta.get("page"),
                content=doc.page_content[:300],  # truncate for UI
                score=round(score, 4),
            )
        )

    logger.info(f"Generated answer with {len(sources)} source citations")
    return answer, sources
