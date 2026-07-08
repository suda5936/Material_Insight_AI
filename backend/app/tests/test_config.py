from app.core.config import Settings


def test_llm_settings_have_safe_defaults() -> None:
    settings = Settings(DATABASE_URL="")

    assert settings.llm_provider == "mock"
    assert settings.openai_model == "gpt-5.5"
    assert settings.vllm_model == "Qwen/Qwen3.5-27B"
    assert settings.rag_retriever_provider == "local"
    assert settings.embedding_provider == "local_hash"
    assert settings.embedding_dimensions == 64
    assert "http://localhost:8001" in settings.cors_origins
