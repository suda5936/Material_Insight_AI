from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = Field(
        default="sqlite+aiosqlite:///./dev_cp_recovery.db",
        alias="DATABASE_URL",
    )
    cors_allow_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173,http://localhost:8001,http://127.0.0.1:8001",
        alias="CORS_ALLOW_ORIGINS",
    )
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4.1-mini", alias="OPENAI_MODEL")
    openai_embedding_model: str = Field(
        default="text-embedding-3-small", alias="OPENAI_EMBEDDING_MODEL"
    )
    embedding_dimensions: int = Field(default=1536, alias="EMBEDDING_DIMENSIONS")
    vllm_gemma_base_url: str = Field(
        default="http://localhost:8002/v1",
        alias="VLLM_GEMMA_BASE_URL",
    )
    vllm_gemma_model: str = Field(default="gemma-4b", alias="VLLM_GEMMA_MODEL")
    rag_chunk_size_chars: int = Field(default=1200, alias="RAG_CHUNK_SIZE_CHARS")
    rag_chunk_overlap_chars: int = Field(default=200, alias="RAG_CHUNK_OVERLAP_CHARS")
    rag_vector_top_k: int = Field(default=20, alias="RAG_VECTOR_TOP_K")
    rag_final_top_k: int = Field(default=8, alias="RAG_FINAL_TOP_K")
    rag_min_score: float = Field(default=0.35, alias="RAG_MIN_SCORE")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @field_validator("database_url", mode="before")
    @classmethod
    def use_default_database_when_empty(cls, value: str | None) -> str:
        if value is None or not str(value).strip():
            return "sqlite+aiosqlite:///./dev_cp_recovery.db"
        return str(value)

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
    return Settings()
