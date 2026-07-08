from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = Field(
        default="sqlite:///./dev_material_insight.db",
        alias="DATABASE_URL",
    )
    llm_provider: str = Field(default="mock", alias="LLM_PROVIDER")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-5.5", alias="OPENAI_MODEL")
    vllm_base_url: str = Field(default="http://localhost:8000/v1", alias="VLLM_BASE_URL")
    vllm_model: str = Field(default="qwen-27b", alias="VLLM_MODEL")
    rag_retriever_provider: str = Field(default="local", alias="RAG_RETRIEVER_PROVIDER")
    embedding_provider: str = Field(default="local_hash", alias="EMBEDDING_PROVIDER")
    embedding_dimensions: int = Field(default=64, alias="EMBEDDING_DIMENSIONS")
    pgvector_min_relevance_score: float = Field(
        default=5.0,
        alias="PGVECTOR_MIN_RELEVANCE_SCORE",
    )
    cors_allow_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173,http://localhost:8001,http://127.0.0.1:8001",
        alias="CORS_ALLOW_ORIGINS",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_allow_origins.split(",")
            if origin.strip()
        ]

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if not settings.database_url:
        return Settings(DATABASE_URL="sqlite:///./dev_material_insight.db")
    return settings
