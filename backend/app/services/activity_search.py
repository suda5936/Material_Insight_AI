"""Activity 후보 검색 — 어휘(lexical) 기반 검색.

[수업 정리] 벡터 검색 vs 어휘 검색, 그리고 하이브리드.
------------------------------------------------------------------
RAG의 문서 검색(retrieval.py)은 "의미(임베딩 벡터)" 기반이었다. 반면 여기 Activity
후보 검색은 pg_trgm(트라이그램 문자열 유사도) 기반의 "어휘/키워드" 검색이다.
    - 벡터 검색  ≈ semantic search  (의미가 비슷하면 매칭)
    - pg_trgm    ≈ lexical search   (글자가 겹치면 매칭, BM25/키워드 검색과 유사)
LangChain으로 치면 BM25Retriever 계열이고, 둘을 합치면 EnsembleRetriever(하이브리드)다.

Activity 이름은 "A동 12층 커튼월 설치"처럼 짧은 고유명사라 어휘 검색이 잘 맞는다.
PostgreSQL이면 similarity()(pg_trgm)를, SQLite 테스트면 토큰 오버랩으로 폴백한다.
여기서 뽑은 후보를 Issue Mapping Agent(LLM)가 다시 re-rank 한다(SQL 후보 → LLM 재순위).
"""

import re
from dataclasses import dataclass

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Activity

_TOKEN_PATTERN = re.compile(r"[0-9a-zA-Z가-힣]+")


@dataclass(frozen=True)
class ActivityMatchCandidate:
    activity_id: str
    name: str
    is_completed: bool
    sql_score: float


def _tokens(value: str) -> set[str]:
    return {t.lower() for t in _TOKEN_PATTERN.findall(value)}


def _fallback_score(query: str, name: str) -> float:
    """Token-overlap similarity used when pg_trgm is unavailable (e.g. SQLite tests)."""
    q_tokens = _tokens(query)
    n_tokens = _tokens(name)
    if not q_tokens or not n_tokens:
        return 0.0
    overlap = len(q_tokens & n_tokens)
    union = len(q_tokens | n_tokens)
    return overlap / union if union else 0.0


async def search_activity_candidates(
    db: AsyncSession,
    snapshot_id: int,
    query_text: str,
    limit: int = 10,
) -> list[ActivityMatchCandidate]:
    dialect = db.bind.dialect.name if db.bind is not None else ""

    if dialect == "postgresql":
        rows = await db.execute(
            text(
                """
                SELECT activity_id, name, is_completed, similarity(name, :q) AS score
                FROM activities
                WHERE snapshot_id = :sid
                ORDER BY score DESC, activity_id ASC
                LIMIT :k
                """
            ),
            {"q": query_text, "sid": snapshot_id, "k": limit},
        )
        return [
            ActivityMatchCandidate(
                activity_id=row.activity_id,
                name=row.name,
                is_completed=bool(row.is_completed),
                sql_score=float(row.score or 0.0),
            )
            for row in rows
        ]

    # Fallback: score every activity in Python.
    result = await db.execute(select(Activity).where(Activity.snapshot_id == snapshot_id))
    activities = list(result.scalars().all())
    scored = [
        ActivityMatchCandidate(
            activity_id=a.activity_id,
            name=a.name,
            is_completed=a.is_completed,
            sql_score=_fallback_score(query_text, a.name),
        )
        for a in activities
    ]
    scored.sort(key=lambda c: (c.sql_score, c.activity_id), reverse=True)
    return scored[:limit]
