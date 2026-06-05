"""
Document ingestion: loading, chunking, vectorstore creation.

Logic ported from notebook. Chunking parameters and splitter
strategy are intentional.
"""

from __future__ import annotations

from pathlib import Path

from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings


def _make_splitter() -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", " ", ""],
    )


def chunk_pdf(pdf_path: Path) -> list[Document]:
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    docs = PyPDFLoader(str(pdf_path)).load()
    return _make_splitter().split_documents(docs)


def chunk_text(raw_text: str, source: str = "uploaded_text") -> list[Document]:
    splitter = _make_splitter()
    chunks = splitter.create_documents([raw_text])
    for chunk in chunks:
        chunk.metadata.setdefault("source", source)
    return chunks


def build_vectorstore(chunks: list[Document]) -> Chroma:
    embeddings = HuggingFaceEmbeddings(model_name=settings.embeddings_model)
    return Chroma.from_documents(chunks, embeddings)


def add_to_vectorstore(vectorstore: Chroma, chunks: list[Document]) -> None:
    vectorstore.add_documents(chunks)
