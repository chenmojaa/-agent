"""LLM factory - LangChain multi-provider with per-request overrides."""
from __future__ import annotations

from typing import Any
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

from app.config import settings

OPENAI_COMPAT_BASE_URLS: dict[str, str] = {
  "deepseek":    "https://api.deepseek.com/v1",
  "zhipu":       "https://open.bigmodel.cn/api/paas/v4",
  "moonshot":    "https://api.moonshot.cn/v1",
  "siliconflow": "https://api.siliconflow.cn/v1",
  "ollama":      "http://localhost:11434/v1",
}

NATIVE_PROVIDERS: set[str] = {"anthropic", "openai"}
ALL_PROVIDERS = sorted(NATIVE_PROVIDERS | set(OPENAI_COMPAT_BASE_URLS.keys()))

_REASONING_MAP = {"low": "low", "medium": "medium", "high": "high", "xhigh": "high"}


def _resolve_base_url(provider: str, base_url: str | None) -> str | None:
  if base_url:
    return base_url
  if provider in OPENAI_COMPAT_BASE_URLS:
    return (settings.llm_api_base or "").strip() or OPENAI_COMPAT_BASE_URLS[provider]
  return None


def _resolve_api_key(api_key: str | None) -> str | None:
  return (api_key or settings.llm_api_key or "").strip() or None


def _build_model(provider=None, model=None, api_key=None, base_url=None, reasoning_level=None):
  p = (provider or settings.llm_provider).strip()
  m = (model or settings.llm_model).strip()
  key = _resolve_api_key(api_key)
  resolved_url = _resolve_base_url(p, base_url)

  extra: dict[str, Any] = {}
  if reasoning_level in _REASONING_MAP:
    extra["reasoning_effort"] = _REASONING_MAP[reasoning_level]

  if p == "anthropic":
    return ChatAnthropic(
      model=m,
      api_key=key,
      max_tokens=4096,
    )

  kwargs: dict[str, Any] = {"model": m}
  if key:
    kwargs["api_key"] = key
  if resolved_url:
    kwargs["base_url"] = resolved_url
  if extra:
    kwargs["model_kwargs"] = extra
  return ChatOpenAI(**kwargs)


def list_providers():
  return ALL_PROVIDERS
