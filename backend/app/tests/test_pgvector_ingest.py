from scripts.ingest_rag_chunks_pgvector import (
    build_embedding_text,
    create_pgvector_table_sql,
    insert_pgvector_chunk_sql,
)


def test_pgvector_table_sql_uses_vector_dimension_and_metadata_fields() -> None:
    sql = create_pgvector_table_sql(64)

    assert "create table if not exists rag_chunks" in sql
    assert "embedding vector(64)" in sql
    assert "object_types jsonb" in sql
    assert "effective_date text" in sql


def test_insert_pgvector_chunk_sql_casts_json_and_vector_values() -> None:
    sql = insert_pgvector_chunk_sql()

    assert "cast(:object_types as jsonb)" in sql
    assert "cast(:embedding as vector)" in sql


def test_build_embedding_text_combines_searchable_chunk_fields() -> None:
    text = build_embedding_text(
        {
            "title": "Meeting room wall",
            "section": "4.2",
            "chunk_text": "Acoustic review required.",
            "object_types": ["interior_wall"],
            "space_types": ["meeting_room"],
            "performance_tags": ["acoustic"],
            "keywords": ["material_missing"],
        }
    )

    assert "Meeting room wall" in text
    assert "interior_wall" in text
    assert "material_missing" in text
