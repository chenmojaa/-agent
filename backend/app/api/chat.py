"""Chat API with per-request overrides and LangGraph streaming."""
import json
from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.storage.hybrid import hybrid_search
from app.storage.db import create_session, append_message
from app.agent.state import AgentState
from app.agent.nodes.retrieve import retrieve_node
from app.agent.nodes.answer import answer_node_stream

router = APIRouter(tags=["chat"])


class Message(BaseModel):
  role: str
  content: str


class ChatRequest(BaseModel):
  messages: list[Message]
  provider: str | None = None
  model: str | None = None
  use_rag: bool = True
  session_id: str | None = None
  base_url: str | None = None
  api_key: str | None = None
  reasoning_level: str | None = None


def _extract_query(messages: list[Message]) -> str:
  for m in reversed(messages):
    if m.role == "user" and m.content.strip():
      return m.content
  return ""


@router.post("/chat")
async def chat(body: ChatRequest, x_api_key: str | None = Header(None, alias="X-API-Key")):
  if not body.messages:
    raise HTTPException(status_code=400, detail="messages is empty")

  query = _extract_query(body.messages)
  effective_api_key = (body.api_key or x_api_key or "").strip() or None
  effective_base_url = (body.base_url or "").strip() or None

  session_id = body.session_id
  if not session_id:
    title = (query[:50] + ("..." if len(query) > 50 else "")) if query else "New chat"
    sess = create_session(title=title)
    session_id = sess.id

  if query and body.messages[-1].role == "user":
    append_message(session_id, "user", query)

  initial_state: AgentState = {
    "messages": [m.model_dump() for m in body.messages],
    "session_id": session_id,
    "query": query,
    "retrieved_chunks": [],
    "provider_override": body.provider,
    "model_override": body.model,
    "base_url_override": effective_base_url,
    "api_key_override": effective_api_key,
    "reasoning_level_override": body.reasoning_level,
    "step_count": 0,
  }

  if body.use_rag and query:
    try:
      retrieved = hybrid_search(query, top_k=5, api_key=effective_api_key, base_url=effective_base_url)
      initial_state["retrieved_chunks"] = retrieved
    except Exception:
      initial_state["retrieved_chunks"] = []

  async def generate():
    yield "event: session\ndata: " + json.dumps({"session_id": session_id}) + "\n\n"
    text_parts = []
    citations = []
    errored = False
    try:
      async for kind, payload in answer_node_stream(initial_state):
        if kind == "text_delta":
          text_parts.append(payload)
          for line in payload.split("\n"):
            yield "data: " + line + "\n"
          yield "\n"
        elif kind == "done":
          citations = payload.get("citations") or []
        elif kind == "error":
          errored = True
          yield "event: error\ndata: " + json.dumps({"detail": payload}, ensure_ascii=False) + "\n\n"
    except Exception as e:
      errored = True
      yield "event: error\ndata: " + json.dumps({"detail": str(e)}, ensure_ascii=False) + "\n\n"

    if citations:
      yield "event: citations\ndata: " + json.dumps(citations, ensure_ascii=False) + "\n\n"
    yield "data: [DONE]\n\n"

    if not errored and text_parts:
      full_text = "".join(text_parts)
      try:
        append_message(session_id, "assistant", full_text, citations if citations else None)
      except Exception:
        pass

  return StreamingResponse(
    generate(),
    media_type="text/event-stream",
    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
  )
