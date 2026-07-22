"""Pydantic models for the agent layer."""
from __future__ import annotations

from pydantic import BaseModel, Field


class Citation(BaseModel):
  note_id: str
  title: str | None = None
  chunk_index: int
  snippet: str
  score: float | None = None


class AnswerResult(BaseModel):
  """Structured output: free-form answer + the citations used."""
  text: str = Field(..., description="The natural-language answer")
  citations: list[Citation] = Field(default_factory=list, description="Source chunks referenced")


class Deps(BaseModel):
  """Per-request dependencies (kept for future expansion)."""
  api_key: str | None = None
  base_url: str | None = None
  retrieved_chunks: list[dict] = Field(default_factory=list)
  query: str | None = None
