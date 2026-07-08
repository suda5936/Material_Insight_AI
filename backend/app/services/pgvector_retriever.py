from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import Settings, get_settings
from app.db.session import engine as default_engine
from app.models.document import RetrievedDocument
from app.models.object import DesignObjectInput
from app.models.rule import RuleResult
from app.services.embedding_client import EmbeddingClient, build_embedding_client, vector_to_pg_literal
from app.services.local_retriever import (
    DEFAULT_MIN_RELEVANCE_SCORE,
    LocalRetriever,
    build_query_terms,
    load_default_retriever,
)


PGVECTOR_TABLE_NAME = "rag_chunks"


class PgVectorRetrieverError(RuntimeError):
    pass


@dataclass(frozen=True)
class PgVectorRetriever:
    engine: Engine
    embedding_client: EmbeddingClient
    fallback_retriever: LocalRetriever | None = None
    min_score: float = DEFAULT_MIN_RELEVANCE_SCORE

    def search(
        self,
        design_object: DesignObjectInput,
        rule_results: Sequence[RuleResult],
        limit: int = 5,
    ) -> list[RetrievedDocument]:
        query_text = build_query_text(design_object, rule_results)
        embedding = vector_to_pg_literal(self.embedding_client.embed_text(query_text))
        sql = text(
            f"""
            select
              source_id,
              source_type,
              title,
              section,
              chunk_text,
              version,
              effective_date,
              status,
              source,
              10.0 / (1.0 + (embedding <=> cast(:embedding as vector))) as score
            from {PGVECTOR_TABLE_NAME}
            where status = 'active'
            order by embedding <=> cast(:embedding as vector)
            limit :limit
            """
        )
        try:
            with self.engine.connect() as connection:
                rows = connection.execute(
                    sql,
                    {"embedding": embedding, "limit": limit},
                ).mappings()
                return [_row_to_document(row) for row in rows]
        except SQLAlchemyError as exc:
            if self.fallback_retriever is None:
                raise PgVectorRetrieverError(str(exc)) from exc
            return self.fallback_retriever.search(design_object, rule_results, limit=limit)

    def search_relevant(
        self,
        design_object: DesignObjectInput,
        rule_results: Sequence[RuleResult],
        limit: int = 5,
        min_score: float | None = None,
    ) -> list[RetrievedDocument]:
        threshold = self.min_score if min_score is None else min_score
        candidates = self.search(design_object, rule_results, limit=limit)
        return [document for document in candidates if document.score >= threshold]


def load_default_pgvector_retriever(settings: Settings | None = None) -> PgVectorRetriever:
    settings = settings or get_settings()
    return PgVectorRetriever(
        engine=default_engine,
        embedding_client=build_embedding_client(
            settings.embedding_provider,
            settings.embedding_dimensions,
        ),
        fallback_retriever=load_default_retriever(),
        min_score=settings.pgvector_min_relevance_score,
    )


def build_query_text(
    design_object: DesignObjectInput,
    rule_results: Sequence[RuleResult],
) -> str:
    query_terms = sorted(build_query_terms(design_object, rule_results))
    return " ".join(query_terms)


def _row_to_document(row) -> RetrievedDocument:
    return RetrievedDocument(
        document_id=row["source_id"],
        title=row["title"],
        section=row["section"],
        chunk_text=row["chunk_text"],
        document_type=row["source_type"],
        score=round(float(row["score"]), 3),
        version=row["version"],
        effective_date=row["effective_date"],
        status=row["status"],
        source=row["source"],
    )
