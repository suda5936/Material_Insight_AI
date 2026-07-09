from datetime import datetime, timezone

from app.db.models import KnowledgeChunk, KnowledgeDocument, Project
from app.services.evidence import validate_evidence_chunk_ids
from app.services.retrieval import cosine_similarity, search_knowledge_chunks
from app.tests.fakes import HashingEmbeddingProvider

from app.core.errors import APIError
import pytest


def test_cosine_similarity_identical_vectors_is_one() -> None:
    assert cosine_similarity([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) == pytest.approx(1.0)


def test_cosine_similarity_orthogonal_vectors_is_zero() -> None:
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)


def test_cosine_similarity_zero_vector_is_zero() -> None:
    assert cosine_similarity([0.0, 0.0], [1.0, 2.0]) == 0.0


async def _seed_document(db_session, project_id, source_name, trade, location, approval_status, date, text):
    provider = HashingEmbeddingProvider()
    document = KnowledgeDocument(
        project_id=project_id,
        source_name=source_name,
        document_type="meeting_minutes",
        document_date=date,
        approval_status=approval_status,
        trade=trade,
        location=location,
        raw_text=text,
    )
    db_session.add(document)
    await db_session.flush()

    embedding = await provider.embed_one(text)
    db_session.add(
        KnowledgeChunk(
            document_id=document.id,
            project_id=project_id,
            chunk_index=0,
            content=text,
            embedding=embedding,
        )
    )
    await db_session.commit()
    return document


async def test_search_returns_most_relevant_chunk_first(db_session) -> None:
    project = Project(name="Tower A")
    db_session.add(project)
    await db_session.flush()

    today = datetime.now(timezone.utc).date().isoformat()
    await _seed_document(
        db_session,
        project.id,
        "curtain_wall_delay_notice.md",
        trade="curtain wall",
        location="A-12F",
        approval_status="approved",
        date=today,
        text="Curtain wall material delivery delayed at building A twelfth floor site",
    )
    await _seed_document(
        db_session,
        project.id,
        "unrelated_minutes.md",
        trade="electrical",
        location="B-3F",
        approval_status="approved",
        date=today,
        text="Electrical panel inspection completed without issues",
    )

    results = await search_knowledge_chunks(
        db=db_session,
        embedding_provider=HashingEmbeddingProvider(),
        project_id=project.id,
        query_text="curtain wall material delivery delayed twelfth floor",
        trade_hint="curtain wall",
        location_hint="A-12F",
    )

    assert len(results) == 1
    assert results[0].source_name == "curtain_wall_delay_notice.md"
    assert results[0].vector_similarity > 0.3


async def test_search_returns_empty_when_below_threshold(db_session) -> None:
    project = Project(name="Tower B")
    db_session.add(project)
    await db_session.flush()

    await _seed_document(
        db_session,
        project.id,
        "unrelated.md",
        trade="electrical",
        location="B-3F",
        approval_status="approved",
        date="2020-01-01",
        text="Completely unrelated topic about landscaping schedules",
    )

    results = await search_knowledge_chunks(
        db=db_session,
        embedding_provider=HashingEmbeddingProvider(),
        project_id=project.id,
        query_text="curtain wall material delivery delayed twelfth floor",
    )

    assert results == []


async def test_search_scoped_to_project(db_session) -> None:
    project_a = Project(name="A")
    project_b = Project(name="B")
    db_session.add_all([project_a, project_b])
    await db_session.flush()

    today = datetime.now(timezone.utc).date().isoformat()
    await _seed_document(
        db_session,
        project_b.id,
        "b_doc.md",
        trade="curtain wall",
        location="A-12F",
        approval_status="approved",
        date=today,
        text="Curtain wall material delivery delayed at building A twelfth floor site",
    )

    results = await search_knowledge_chunks(
        db=db_session,
        embedding_provider=HashingEmbeddingProvider(),
        project_id=project_a.id,
        query_text="curtain wall material delivery delayed twelfth floor",
    )

    assert results == []


def test_validate_evidence_chunk_ids_passes_when_subset() -> None:
    validate_evidence_chunk_ids(claimed_chunk_ids=[1, 2], allowed_chunk_ids=[1, 2, 3])


def test_validate_evidence_chunk_ids_rejects_unknown_id() -> None:
    with pytest.raises(APIError) as excinfo:
        validate_evidence_chunk_ids(claimed_chunk_ids=[1, 99], allowed_chunk_ids=[1, 2, 3])

    assert excinfo.value.error_code == "evidence_not_in_allowlist"
