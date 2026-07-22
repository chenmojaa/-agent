"""SQLite metadata store (SQLModel) + FTS5 + ChatSession/ChatMessage."""
from __future__ import annotations

import os
import json
from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel, create_engine, Session, select, text
from app.config import settings


class Note(SQLModel, table=True):
  __tablename__ = "notes"
  id: str = Field(primary_key=True)
  title: str
  source_type: str
  source_url: Optional[str] = None
  content_path: Optional[str] = None
  summary: Optional[str] = None
  tags: Optional[str] = None
  word_count: int = 0
  chunk_count: int = 0
  created_at: datetime = Field(default_factory=datetime.utcnow)
  embedded: bool = False


class ChatSession(SQLModel, table=True):
  __tablename__ = "chat_sessions"
  id: str = Field(primary_key=True)
  title: str = "新对话"
  created_at: datetime = Field(default_factory=datetime.utcnow)
  updated_at: datetime = Field(default_factory=datetime.utcnow)


class ChatMessage(SQLModel, table=True):
  __tablename__ = "chat_messages"
  id: Optional[int] = Field(default=None, primary_key=True)
  session_id: str = Field(index=True)
  role: str  # user | assistant | system
  content: str
  citations_json: Optional[str] = None
  created_at: datetime = Field(default_factory=datetime.utcnow)


_engine = None


def get_engine():
  global _engine
  if _engine is None:
    os.makedirs(os.path.dirname(settings.sqlite_path), exist_ok=True)
    _engine = create_engine(
      f"sqlite:///{settings.sqlite_path}",
      echo=False,
      connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(_engine)
    _init_fts(_engine)
  return _engine


def _init_fts(engine):
  with engine.begin() as conn:
    conn.execute(text("""
      CREATE VIRTUAL TABLE IF NOT EXISTS chunk_fts USING fts5(
        note_id UNINDEXED,
        chunk_index UNINDEXED,
        content,
        tokenize = "unicode61 remove_diacritics 2"
      )
    """))


def get_session() -> Session:
  return Session(get_engine())


# === FTS5 helpers ===
def add_fts(note_id: str, chunk_index: int, content: str):
  with get_engine().begin() as conn:
    conn.execute(
      text("INSERT INTO chunk_fts (note_id, chunk_index, content) VALUES (:nid, :idx, :c)"),
      {"nid": note_id, "idx": chunk_index, "c": content},
    )


def delete_fts(note_id: str) -> int:
  with get_engine().begin() as conn:
    result = conn.execute(
      text("DELETE FROM chunk_fts WHERE note_id = :nid"),
      {"nid": note_id},
    )
  return result.rowcount or 0


def fts_search(query: str, top_k: int = 5) -> list[dict]:
  safe = query.replace(chr(34), " ").strip()
  if not safe:
    return []
  with get_engine().begin() as conn:
    rows = conn.execute(
      text("""
        SELECT note_id, chunk_index, content, bm25(chunk_fts) AS score
        FROM chunk_fts
        WHERE chunk_fts MATCH :q
        ORDER BY score
        LIMIT :k
      """),
      {"q": safe, "k": top_k},
    ).all()
  return [
    {"note_id": r.note_id, "chunk_index": r.chunk_index, "text": r.content, "score": float(r.score) if r.score is not None else 0.0}
    for r in rows
  ]


def get_note_title(note_id: str) -> str | None:
  with get_session() as s:
    n = s.get(Note, note_id)
    return n.title if n else None


# === Chat Session helpers ===
def list_sessions(limit: int = 100) -> list[dict]:
  with get_session() as s:
    rows = s.exec(
      select(ChatSession).order_by(ChatSession.updated_at.desc()).limit(limit)
    ).all()
    out = []
    for r in rows:
      # 取最后一条消息作为 preview
      last = s.exec(
        select(ChatMessage).where(ChatMessage.session_id == r.id).order_by(ChatMessage.id.desc()).limit(1)
      ).first()
      msg_count = s.exec(
        select(ChatMessage).where(ChatMessage.session_id == r.id)
      ).all()
      out.append({
        "id": r.id,
        "title": r.title,
        "created_at": r.created_at.isoformat(),
        "updated_at": r.updated_at.isoformat(),
        "message_count": len(msg_count),
        "preview": (last.content[:60] + ("..." if last.content and len(last.content) > 60 else "")) if last else "",
      })
  return out


def get_session_with_messages(session_id: str) -> dict | None:
  with get_session() as s:
    sess = s.get(ChatSession, session_id)
    if not sess:
      return None
    msgs = s.exec(
      select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.id)
    ).all()
  return {
    "id": sess.id,
    "title": sess.title,
    "created_at": sess.created_at.isoformat(),
    "updated_at": sess.updated_at.isoformat(),
    "messages": [
      {
        "id": m.id,
        "role": m.role,
        "content": m.content,
        "citations": json.loads(m.citations_json) if m.citations_json else None,
        "created_at": m.created_at.isoformat(),
      }
      for m in msgs
    ],
  }


def create_session(title: str = "新对话") -> ChatSession:
  from uuid import uuid4
  sid = "s_" + uuid4().hex[:12]
  sess = ChatSession(id=sid, title=title[:100])
  with get_session() as s:
    s.add(sess)
    s.commit()
    s.refresh(sess)
  return sess


def delete_session(session_id: str) -> bool:
  with get_session() as s:
    sess = s.get(ChatSession, session_id)
    if not sess:
      return False
    msgs = s.exec(select(ChatMessage).where(ChatMessage.session_id == session_id)).all()
    for m in msgs:
      s.delete(m)
    s.delete(sess)
    s.commit()
  return True


def rename_session(session_id: str, title: str) -> bool:
  with get_session() as s:
    sess = s.get(ChatSession, session_id)
    if not sess:
      return False
    sess.title = title[:100]
    sess.updated_at = datetime.utcnow()
    s.add(sess)
    s.commit()
  return True


def touch_session(session_id: str) -> None:
  with get_session() as s:
    sess = s.get(ChatSession, session_id)
    if sess:
      sess.updated_at = datetime.utcnow()
      s.add(sess)
      s.commit()


def append_message(session_id: str, role: str, content: str, citations: list | None = None) -> ChatMessage:
  from sqlmodel import Session as SqlSession
  msg = ChatMessage(
    session_id=session_id,
    role=role,
    content=content,
    citations_json=json.dumps(citations, ensure_ascii=False) if citations else None,
  )
  with get_session() as s:
    s.add(msg)
    s.commit()
    s.refresh(msg)
    # 同时 touch session.updated_at
    sess = s.get(ChatSession, session_id)
    if sess:
      sess.updated_at = datetime.utcnow()
      s.add(sess)
      s.commit()
  return msg


def update_message_citations(message_id: int, citations: list) -> None:
  with get_session() as s:
    msg = s.get(ChatMessage, message_id)
    if msg:
      msg.citations_json = json.dumps(citations, ensure_ascii=False)
      s.add(msg)
      s.commit()