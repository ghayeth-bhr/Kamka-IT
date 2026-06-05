"""
LLM-based test question generator.

Given a list of LangChain Document chunks (already ingested into the
vectorstore), this module calls an LLM to produce a list of TestQuestion
objects that can be used directly by the eval pipeline.

Generation strategy
───────────────────
- Chunks are grouped by source document.
- For each document, a representative sample of chunks (up to MAX_CHUNKS_PER_DOC)
  is assembled and sent to the LLM in one call.
- The LLM returns a JSON array of TestQuestion objects.
- Questions are distributed across four categories to ensure coverage:
    direct_fact   – single-chunk lookup, exact values
    inferential   – requires reasoning across one chunk
    spanning      – answer requires combining ≥2 chunks
    numerical     – involves a number mentioned in the document
- The LLM is instructed to return ONLY valid JSON (no markdown fences).
  We strip any accidental fences before parsing.
"""

from __future__ import annotations

import json
import os
from collections import defaultdict

from langchain_core.documents import Document
from litellm import completion

from evaluation.test import TestQuestion

# ── Tuning knobs ──────────────────────────────────────────────────────────────

MAX_CHUNKS_PER_DOC = (
    40  # sample up to 40 evenly-spaced chunks (~32k tokens for gpt-4o-mini)
)
QUESTIONS_PER_DOC = 24  # target questions per document
CATEGORY_DISTRIBUTION = [  # cycle for consistent coverage across all questions
    "direct_fact",
    "direct_fact",
    "inferential",
    "direct_fact",
    "spanning",
    "numerical",
    "direct_fact",
    "inferential",
    "direct_fact",
    "spanning",
    "direct_fact",
    "numerical",
    "inferential",
    "direct_fact",
    "spanning",
    "numerical",
    "direct_fact",
    "inferential",
    "direct_fact",
    "spanning",
    "numerical",
    "direct_fact",
    "inferential",
    "spanning",
]
MODEL = os.getenv("LLM_MODEL", "openai/gpt-4o-mini")

# ── Prompt ────────────────────────────────────────────────────────────────────

_SYSTEM = (
    "You are a question-answer dataset creator for evaluating RAG systems. "
    "Your output must be ONLY a valid JSON array — no markdown fences, no preamble."
)

_USER_TEMPLATE = """\
Below are text chunks extracted from the document "{doc_name}".
Generate exactly {n} test questions based on the content.

Category definitions:
- direct_fact   : a single fact stated explicitly in one chunk (e.g. a name, date, price)
- inferential   : requires interpreting or paraphrasing information from one chunk
- spanning      : answer requires combining information from at least two chunks
- numerical     : involves a specific number, amount, percentage, or date in the document

Required category sequence for the {n} questions (in this order):
{categories}

Rules:
1. Every question must be answerable from the provided chunks — do NOT invent facts.
2. keywords: 2–4 short strings that MUST appear verbatim (case-insensitive) in the
   chunk(s) that answer the question. Choose specific terms, not common stop words.
3. reference_answer: a complete, standalone answer based only on the document content.
4. Each question must be distinct and cover a different piece of information.

Return a JSON array with exactly {n} objects. Each object:
{{
  "question": "...",
  "keywords": ["kw1", "kw2"],
  "reference_answer": "...",
  "category": "direct_fact|inferential|spanning|numerical"
}}

Document chunks:
{chunks}
"""

# ── Core function ─────────────────────────────────────────────────────────────


def _sample_chunks(chunks: list[Document], max_chunks: int) -> list[Document]:
    """
    Sample chunks evenly across a document.
    Evenly spaced sampling preserves coverage across long documents.
    """
    if len(chunks) <= max_chunks:
        return chunks
    step = len(chunks) / max_chunks
    return [chunks[int(i * step)] for i in range(max_chunks)]


def _chunks_to_text(chunks: list[Document]) -> str:
    parts = []
    for i, chunk in enumerate(chunks, start=1):
        page = chunk.metadata.get("page", "")
        page_info = f" (page {page})" if page != "" else ""
        parts.append(f"[Chunk {i}{page_info}]\n{chunk.page_content.strip()}")
    return "\n\n---\n\n".join(parts)


def _call_llm(doc_name: str, chunks: list[Document], n: int) -> list[TestQuestion]:
    """Call the LLM and parse the JSON response into TestQuestion objects."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    base_url = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
    if api_key:
        os.environ.setdefault("OPENAI_API_KEY", api_key)
        os.environ.setdefault("OPENAI_BASE_URL", base_url)

    categories = CATEGORY_DISTRIBUTION[:n]
    # If n > len distribution, cycle it
    while len(categories) < n:
        categories.extend(CATEGORY_DISTRIBUTION)
    categories = categories[:n]

    user_msg = _USER_TEMPLATE.format(
        doc_name=doc_name,
        n=n,
        categories=", ".join(categories),
        chunks=_chunks_to_text(chunks),
    )

    response = completion(
        model=MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.3,  # low temp → more factual, less creative
    )

    raw = response.choices[0].message.content.strip()

    # Strip any accidental markdown fences
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    data = json.loads(raw)
    questions = []
    for item in data:
        try:
            questions.append(TestQuestion(**item))
        except Exception:
            continue  # skip malformed entries silently
    return questions


def generate_tests(chunks: list[Document]) -> list[TestQuestion]:
    """
    Generate test questions for a batch of Document chunks.

    Chunks are grouped by their `source` metadata field (i.e. by document).
    For each document a separate LLM call is made.

    Parameters
    ----------
    chunks : list[Document]
        The chunks returned by `ingest_files()`.

    Returns
    -------
    list[TestQuestion]
        All generated questions, ready to be stored in the session.
    """
    # Group chunks by source document
    by_source: dict[str, list[Document]] = defaultdict(list)
    for chunk in chunks:
        source = chunk.metadata.get("source", "unknown")
        by_source[source].append(chunk)

    all_tests: list[TestQuestion] = []

    for doc_name, doc_chunks in by_source.items():
        sampled = _sample_chunks(doc_chunks, MAX_CHUNKS_PER_DOC)
        try:
            tests = _call_llm(doc_name, sampled, QUESTIONS_PER_DOC)
            all_tests.extend(tests)
        except Exception as exc:
            # Do not crash the whole pipeline if one document fails
            print(f"[test_generator] WARNING: failed for '{doc_name}': {exc}")

    return all_tests
