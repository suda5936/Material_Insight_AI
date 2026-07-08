# Phase 8B. pgvector RAG 전환 Report

## 1. 목표

Phase 7B에서 만든 RAG chunk를 PostgreSQL/pgvector에 적재하고, 기존 Local Retrieval을 vector search 기반 retriever로 교체 가능한 구조를 만든다.

외부 API contract는 바꾸지 않는다. `/api/v1/review-object`는 그대로 사용하고, 내부 검색 provider만 설정으로 전환한다.

## 2. 작업 내용

### 2.1 Embedding provider 추가

`backend/app/services/embedding_client.py`를 추가했다.

MVP 기본 embedding provider는 `local_hash`다. 외부 API 없이 deterministic vector를 만들기 때문에 테스트와 데모가 안정적이다.

추후 OpenAI embedding 또는 사내 embedding model을 붙일 때는 같은 interface를 확장하면 된다.

### 2.2 pgvector retriever 추가

`backend/app/services/pgvector_retriever.py`를 추가했다.

역할은 다음과 같다.

- review object와 rule result로 query text 생성
- query embedding 생성
- PostgreSQL pgvector similarity search 실행
- score threshold를 통과한 문서만 sources로 채택
- DB 오류 또는 pgvector 미준비 시 Local Retrieval fallback 사용

### 2.3 pgvector ingest script 추가

`backend/scripts/ingest_rag_chunks_pgvector.py`를 추가했다.

이 스크립트는 다음 흐름으로 동작한다.

1. `data/processed/rag_chunks.jsonl`이 없으면 먼저 chunk builder 실행
2. PostgreSQL `vector` extension 활성화
3. `rag_chunks` table 생성
4. 기존 chunk 삭제 후 재적재
5. 각 chunk의 searchable text를 embedding으로 변환
6. `embedding vector(64)` 컬럼에 저장

### 2.4 설정 추가

`backend/app/core/config.py`와 `.env.example`에 다음 설정을 추가했다.

```text
RAG_RETRIEVER_PROVIDER=local
EMBEDDING_PROVIDER=local_hash
EMBEDDING_DIMENSIONS=64
PGVECTOR_MIN_RELEVANCE_SCORE=5.0
```

기본값은 `local`이다. PostgreSQL/pgvector를 사용할 때만 `RAG_RETRIEVER_PROVIDER=pgvector`로 전환한다.

### 2.5 Orchestrator 연결

`RecommendationOrchestrator`는 이제 설정에 따라 retriever를 선택한다.

- `local`: 기존 Local Retriever
- `pgvector`: pgvector retriever + Local Retriever fallback

Rule Engine, LLM, Review Action API는 변경하지 않았다.

### 2.6 테스트 추가

다음 테스트를 추가했다.

- `backend/app/tests/test_embedding_client.py`
- `backend/app/tests/test_pgvector_ingest.py`
- `backend/app/tests/test_pgvector_retriever.py`

테스트 범위:

- local hash embedding이 deterministic한가
- pgvector table SQL이 vector dimension과 metadata를 포함하는가
- insert SQL이 jsonb/vector cast를 수행하는가
- pgvector 검색 실패 시 Local Retrieval fallback이 동작하는가

## 3. 실행 방법

PostgreSQL/pgvector 사용 시 `.env`를 설정한다.

```powershell
DATABASE_URL=postgresql+psycopg://material_user:material_password@localhost:5432/material_insight
RAG_RETRIEVER_PROVIDER=pgvector
EMBEDDING_PROVIDER=local_hash
EMBEDDING_DIMENSIONS=64
PGVECTOR_MIN_RELEVANCE_SCORE=5.0
```

전처리와 적재:

```powershell
cd backend
python scripts/build_rag_chunks.py
python scripts/ingest_rag_chunks_pgvector.py
```

서버 실행:

```powershell
uvicorn app.main:app --reload
```

## 4. 설계 문서 일치성 검토

### 일치한 점

- `07-rag-hitl.md`의 “근거 기반 추천” 흐름을 유지했다.
- Retrieval은 항상 실행하고, sources 채택은 score threshold 기반으로 유지했다.
- `review-object` API contract는 변경하지 않았다.
- source, version, effective_date, status metadata를 pgvector table에 유지한다.
- PostgreSQL/pgvector 미준비 시 Local Retrieval fallback을 제공한다.
- LLM이 근거 없는 내용을 임의로 보강하지 않도록 기존 orchestrator 제약을 유지했다.

### 의도적으로 남긴 범위

- 실제 OpenAI embedding 호출은 구현하지 않았다.
- 운영용 migration tool은 도입하지 않았다.
- 대용량 PDF 파싱/OCR pipeline은 아직 포함하지 않았다.
- PostgreSQL 서버 연결 검증은 사용자 로컬 환경에서 수행해야 한다.

## 5. 검증 결과

현재 Codex 실행 세션에서는 Python 실행 파일을 사용할 수 없어 pytest와 PostgreSQL ingest를 직접 실행하지 못했다.

사용자 로컬 Python 3.12 환경에서는 다음 명령으로 구조 테스트를 실행하면 된다.

```powershell
cd backend
pytest app/tests/test_embedding_client.py app/tests/test_pgvector_ingest.py app/tests/test_pgvector_retriever.py
```

PostgreSQL 서버가 준비되어 있으면 다음 명령으로 실제 적재를 확인한다.

```powershell
python scripts/build_rag_chunks.py
python scripts/ingest_rag_chunks_pgvector.py
```

## 6. 산출물

- `backend/app/services/embedding_client.py`
- `backend/app/services/pgvector_retriever.py`
- `backend/scripts/ingest_rag_chunks_pgvector.py`
- `backend/app/tests/test_embedding_client.py`
- `backend/app/tests/test_pgvector_ingest.py`
- `backend/app/tests/test_pgvector_retriever.py`
- `backend/app/core/config.py`
- `backend/app/services/recommendation_orchestrator.py`
- `backend/.env.example`
- `backend/README.md`
- `README.md`

## 7. 다음 단계

다음 phase는 `Phase 9. Rhino Plugin Skeleton`이다.

Phase 9에서는 실제 Rhino plugin의 C# 구조를 만들고, Rhino 객체 선택, 속성 추출, backend API 호출, 결과 표시의 책임 경계를 코드 형태로 제시한다.
