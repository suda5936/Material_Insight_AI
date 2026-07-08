from sqlalchemy import create_engine

from app.models.object import DesignObjectInput
from app.services.embedding_client import LocalHashEmbeddingClient
from app.services.local_retriever import load_default_retriever
from app.services.pgvector_retriever import PgVectorRetriever, build_query_text
from app.services.rule_engine import load_default_rule_engine


def test_pgvector_retriever_falls_back_to_local_retriever_when_database_is_unavailable() -> None:
    design_object = DesignObjectInput(
        object_id="W-012",
        object_type="interior_wall",
        space_type="meeting_room",
        material=None,
        thickness_mm=75,
        user_attributes={"acoustic_required": True},
    )
    rule_results = load_default_rule_engine().evaluate(design_object)
    retriever = PgVectorRetriever(
        engine=create_engine("sqlite:///:memory:", future=True),
        embedding_client=LocalHashEmbeddingClient(dimensions=8),
        fallback_retriever=load_default_retriever(),
    )

    results = retriever.search_relevant(design_object, rule_results, limit=5)

    assert results
    assert results[0].document_id == "SPEC-INT-024"


def test_build_query_text_uses_object_and_rule_terms() -> None:
    design_object = DesignObjectInput(
        object_id="W-012",
        object_type="interior_wall",
        space_type="meeting_room",
        material=None,
    )
    rule_results = load_default_rule_engine().evaluate(design_object)

    query_text = build_query_text(design_object, rule_results)

    assert "interior_wall" in query_text
    assert "meeting_room" in query_text
    assert "material_missing" in query_text
