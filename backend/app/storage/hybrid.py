"""Hybrid search: vector (Chroma) + keyword (FTS5) -> dedupe + rerank."""
from __future__ import annotations

import logging
import re

from app.embeddings.factory import embed_texts
from app.storage.vector import search as vector_search
from app.storage.db import fts_search


def _make_key(note_id: str, chunk_index: int) -> str:
  return f"{note_id}#{chunk_index}"


def _fts_escape(query: str) -> str:
  """Make a string safe for SQLite FTS5 MATCH.

  FTS5 treats double quotes and a few ASCII chars as syntax. Strip them and
  wrap the cleaned string in double quotes so the engine treats it as a phrase
  and tokenizes CJK characters correctly even for 2-3 char queries.
  """
  if not query:
    return ""
  s = query.strip()
  if not s:
    return ""
  # FTS5 reserved chars: " ( ) * ^ : AND OR NOT NEAR
  for ch in (chr(34), '(', ')', '*', '^', ':'):
    s = s.replace(ch, ' ')
  s = s.strip()
  if not s:
    return ""
  return chr(34) + s + chr(34)



def hybrid_search(
  query: str,
  top_k: int = 5,
  api_key: str | None = None,
  base_url: str | None = None,
  model: str | None = None,
) -> list[dict]:
  """Combine vector + keyword search, dedupe, return top_k.

  base_url lets the caller reuse the same OpenAI-compatible endpoint that
  chat is using, so embeddings stay consistent with whatever was at ingest.
  """
  # vector search
  vec_hits: list[dict] = []
  try:
    emb = embed_texts([query], api_key=api_key, base_url=base_url, model=model, mode="query")[0]
    vec_hits = vector_search(emb, top_k=top_k * 2)
    for h in vec_hits:
      d = h.get("distance")
      h["vec_score"] = max(0.0, 1.0 - (d if d is not None else 1.0))
  except Exception as e:
    # MiniMax rejects type="query" on embo-01 with status_code=2013.
    # Fall back to type="db" (ingestion mode) which is the only one MiniMax embo-01 accepts.
    try:
      emb = embed_texts([query], api_key=api_key, base_url=base_url, model=model, mode="db")[0]
      vec_hits = vector_search(emb, top_k=top_k * 2)
      for h in vec_hits:
        d = h.get("distance")
        h["vec_score"] = max(0.0, 1.0 - (d if d is not None else 1.0))
    except Exception as e2:
      logging.getLogger(__name__).warning("hybrid_search vector embed failed (query mode: %s; db fallback: %s)", e, e2)

  # keyword search (FTS5 / BM25)
  kw_hits = []
  try:
    safe_q = _fts_escape(query)
    if safe_q:
      kw_hits = fts_search(safe_q, top_k=top_k * 2)
      for h in kw_hits:
        s = h.get("score") or 0.0
        h["kw_score"] = 1.0 / (1.0 + abs(s))
  except Exception as e:
    logging.getLogger(__name__).warning("hybrid_search fts failed: %s", e)

  # merge + dedupe by (note_id, chunk_index)
  merged = {}
  for h in vec_hits:
    k = _make_key(h["note_id"], h["chunk_index"])
    merged[k] = {
      "note_id": h["note_id"],
      "chunk_index": h["chunk_index"],
      "text": h["text"],
      "vec_score": h.get("vec_score", 0.0),
      "kw_score": 0.0,
    }
  for h in kw_hits:
    k = _make_key(h["note_id"], h["chunk_index"])
    if k in merged:
      merged[k]["kw_score"] = h.get("kw_score", 0.0)
    else:
      merged[k] = {
        "note_id": h["note_id"],
        "chunk_index": h["chunk_index"],
        "text": h["text"],
        "vec_score": 0.0,
        "kw_score": h.get("kw_score", 0.0),
      }

  # combined: vector 0.7 + keyword 0.3
  ranked = sorted(
    merged.values(),
    key=lambda x: 0.7 * x["vec_score"] + 0.3 * x["kw_score"],
    reverse=True,
  )[:top_k]

  from app.storage.db import get_note_title
  for r in ranked:
    r["title"] = get_note_title(r["note_id"])
    r["final_score"] = round(0.7 * r["vec_score"] + 0.3 * r["kw_score"], 4)

  return ranked
