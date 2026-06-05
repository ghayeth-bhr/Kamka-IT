"""
LangChain tools for the RAG agent.
"""

from __future__ import annotations

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from app.config import settings
from app.core.rag.prompts import SUMMARIZE_PROMPT_TEMPLATE
from app.core.store.vector_store import vector_store_manager


def _get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.openrouter_api_key,
        base_url=settings.llm_base_url,
    )


@tool
def retrieve_context(query: str) -> str:
    """
    Search uploaded documents for chunks relevant to the query.
    Returns a formatted string with chunk headers and content.
    """
    retriever = vector_store_manager.retriever
    if retriever is None:
        return "No documents have been uploaded yet."

    docs = retriever.invoke(query)
    if not docs:
        return "No relevant context found in the uploaded documents."

    parts = []
    for i, doc in enumerate(docs, start=1):
        source = doc.metadata.get("source", "unknown")
        page = doc.metadata.get("page", "")
        page_info = f", page {page}" if page != "" else ""
        parts.append(f"[Chunk {i} - {source}{page_info}]\n{doc.page_content.strip()}")

    return "\n\n---\n\n".join(parts)


@tool
def summarize_document(filename: str) -> str:
    """
    Summarize the full document identified by filename.
    The filename must match an uploaded document.
    """
    chunks = vector_store_manager.get_all_chunks_for_source(filename)
    if not chunks:
        available = [d.filename for d in vector_store_manager.documents]
        return (
            f"Document '{filename}' not found. "
            f"Available documents: {available or 'none uploaded yet'}."
        )

    combined = "\n\n".join(chunks)[:6000]
    prompt = SUMMARIZE_PROMPT_TEMPLATE.format(content=combined)

    llm = _get_llm()
    response = llm.invoke(prompt)
    return response.content


@tool
def calculate(expression: str) -> str:
    """
    Safely evaluate a basic arithmetic expression.
    Supports +, -, *, /, ** and parentheses.
    """
    allowed = set("0123456789+-*/.() \t\n")
    if not all(c in allowed for c in expression):
        return "Invalid expression - only arithmetic operators are allowed."
    try:
        result = eval(expression, {"__builtins__": {}})
        return str(result)
    except Exception as exc:
        return f"Calculation error: {exc}"


ALL_TOOLS = [retrieve_context, summarize_document, calculate]
