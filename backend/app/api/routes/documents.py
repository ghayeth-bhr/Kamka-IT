"""
Document management endpoints.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File

from app.core.rag.ingestion import chunk_pdf, chunk_text
from app.core.store.vector_store import vector_store_manager
from app.models.schemas import DocumentListResponse, DocumentMeta, UploadResponse

router = APIRouter(prefix="/api/documents", tags=["documents"])

ALLOWED_EXTENSIONS = {".pdf", ".txt"}


@router.post("/upload", response_model=UploadResponse, status_code=201)
async def upload_documents(files: list[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    ingested: list[DocumentMeta] = []
    errors: list[str] = []

    for upload in files:
        filename = upload.filename or "unnamed"
        ext = Path(filename).suffix.lower()

        if ext not in ALLOWED_EXTENSIONS:
            errors.append(
                f"'{filename}': unsupported type '{ext}'. "
                f"Accepted: {sorted(ALLOWED_EXTENSIONS)}"
            )
            continue

        raw_bytes = await upload.read()

        if ext == ".pdf":
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(raw_bytes)
                tmp_path = Path(tmp.name)
            try:
                chunks = chunk_pdf(tmp_path)
                for chunk in chunks:
                    chunk.metadata["source"] = filename
            except Exception as exc:
                errors.append(f"'{filename}': failed to read PDF ({exc}).")
                continue
            finally:
                tmp_path.unlink(missing_ok=True)
        else:
            text = raw_bytes.decode("utf-8", errors="ignore")
            chunks = chunk_text(text, source=filename)

        if not chunks:
            errors.append(f"'{filename}': no content extracted.")
            continue

        meta = DocumentMeta(filename=filename, chunks_count=len(chunks))
        vector_store_manager.ingest(chunks, meta)
        ingested.append(meta)

    if not ingested:
        raise HTTPException(
            status_code=422,
            detail=(
                f"No documents were ingested. Errors: {errors or ['unknown error']}"
            ),
        )

    message = f"Successfully ingested {len(ingested)} document(s)."
    if errors:
        message += f" {len(errors)} file(s) failed."

    return UploadResponse(
        documents=ingested,
        message=message,
        errors=errors or None,
    )


@router.get("", response_model=DocumentListResponse)
async def list_documents():
    return DocumentListResponse(documents=vector_store_manager.documents)
