"""Parse .csv -> text (stdlib csv)."""
from __future__ import annotations

import os
import csv


def parse_csv(path: str) -> dict:
  if not os.path.isfile(path):
    raise FileNotFoundError(path)
  # try utf-8, then gbk (common for Chinese exports)
  raw = None
  for enc in ("utf-8-sig", "utf-8", "gbk", "latin-1"):
    try:
      raw = open(path, "r", encoding=enc, newline="").read()
      break
    except UnicodeDecodeError:
      continue
  if raw is None:
    raw = open(path, "rb").read().decode("utf-8", errors="ignore")
  rows = list(csv.reader(raw.splitlines()))
  out = []
  for r in rows:
    cells = [(c or "").strip() for c in r]
    if any(cells):
      out.append(" | ".join(cells))
  content = "\n".join(out).strip() or "(empty csv)"
  title = os.path.splitext(os.path.basename(path))[0] or "Untitled CSV"
  return {"title": title[:200], "content": content}
