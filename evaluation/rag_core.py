"""
RAG primitives for the evaluation app.

These are intentionally separate from the main FastAPI backend so that the
evaluator can run standalone (no running server required).

The logic mirrors the notebook exactly:
  - RecursiveCharacterTextSplitter(800, 100)
  - HuggingFaceEmbeddings("all-MiniLM-L6-v2")
  - similarity retriever, k=6
"""

from __future__ import annotations

import os
from pathlib import Path

from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from litellm import completion

from evaluation.session import EvalSession, session_store

# ── Constants (mirror notebook) ──────────────────────────────────────────────

CHUNK_SIZE = 1667
CHUNK_OVERLAP = 100
EMBEDDINGS_MODEL = os.getenv("EMBEDDINGS_MODEL", "all-MiniLM-L6-v2")
RETRIEVER_K = 3

SYSTEM_PROMPT_TEMPLATE = """
You are a document-grounded AI assistant. Your sole source of truth is the
context provided below. Answer the user's question strictly based on that context.

## Rules
- Answer ONLY based on the provided context.
- If the context does not contain enough information to answer, say so explicitly.
- Never speculate or use outside knowledge to fill gaps.
- Be concise and direct. Lead with the answer, then support it with evidence.
- If multiple parts of the context contain conflicting information, surface the
  conflict explicitly rather than picking one silently.

## Context
{context}
"""

# ── Internal helpers ──────────────────────────────────────────────────────────


def _make_splitter() -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", " ", ""],
    )


def _get_llm_kwargs() -> dict:
    api_key = os.getenv("OPENROUTER_API_KEY")
    base_url = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
    os.environ.setdefault("OPENAI_API_KEY", api_key or "")
    os.environ.setdefault("OPENAI_BASE_URL", base_url)
    return {
        "model": os.getenv("LLM_MODEL", "openai/gpt-4o-mini"),
        "api_key": api_key,
        "base_url": base_url,
    }


# ── Public API ────────────────────────────────────────────────────────────────


def ingest_files(session_id: str, file_paths: list[str]) -> list:
    """
    Load, chunk, and embed a list of file paths (PDF or .txt).
    Incrementally adds to the session's vectorstore.

    Returns the full list of chunks ingested in this call.
    """
    _, session = session_store.get_or_create(session_id)
    splitter = _make_splitter()
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDINGS_MODEL)

    all_chunks = []

    for file_path in file_paths:
        path = Path(file_path)
        filename = path.name
        ext = path.suffix.lower()

        if ext == ".pdf":
            docs = PyPDFLoader(str(path)).load()
            chunks = splitter.split_documents(docs)
        else:  # .txt
            text = path.read_text(errors="ignore")
            chunks = splitter.create_documents([text])

        # Normalise source metadata to the original filename
        for chunk in chunks:
            chunk.metadata["source"] = filename

        all_chunks.extend(chunks)

        if filename not in session.doc_names:
            session.doc_names.append(filename)

    # Build or extend vectorstore
    if session.vectorstore is None:
        session.vectorstore = Chroma.from_documents(all_chunks, embeddings)
    else:
        session.vectorstore.add_documents(all_chunks)

    session.retriever = session.vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": RETRIEVER_K},
    )

    return all_chunks


def fetch_context(question: str, session: EvalSession) -> list:
    """Retrieve relevant chunks for a question. Returns list[Document]."""
    if session.retriever is None:
        return []
    return session.retriever.invoke(question)


def answer_question(question: str, session: EvalSession) -> tuple[str, list]:
    """
    Run the full RAG pipeline for a question.

    Returns
    -------
    answer : str
    docs   : list[Document]
    """
    docs = fetch_context(question, session)
    if not docs:
        return "No relevant context found in the uploaded documents.", []

    context = "\n\n".join(doc.page_content for doc in docs)
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(context=context)

    response = completion(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
        **_get_llm_kwargs(),
    )
    return response.choices[0].message.content, docs
