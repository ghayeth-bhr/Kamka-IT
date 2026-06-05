"""
TestQuestion model and session-scoped loader.

The load_tests() function no longer reads a static JSONL file.
Tests are generated per session by test_generator.py and stored in
the SessionStore. Callers must pass a session_id.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class TestQuestion(BaseModel):
    """A test question with expected keywords and reference answer."""

    question: str = Field(description="The question to ask the RAG system")
    keywords: list[str] = Field(
        description="Keywords that must appear verbatim in retrieved context"
    )
    reference_answer: str = Field(description="Ground-truth answer for this question")
    category: str = Field(
        description="Question category: direct_fact | inferential | spanning | numerical"
    )


def load_tests(session_id: str) -> list[TestQuestion]:
    """
    Return the test questions for a given session.

    Replaces the original file-based loader. Session must have been
    populated by test_generator.generate_tests() before calling this.
    """
    from evaluation.session import session_store  # late import to avoid circularity

    try:
        session = session_store.get(session_id)
        return list(session.tests)
    except KeyError:
        return []
