"""
Retrieval helpers.
"""

from __future__ import annotations

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

from app.config import settings


def make_retriever(
    vectorstore: Chroma,
    k: int | None = None,
    search_type: str = "similarity",
) -> BaseRetriever:
    return vectorstore.as_retriever(
        search_type=search_type,
        search_kwargs={"k": k or settings.retriever_k},
    )


def retrieve(retriever: BaseRetriever, query: str) -> list[Document]:
    return retriever.invoke(query)
