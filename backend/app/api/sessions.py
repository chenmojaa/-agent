"""Chat session REST API."""
from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.storage.db import (
  list_sessions, get_session_with_messages, create_session,
  delete_session, rename_session,
)

router = APIRouter(tags=["sessions"])


class CreateSessionRequest(BaseModel):
  title: Optional[str] = Field(None, description="可选标题，默认 新对话")


class RenameRequest(BaseModel):
  title: str = Field(..., min_length=1, max_length=100)


@router.get("/sessions")
async def api_list_sessions(limit: int = 100):
  return {"items": list_sessions(limit=limit)}


@router.post("/sessions")
async def api_create_session(body: CreateSessionRequest = CreateSessionRequest()):
  s = create_session(body.title or "新对话")
  return {"id": s.id, "title": s.title, "created_at": s.created_at.isoformat()}


@router.get("/sessions/{session_id}")
async def api_get_session(session_id: str):
  data = get_session_with_messages(session_id)
  if not data:
    raise HTTPException(404, "Session not found")
  return data


@router.delete("/sessions/{session_id}")
async def api_delete_session(session_id: str):
  ok = delete_session(session_id)
  if not ok:
    raise HTTPException(404, "Session not found")
  return {"deleted": session_id}


@router.patch("/sessions/{session_id}")
async def api_rename_session(session_id: str, body: RenameRequest):
  ok = rename_session(session_id, body.title)
  if not ok:
    raise HTTPException(404, "Session not found")
  return {"renamed": session_id, "title": body.title}