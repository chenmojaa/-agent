"""Embedding factory - OpenAI-compatible /v1/embeddings via httpx.

No `openai` SDK dependency. Handles non-standard response envelopes (MiniMax `base_resp`)
and three common embedding response shapes.
"""
from __future__ import annotations

import httpx
from app.config import settings

OPENAI_DEFAULT_BASE = "https://api.openai.com/v1"


def _resolve_url(base_url):
  if base_url:
    return base_url.rstrip("/") + "/embeddings"
  provider = (settings.embedding_provider or "openai").strip()
  if provider == "openai":
    fallback = (
      (settings.embedding_api_base or "").strip()
      or (settings.llm_api_base or "").strip()
      or OPENAI_DEFAULT_BASE
    )
    return fallback.rstrip("/") + "/embeddings"
  raise NotImplementedError(
    f"Embedding provider not yet implemented: {provider!r}. Pass base_url= to override at call site."
  )


def _resolve_key(api_key):
  return (api_key or settings.embedding_api_key or settings.llm_api_key or "").strip()


def _resolve_model(model):
  return (model or settings.embedding_model or "").strip()


def _parse_embedding_response(j):
  """Parse an embedding response into a list[list[float]].

  Supports:
  - {"data": [{"embedding": [...]}]}    OpenAI / MiniMax
  - {"data": [[...]]}                   some providers
  - {"embeddings": [[...]]}             some providers

  Raises on upstream error envelope:
  - {"base_resp": {"status_code": 1004, "status_msg": "..."}}   MiniMax / Volcengine
  - {"error": {...}}                                            OpenAI error style
  """
  base = j.get("base_resp") if isinstance(j, dict) else None
  if isinstance(base, dict) and base.get("status_code") not in (None, 0, "0"):
    raise RuntimeError(
      f"Embedding upstream error (status_code={base.get('status_code')}): {base.get('status_msg') or j}"
    )
  if isinstance(j, dict) and isinstance(j.get("error"), dict):
    raise RuntimeError(f"Embedding upstream error: {j['error']}")

  raw = (j.get("data") if isinstance(j, dict) else None) or (j.get("embeddings") if isinstance(j, dict) else None)
  if raw is None:
    raise RuntimeError(f"Embedding response missing 'data'/'embeddings': {j}")

  vecs = []
  order = []
  for i, item in enumerate(raw):
    if isinstance(item, dict):
      emb = item.get("embedding")
      if emb is None:
        raise RuntimeError(f"Embedding item {i} missing 'embedding': {item}")
      vecs.append(emb)
      order.append(item.get("index", i))
    elif isinstance(item, list):
      vecs.append(item)
      order.append(i)
    else:
      raise RuntimeError(f"Embedding item {i} unexpected type: {type(item).__name__}")

  pairs = sorted(zip(order, vecs), key=lambda p: p[0])
  return [v for _, v in pairs]



def _build_body(inputs, model, base_url, mode="db"):
  """Provider-aware /v1/embeddings request body.

  OpenAI / standard:    {"input": [...], "model": "..."}
  MiniMax native:      {"type": "<mode>", "texts": [...], "model": "..."}

  mode: "db" for ingestion (storing), "query" for retrieval.
  MiniMax uses different embedding for indexing vs querying.
  """
  b = (base_url or "").lower()
  if "minimax" in b:
    return {"model": model, "type": mode, "texts": list(inputs)}
  return {"model": model, "input": list(inputs)}

def embed_texts(texts, api_key=None, base_url=None, model=None, mode="db"):
  """Embed a list of strings via an OpenAI-compatible /v1/embeddings endpoint."""
  if not texts:
    return []

  key = _resolve_key(api_key)
  if not key:
    raise RuntimeError("No embedding API key configured (set EMBEDDING_API_KEY or pass api_key=)")

  m = _resolve_model(model)
  if not m:
    raise RuntimeError("No embedding model configured (set EMBEDDING_MODEL or pass model=)")

  url = _resolve_url(base_url)
  headers = {
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json",
  }

  all_vecs = []
  batch = 100
  with httpx.Client(timeout=60.0) as cli:
    for i in range(0, len(texts), batch):
      chunk = texts[i:i + batch]
      body = _build_body(chunk, m, base_url, mode=mode)
      r = cli.post(url, headers=headers, json=body)
      if r.status_code != 200:
        raise RuntimeError(f"Embedding endpoint {url} returned {r.status_code}: {r.text[:300]}")
      try:
        j = r.json()
      except Exception as e:
        raise RuntimeError(f"Embedding response is not JSON: {e}; body={r.text[:200]}")
      all_vecs.extend(_parse_embedding_response(j))
  return all_vecs
