"""
VectorStoreManager singleton.
"""

from __future__ import annotations

import threading
from typing import Optional

from langchain_chroma import Chroma
from langchain_core.retrievers import BaseRetriever

from app.core.rag.ingestion import add_to_vectorstore, build_vectorstore
from app.core.rag.retrieval import make_retriever
from app.models.schemas import DocumentMeta


class VectorStoreManager:
    _instance: Optional["VectorStoreManager"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "VectorStoreManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._init()
        return cls._instance

    def _init(self) -> None:
        self._vectorstore: Optional[Chroma] = None
        self._retriever: Optional[BaseRetriever] = None
        self._documents: list[DocumentMeta] = []

    @property
    def is_ready(self) -> bool:
        return self._vectorstore is not None

    @property
    def retriever(self) -> Optional[BaseRetriever]:
        return self._retriever

    @property
    def documents(self) -> list[DocumentMeta]:
        return list(self._documents)

    def ingest(self, chunks: list, doc_meta: DocumentMeta) -> None:
        with self._lock:
            if self._vectorstore is None:
                self._vectorstore = build_vectorstore(chunks)
            else:
                add_to_vectorstore(self._vectorstore, chunks)
            self._retriever = make_retriever(self._vectorstore)
            self._documents.append(doc_meta)

    def get_all_chunks_for_source(self, filename: str) -> list:
        if self._vectorstore is None:
            return []
        results = self._vectorstore.get(
            where={"source": filename},
        )
        return results.get("documents", [])

    def reset(self) -> None:
        with self._lock:
            self._init()


vector_store_manager = VectorStoreManager()
