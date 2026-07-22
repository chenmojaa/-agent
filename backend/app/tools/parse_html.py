"""Parse .html / .htm -> clean text via BeautifulSoup."""
from __future__ import annotations

import os
import re
from bs4 import BeautifulSoup


def parse_html(path: str) -> dict:
  if not os.path.isfile(path):
    raise FileNotFoundError(path)
  with open(path, "r", encoding="utf-8", errors="ignore") as f:
    raw = f.read()
  soup = BeautifulSoup(raw, "html.parser")
  for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
    tag.decompose()
  title = ""
  if soup.title and soup.title.string:
    title = soup.title.string.strip()[:200]
  if not title:
    h1 = soup.find("h1")
    if h1:
      title = h1.get_text(strip=True)[:200]
  if not title:
    title = os.path.splitext(os.path.basename(path))[0]
  text = soup.get_text(separator="\n")
  text = re.sub(r"\n\s*\n+", "\n\n", text)
  text = re.sub(r"[ \t]+", " ", text)
  content = text.strip() or "(empty html)"
  return {"title": title[:200], "content": content}
