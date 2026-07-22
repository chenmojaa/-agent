"""Text chunking - sliding window with paragraph/sentence boundary preference."""
from __future__ import annotations


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 80) -> list[str]:
  """Split text into chunks of approximately chunk_size chars.
  Tries to break at sentence/paragraph boundaries.
  """
  text = (text or "").strip()
  if not text:
    return []
  if len(text) <= chunk_size:
    return [text]

  seps = ["\n\n", "。", "！", "？", "\n", ". ", "! ", "? ", " "]
  chunks: list[str] = []
  start = 0
  n = len(text)
  while start < n:
    end = min(start + chunk_size, n)
    if end < n:
      best_idx = -1
      best_sep_len = 0
      for sep in seps:
        idx = text.rfind(sep, start, end)
        if idx > start + chunk_size // 2 and idx > best_idx:
          best_idx = idx
          best_sep_len = len(sep)
      if best_idx > 0:
        end = best_idx + best_sep_len
    piece = text[start:end].strip()
    if piece:
      chunks.append(piece)
    if end >= n:
      break
    start = max(end - overlap, start + 1)
  return chunks