from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
  model_config = SettingsConfigDict(
    env_file=".env",
    env_file_encoding="utf-8",
    extra="ignore",
    case_sensitive=False,
  )

  # ---- LLM ----
  llm_provider: str = "openai"
  llm_model: str = "gpt-4o-mini"
  llm_api_key: str = ""
  llm_api_base: str = ""

  # ---- Embedding ----
  embedding_provider: str = "openai"
  embedding_model: str = "text-embedding-3-small"
  embedding_api_key: str = ""
  embedding_api_base: str = ""
  embedding_device: str = "cpu"

  # ---- Server ----
  host: str = "127.0.0.1"
  port: int = 8000
  log_level: str = "info"

  # ---- Storage (P2) ----
  data_dir: str = "./data"
  sqlite_path: str = "./data/notes.db"
  chroma_dir: str = "./data/chroma"
  notes_dir: str = "./data/notes"

  # ---- Ingestion ----
  chunk_size: int = 500
  chunk_overlap: int = 80


@lru_cache
def get_settings() -> Settings:
  return Settings()


settings = get_settings()