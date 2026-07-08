from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

from sqlalchemy import text


BACKEND_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_ROOT.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import get_settings
from app.db.session import engine
from app.services.embedding_client import build_embedding_client, vector_to_pg_literal
from app.services.pgvector_retriever import PGVECTOR_TABLE_NAME
from scripts.build_rag_chunks import OUTPUT_PATH, main as build_rag_chunks


def main() -> None:
    settings = get_settings()
    if not settings.database_url.startswith("postgresql"):
        raise RuntimeError(
            "pgvector ingestion requires PostgreSQL. "
            "Set DATABASE_URL=postgresql+psycopg://..."
        )

    if not OUTPUT_PATH.exists():
        build_rag_chunks()

    chunks = load_jsonl(OUTPUT_PATH)
    embedding_client = build_embedding_client(
        settings.embedding_provider,
        settings.embedding_dimensions,
    )

    with engine.begin() as connection:
        connection.execute(text("create extension if not exists vector"))
        connection.execute(text(create_pgvector_table_sql(settings.embedding_dimensions)))
        connection.execute(text(f"delete from {PGVECTOR_TABLE_NAME}"))
        for chunk in chunks:
            embedding_text = build_embedding_text(chunk)
            embedding = vector_to_pg_literal(embedding_client.embed_text(embedding_text))
            connection.execute(
                text(insert_pgvector_chunk_sql()),
                {
                    "chunk_id": chunk["chunk_id"],
                    "source_id": chunk["source_id"],
                    "source_type": chunk["source_type"],
                    "title": chunk["title"],
                    "section": chunk["section"],
                    "chunk_text": chunk["chunk_text"],
                    "object_types": json.dumps(chunk["object_types"], ensure_ascii=False),
                    "space_types": json.dumps(chunk["space_types"], ensure_ascii=False),
                    "performance_tags": json.dumps(chunk["performance_tags"], ensure_ascii=False),
                    "keywords": json.dumps(chunk["keywords"], ensure_ascii=False),
                    "version": chunk["version"],
                    "effective_date": chunk["effective_date"],
                    "status": chunk["status"],
                    "source": chunk["source"],
                    "embedding": embedding,
                },
            )

    print(f"ingested_pgvector_chunks: {len(chunks)} ({OUTPUT_PATH})")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def build_embedding_text(chunk: dict[str, Any]) -> str:
    values = [
        chunk.get("title"),
        chunk.get("section"),
        chunk.get("chunk_text"),
        *chunk.get("object_types", []),
        *chunk.get("space_types", []),
        *chunk.get("performance_tags", []),
        *chunk.get("keywords", []),
    ]
    return " ".join(str(value) for value in values if value)


def create_pgvector_table_sql(dimensions: int) -> str:
    return f"""
    create table if not exists {PGVECTOR_TABLE_NAME} (
      chunk_id text primary key,
      source_id text not null,
      source_type text not null,
      title text not null,
      section text,
      chunk_text text not null,
      object_types jsonb not null default '[]'::jsonb,
      space_types jsonb not null default '[]'::jsonb,
      performance_tags jsonb not null default '[]'::jsonb,
      keywords jsonb not null default '[]'::jsonb,
      version text,
      effective_date text,
      status text not null default 'active',
      source text,
      embedding vector({dimensions}) not null,
      created_at timestamptz not null default now()
    )
    """


def insert_pgvector_chunk_sql() -> str:
    return f"""
    insert into {PGVECTOR_TABLE_NAME} (
      chunk_id,
      source_id,
      source_type,
      title,
      section,
      chunk_text,
      object_types,
      space_types,
      performance_tags,
      keywords,
      version,
      effective_date,
      status,
      source,
      embedding
    ) values (
      :chunk_id,
      :source_id,
      :source_type,
      :title,
      :section,
      :chunk_text,
      cast(:object_types as jsonb),
      cast(:space_types as jsonb),
      cast(:performance_tags as jsonb),
      cast(:keywords as jsonb),
      :version,
      :effective_date,
      :status,
      :source,
      cast(:embedding as vector)
    )
    """


if __name__ == "__main__":
    main()
