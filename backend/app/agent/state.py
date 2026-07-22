"""LangGraph state schema for the HEAR agent."""
from __future__ import annotations

from typing import TypedDict


class AgentState(TypedDict, total=False):
  messages: list
  session_id: str
  query: str
  retrieved_chunks: list
  answer: str | None
  citations: list
  provider_override: str | None
  model_override: str | None
  base_url_override: str | None
  api_key_override: str | None
  reasoning_level_override: str | None
  step_count: int
