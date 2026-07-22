"""PDF parser using pypdf."""
from __future__ import annotations

import os
from pypdf import PdfReader


def parse_pdf(path: str) -> dict:
  """Parse PDF file. Returns {title, content, word_count, page_count}."""
  if not os.path.isfile(path):
    raise FileNotFoundError(path)
  reader = PdfReader(path)
  pages_text = []
  for i, page in enumerate(reader.pages):
    txt = page.extract_text() or ""
    if txt.strip():
      pages_text.append(f"[P{i + 1}]\n" + txt)
  content = "\n\n".join(pages_text)
  if not content.strip():
    raise ValueError(f"PDF 无可提取文字（可能是扫描件）: {path}")
  return {
    "title": os.path.basename(path),
    "content": content,
    "word_count": len(content),
    "page_count": len(reader.pages),
  }