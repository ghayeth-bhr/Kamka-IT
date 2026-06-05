"""
Chat endpoints.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from app.core.agent.executor import build_agent_executor
from app.core.store.vector_store import vector_store_manager
from app.models.schemas import (
    AgentStep,
    ChatRequest,
    ChatResponse,
    ClearResponse,
    SourceChunk,
)

router = APIRouter(prefix="/api/chat", tags=["chat"])

_sessions: dict[str, dict[str, Any]] = {}


def _get_or_create_session(session_id: str | None) -> tuple[str, dict]:
    sid = session_id or str(uuid.uuid4())
    if sid not in _sessions:
        _sessions[sid] = {
            "history": "",
            "executor": build_agent_executor(),
        }
    return sid, _sessions[sid]


def _format_history(history: str) -> str:
    return history if history else "No prior conversation."


def _extract_sources(intermediate_steps: list) -> list[SourceChunk]:
    sources: list[SourceChunk] = []
    seen: set[str] = set()

    for action, observation in intermediate_steps:
        if action.tool != "retrieve_context":
            continue
        for block in str(observation).split("---"):
            block = block.strip()
            if not block:
                continue
            first_line = block.split("\n")[0]
            content = "\n".join(block.split("\n")[1:]).strip()
            preview = content[:200]

            filename = "unknown"
            page = None
            chunk_index = 0

            if first_line.startswith("[Chunk "):
                try:
                    inner = first_line.strip("[").split("]")[0]
                    parts = inner.split("-", 1)
                    chunk_index = int(parts[0].replace("Chunk", "").strip())
                    if len(parts) > 1:
                        rest = parts[1].strip()
                        if ", page" in rest:
                            filename, page_str = rest.split(", page", 1)
                            filename = filename.strip()
                            try:
                                page = int(page_str.strip())
                            except ValueError:
                                pass
                        else:
                            filename = rest
                except (IndexError, ValueError):
                    pass

            key = f"{filename}:{chunk_index}"
            if key not in seen:
                seen.add(key)
                sources.append(
                    SourceChunk(
                        filename=filename,
                        page=page,
                        chunk_index=chunk_index,
                        content_preview=preview,
                    )
                )

    return sources


def _extract_agent_steps(intermediate_steps: list) -> list[AgentStep]:
    steps = []
    for action, observation in intermediate_steps:
        steps.append(
            AgentStep(
                tool=action.tool,
                input=str(action.tool_input)[:300],
                output_summary=str(observation)[:200],
            )
        )
    return steps


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not vector_store_manager.is_ready:
        raise HTTPException(
            status_code=422,
            detail=(
                "No documents have been uploaded yet. "
                "Please upload at least one document before chatting."
            ),
        )

    session_id, session = _get_or_create_session(request.session_id)
    executor: Any = session["executor"]
    history: str = session["history"]

    try:
        result = executor.invoke(
            {
                "input": request.message,
                "history": _format_history(history),
            }
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Agent error: {exc}") from exc

    answer: str = result.get("output", "No answer generated.")
    intermediate = result.get("intermediate_steps", [])

    session["history"] += f"\nUSER: {request.message}\nASSISTANT: {answer}"
    lines = session["history"].strip().split("\n")
    session["history"] = "\n".join(lines[-20:])

    return ChatResponse(
        answer=answer,
        sources=_extract_sources(intermediate),
        agent_steps=_extract_agent_steps(intermediate),
        session_id=session_id,
    )


@router.post("/clear", response_model=ClearResponse)
async def clear_session(session_id: str):
    if session_id in _sessions:
        del _sessions[session_id]
    return ClearResponse(session_id=session_id, message="Session cleared.")
