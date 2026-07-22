"""Answer node - LangChain ChatOpenAI with structured output and streaming."""
from __future__ import annotations

from langchain_core.messages import SystemMessage, HumanMessage

from app.llm.factory import _build_model
from app.agent.schemas import AnswerResult
from app.agent.state import AgentState


ANSWER_INSTRUCTIONS = """You are a strict assistant. Answer the question using ONLY the reference material below.

Rules:
1. Use only the reference chunks; never fabricate facts.
2. After every claim, cite the source with [n] matching the reference index.
3. If the reference material is insufficient, say so explicitly.
4. Keep the answer concise: short paragraphs or bullet points.

Reference material:
<<CONTEXT>>

Question: <<QUESTION>>
"""


def _format_context(chunks):
  if not chunks:
    return "(no reference material available)"
  out = []
  for i, c in enumerate(chunks, 1):
    title = c.get("title") or c.get("note_id", "?")
    out.append("[%d] source: %s\n%s" % (i, title, c.get("text", "")))
  return "\n\n---\n\n".join(out)


def _build_messages(state: AgentState):
  chat = _build_model(
    provider=state.get("provider_override"),
    model=state.get("model_override"),
    api_key=state.get("api_key_override"),
    base_url=state.get("base_url_override"),
    reasoning_level=state.get("reasoning_level_override"),
  )
  chunks = state.get("retrieved_chunks") or []
  question = state.get("query", "") or "(no question)"
  instructions = ANSWER_INSTRUCTIONS.replace("<<CONTEXT>>", _format_context(chunks)).replace("<<QUESTION>>", question)
  msgs = [SystemMessage(content=instructions), HumanMessage(content=question)]
  return chat, msgs


def answer_node(state: AgentState) -> dict:
  chat, msgs = _build_messages(state)
  structured = chat.with_structured_output(AnswerResult)
  result: AnswerResult = structured.invoke(msgs)
  return {
    "answer": result.text,
    "citations": [c.model_dump() for c in (result.citations or [])],
    "step_count": state.get("step_count", 0) + 1,
  }


async def answer_node_stream(state: AgentState):
  chat, msgs = _build_messages(state)
  full_text = ""
  async for chunk in chat.astream(msgs):
    delta = getattr(chunk, "content", "") or ""
    if delta:
      full_text += delta
      yield ("text_delta", delta)
  citations: list = []
  try:
    structured = chat.with_structured_output(AnswerResult)
    result: AnswerResult = await structured.ainvoke(msgs)
    citations = [c.model_dump() for c in (result.citations or [])]
  except Exception:
    citations = []
  yield ("done", {"answer": full_text, "citations": citations})
