"""
Per-user session state for the evaluation app.

Each Gradio user gets a unique session_id (stored in gr.State).
The SessionStore maps session_id → EvalSession, which holds that user's
vectorstore, retriever, and generated test questions.

Thread safety: individual session objects are not shared between users,
so no locking is needed at the session level. The dict-level lock only
protects session creation.
"""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from typing import Optional

from langchain_chroma import Chroma
from langchain_core.retrievers import BaseRetriever

from evaluation.test import TestQuestion


@dataclass
class EvalSession:
    """All state for one evaluation user session."""

    vectorstore: Optional[Chroma] = None
    retriever: Optional[BaseRetriever] = None
    tests: list[TestQuestion] = field(default_factory=list)
    doc_names: list[str] = field(default_factory=list)

    @property
    def is_ready(self) -> bool:
        return self.vectorstore is not None and len(self.tests) > 0


class SessionStore:
    """Thread-safe singleton registry of EvalSession objects."""

    _instance: Optional["SessionStore"] = None
    _meta_lock = threading.Lock()

    def __new__(cls) -> "SessionStore":
        if cls._instance is None:
            with cls._meta_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._sessions: dict[str, EvalSession] = {}
        return cls._instance

    def create(self) -> str:
        """Create a new session and return its ID."""
        sid = str(uuid.uuid4())
        self._sessions[sid] = EvalSession()
        return sid

    def get(self, session_id: str) -> EvalSession:
        """Retrieve an existing session. Raises KeyError if not found."""
        return self._sessions[session_id]

    def get_or_create(self, session_id: Optional[str]) -> tuple[str, EvalSession]:
        """Return existing session or create a new one."""
        if session_id and session_id in self._sessions:
            return session_id, self._sessions[session_id]
        sid = self.create()
        return sid, self._sessions[sid]


# Module-level singleton — import this everywhere
session_store = SessionStore()
