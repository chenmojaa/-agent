"""Search API."""
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, Field
from app.storage.hybrid import hybrid_search

router = APIRouter(tags=["search"])


class SearchRequest(BaseModel):
    query: str = Field(..., description="检索关键词或问题")
    top_k: int = Field(5, ge=1, le=20)
    base_url: str | None = Field(None, description="自定义 embedding 节点 URL，默认 None 走 EMBEDDING_API_BASE > LLM_API_BASE > openai")


@router.post("/search")
async def search(
    body: SearchRequest,
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    x_embedding_base_url: str | None = Header(None, alias="X-Embedding-Base-URL"),
):
    if not body.query.strip():
        raise HTTPException(400, "query 不能为空")
    base_url = (body.base_url or x_embedding_base_url or "").strip() or None
    hits = hybrid_search(body.query, top_k=body.top_k, api_key=x_api_key, base_url=base_url)
    return {
        "query": body.query,
        "count": len(hits),
        "results": hits,
    }