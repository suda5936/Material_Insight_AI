from scripts.build_rag_chunks import (
    DOCUMENT_METADATA_PATH,
    MATERIAL_CATALOG_PATH,
    build_document_chunks,
    build_material_chunks,
)


def test_build_material_chunks_contains_expected_catalog_entries() -> None:
    chunks = build_material_chunks(MATERIAL_CATALOG_PATH)

    source_ids = {chunk["source_id"] for chunk in chunks}
    assert "MAT-WALL-GB-001" in source_ids
    assert "MAT-FLR-PT-011" in source_ids
    assert "MAT-CLG-AC-021" in source_ids
    assert all(chunk["source_type"] == "material_catalog" for chunk in chunks)


def test_document_and_material_chunks_share_common_schema() -> None:
    chunks = [
        *build_document_chunks(DOCUMENT_METADATA_PATH),
        *build_material_chunks(MATERIAL_CATALOG_PATH),
    ]
    required_keys = {
        "chunk_id",
        "source_id",
        "source_type",
        "title",
        "section",
        "chunk_text",
        "object_types",
        "space_types",
        "performance_tags",
        "keywords",
        "version",
        "effective_date",
        "status",
        "source",
    }

    assert chunks
    assert all(required_keys <= set(chunk) for chunk in chunks)
    assert all(chunk["chunk_text"] for chunk in chunks)
