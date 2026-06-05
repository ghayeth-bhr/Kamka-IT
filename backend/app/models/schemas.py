from __future__ import annotations

from datetime import datetime
from typing import Optional
import uuid

from pydantic import BaseModel, Field


class DocumentMeta(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    chunks_count: int
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class UploadResponse(BaseModel):
    documents: list[DocumentMeta]
    message: str
    errors: list[str] | None = None


class DocumentListResponse(BaseModel):
    documents: list[DocumentMeta]


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="The user's question")
    session_id: Optional[str] = Field(
        default=None,
        description=(
            "Optional session ID for multi-turn conversations. "
            "Omit on first turn; reuse the returned value on subsequent turns."
        ),
    )


class SourceChunk(BaseModel):
    filename: str
    page: Optional[int] = None
    chunk_index: int
    content_preview: str


class AgentStep(BaseModel):
    tool: str
    input: str
    output_summary: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]
    agent_steps: list[AgentStep]
    session_id: str


class ClearResponse(BaseModel):
    session_id: str
    message: str
