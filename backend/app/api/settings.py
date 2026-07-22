"""Settings API: list available providers, auto-detect custom model lists."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import httpx

from app.llm.factory import list_providers

router = APIRouter(tags=["settings"])


@router.get("/settings/models")
async def list_models():
  from app.config import settings
  return {
    "providers": list_providers(),
    "current": {
      "llm_provider": settings.llm_provider,
      "llm_model": settings.llm_model,
      "llm_api_base": settings.llm_api_base,
      "embedding_provider": settings.embedding_provider,
      "embedding_model": settings.embedding_model,
    },
  }


class CustomModelsRequest(BaseModel):
  """Auto-detect models exposed by an OpenAI-compatible endpoint."""
  base_url: str = Field(..., description="e.g. https://api.openai.com/v1")
  api_key: str = Field(..., description="Bearer token")


@router.post("/settings/custom-models")
async def custom_models(body: CustomModelsRequest):
  """Call <base_url>/models with Authorization Bearer <api_key>, return id list."""
  base = body.base_url.rstrip("/")
  url = base + "/models"
  headers = {"Authorization": f"Bearer {body.api_key}"}
  try:
    async with httpx.AsyncClient(timeout=15.0) as cli:
      r = await cli.get(url, headers=headers)
  except Exception as e:
    raise HTTPException(status_code=400, detail=f"网络错误：{e}")
  if r.status_code != 200:
    raise HTTPException(status_code=400, detail=f"上游返回 {r.status_code}: {r.text[:200]}")
  try:
    j = r.json()
  except Exception:
    raise HTTPException(status_code=400, detail="上游响应不是 JSON")
  data = j.get("data") or j.get("models") or []
  ids: list[str] = []
  for m in data:
    if isinstance(m, dict):
      mid = m.get("id") or m.get("name")
      if mid: ids.append(str(mid))
    elif isinstance(m, str):
      ids.append(m)
  if not ids:
    raise HTTPException(status_code=400, detail="未识别到任何模型")
  # 推断 provider：根据 base_url 关键字
  provider = "openai"
  b = body.base_url.lower()
  if "deepseek" in b: provider = "deepseek"
  elif "zhipu" in b or "bigmodel" in b: provider = "zhipu"
  elif "moonshot" in b: provider = "moonshot"
  elif "siliconflow" in b: provider = "siliconflow"
  elif "ollama" in b or "11434" in b: provider = "ollama"
  return {"provider": provider, "base_url": base, "models": ids}