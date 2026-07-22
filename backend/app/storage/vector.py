"""Chroma vector store wrapper + FTS5 sync."""
from __future__ import annotations

import os
import chromadb
from app.config import settings
from app.storage.db import add_fts, delete_fts

_client = None
_collection = None


def get_collection():
  global _client, _collection
  if _collection is None:
    os.makedirs(settings.chroma_dir, exist_ok=True)
    _client = chromadb.PersistentClient(path=settings.chroma_dir)
    _collection = _client.get_or_create_collection(
      name="notes",
      metadata={"hnsw:space": "cosine"},
    )
  return _collection


def add_chunks(note_id: str, chunks: list[str], embeddings: list[list[float]]) -> int:
  if not chunks:
    return 0
  col = get_collection()
  ids = [f"{note_id}_c{i}" for i in range(len(chunks))]
  metadatas = [{"note_id": note_id, "chunk_index": i} for i in range(len(chunks))]
  col.add(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)
  # 同步 FTS5
  for i, content in enumerate(chunks):
    add_fts(note_id, i, content)
  return len(chunks)


def search(query_embedding: list[float], top_k: int = 5) -> list[dict]:
  col = get_collection()
  res = col.query(query_embeddings=[query_embedding], n_results=top_k)
  out = []
  if not res or not res["ids"] or not res["ids"][0]:
    return out
  for i, cid in enumerate(res["ids"][0]):
    out.append({
      "chunk_id": cid,
      "note_id": res["metadatas"][0][i]["note_id"],
      "chunk_index": res["metadatas"][0][i]["chunk_index"],
      "text": res["documents"][0][i],
      "distance": res["distances"][0][i] if res.get("distances") else None,
    })
  return out


def delete_note_chunks(note_id: str) -> int:
  col = get_collection()
  existing = col.get(where={"note_id": note_id})
  n = 0
  if existing and existing["ids"]:
    col.delete(ids=existing["ids"])
    n = len(existing["ids"])
  delete_fts(note_id)
  return n


def collection_stats() -> dict:
  col = get_collection()
  return {"count": col.count(), "name": col.name}