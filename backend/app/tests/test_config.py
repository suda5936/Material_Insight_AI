from app.core.config import Settings


def test_settings_have_safe_defaults() -> None:
    settings = Settings(DATABASE_URL="")

    assert settings.database_url == "sqlite+aiosqlite:///./dev_cp_recovery.db"
    assert "http://localhost:8001" in settings.cors_origins
    assert settings.rag_chunk_size_chars == 1200
    assert settings.rag_chunk_overlap_chars == 200
    assert settings.rag_final_top_k == 8
