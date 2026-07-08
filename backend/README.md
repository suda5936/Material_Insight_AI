# Material Insight AI Backend

FastAPI 기반 Agent Backend다. Rhino Plugin 또는 Mock Plugin UI에서 전달한 객체 메타데이터를 검증하고, 이후 phase에서 Rule Engine, Retrieval/RAG, LLM 추천, Review Logging을 연결한다.

## 현재 범위

Phase 1에서는 다음만 구현한다.

- FastAPI app skeleton
- `/health` API
- Pydantic schema
- 샘플 review-object request
- schema validation script

Rule Engine, RAG, LLM, DB 저장은 이후 phase에서 구현한다.

## 실행 준비

권장 Python 버전은 3.12다.

```powershell
cd backend
py -3.12 -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

`pyproject.toml`도 동일한 런타임 기준을 유지한다. editable install 방식이 필요하면 다음 명령을 사용할 수 있다.

```powershell
python -m pip install -e ".[dev]"
```

## 서버 실행

```powershell
uvicorn app.main:app --reload
```

## 기본 검증

```powershell
python scripts/validate_sample_request.py
python scripts/run_rule_engine_sample.py
python scripts/run_local_retrieval_sample.py
python scripts/build_rag_chunks.py
pytest app/tests/test_recommendation_orchestrator.py app/tests/test_review_api.py
pytest app/tests/test_llm_client.py
pytest app/tests/test_review_logger.py app/tests/test_review_actions_api.py
pytest app/tests/test_model_scanner.py app/tests/test_scan_api.py
pytest app/tests/test_rag_chunk_builder.py
pytest app/tests/test_embedding_client.py app/tests/test_pgvector_ingest.py app/tests/test_pgvector_retriever.py
pytest app/tests/test_review_object_contract.py app/tests/test_review_api.py
pytest
```

## Phase 2 Rule Engine 검증

Rule Engine은 루트 `data/rules/material_insight_rules.yaml`을 읽고, 루트 `data/sample_objects/*.json` 샘플 객체를 평가한다.

```powershell
python scripts/run_rule_engine_sample.py
pytest app/tests/test_rule_engine.py
```

`W-012` 샘플 객체는 최소한 다음 issue를 반환해야 한다.

```text
material_missing
thickness_review_required
```

## Phase 3A Local Retrieval 검증

Local Retrieval은 루트 `data/documents/document_metadata.yaml`을 읽고, 샘플 문서를 section 단위로 검색한다. Retrieval은 항상 실행하되, recommendation prompt에 포함할 sources는 relevance score threshold를 통과한 결과만 채택한다.

```powershell
python scripts/run_local_retrieval_sample.py
pytest app/tests/test_local_retriever.py
```

`W-012` 샘플 객체는 threshold를 통과한 상위 검색 결과로 `SPEC-INT-024`를 반환해야 한다. threshold를 통과한 문서가 없으면 “근거 없음”으로 처리한다.

## Phase 3B PostgreSQL 저장 구조 검증

DB 연결은 `DATABASE_URL` 환경변수로 설정한다. PostgreSQL을 사용할 경우 `.env`에 다음 형식으로 설정한다.

```powershell
DATABASE_URL=postgresql+psycopg://material_user:material_password@localhost:5432/material_insight
```

`DATABASE_URL`이 비어 있으면 개발용 SQLite 파일인 `dev_material_insight.db`를 사용한다.

```powershell
python scripts/check_db.py
python scripts/init_db.py
python scripts/seed_document_metadata.py
pytest app/tests/test_db_schema.py
```

## Phase 4 Review Object API 검증

`/api/v1/review-object`는 Rule Engine을 먼저 실행하고, Local Retrieval은 항상 실행한다. 검색 후보 중 relevance score threshold를 통과한 문서만 `sources`로 채택하며, 통과한 문서가 없으면 “근거 없음” 상태로 fallback recommendation을 반환한다.

```powershell
pytest app/tests/test_recommendation_orchestrator.py app/tests/test_review_api.py
```

서버 실행 후에는 다음 API를 호출할 수 있다.

```powershell
uvicorn app.main:app --reload
```

```text
POST /api/v1/review-object
```

## Phase 5 Multi-Provider LLM 검증

LLM provider는 `LLM_PROVIDER`로 선택한다. 기본값은 `mock`이며, OpenAI API는 `OPENAI_API_KEY`와 `OPENAI_MODEL`만 사용한다. vLLM은 OpenAI-compatible local server URL과 사용 가능한 모델명 `qwen-27b` 또는 `gemma-4b`를 사용한다.

```powershell
pytest app/tests/test_llm_client.py app/tests/test_recommendation_orchestrator.py app/tests/test_review_api.py
```

실제 OpenAI 호출 설정:

```powershell
LLM_PROVIDER=openai
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-5.5
```

로컬 vLLM 호출 설정:

```powershell
LLM_PROVIDER=vllm
VLLM_BASE_URL=http://localhost:8000/v1
VLLM_MODEL=qwen-27b
```

## Phase 6 Review Action Logging 검증

사용자의 수용, 수정, 보류, 무시, 전문가 검토 요청은 `/api/v1/review-actions`로 저장한다. 이 API는 Rhino 객체를 자동 수정하지 않고, 사용자의 결정과 수정값, 사유, 출처를 로그로 남긴다.

```powershell
pytest app/tests/test_review_logger.py app/tests/test_review_actions_api.py
```

```text
POST /api/v1/review-actions
```

## Phase 7 Scan Model API 검증

여러 객체를 한 번에 검사하려면 `/api/v1/scan-model`을 호출한다. 이 API는 Rule Engine을 객체별로 실행하고, required action, severity, issue 수 기준으로 우선순위 목록을 반환한다.

```powershell
pytest app/tests/test_model_scanner.py app/tests/test_scan_api.py
```

```text
POST /api/v1/scan-model
```

## Phase 7B Material Knowledge Preprocessing 검증

RAG/vector DB에 넣을 문서와 재료 카탈로그 chunk는 같은 JSONL schema로 전처리한다. 이 단계의 출력은 추후 pgvector 적재 입력으로 사용한다.

```powershell
python scripts/build_rag_chunks.py
pytest app/tests/test_rag_chunk_builder.py
```

```text
data/processed/rag_chunks.jsonl
```

## Phase 8 Mock Plugin UI 실행

Mock Plugin UI는 Rhino 없이 backend API 흐름을 시연하는 정적 화면이다. Backend를 먼저 실행한 뒤 UI를 별도 정적 서버로 띄운다.

```powershell
uvicorn app.main:app --reload
```

다른 터미널에서 실행한다.

```powershell
cd ..\frontend\mock-plugin-ui
python -m http.server 8001
```

브라우저에서 `http://localhost:8001`을 열고 Backend 주소가 `http://localhost:8000`인지 확인한다.

Mock UI의 기본 origin은 `.env.example`의 `CORS_ALLOW_ORIGINS`에 포함되어 있다.

## Phase 8B pgvector RAG 전환 검증

기본 검색은 `RAG_RETRIEVER_PROVIDER=local`로 유지한다. PostgreSQL/pgvector를 사용할 때만 `.env`에서 다음 값을 설정한다.

```powershell
DATABASE_URL=postgresql+psycopg://material_user:material_password@localhost:5432/material_insight
RAG_RETRIEVER_PROVIDER=pgvector
EMBEDDING_PROVIDER=local_hash
EMBEDDING_DIMENSIONS=64
PGVECTOR_MIN_RELEVANCE_SCORE=5.0
```

전처리 chunk를 만들고 pgvector에 적재한다.

```powershell
python scripts/build_rag_chunks.py
python scripts/ingest_rag_chunks_pgvector.py
```

PostgreSQL 서버 없이 단위 구조만 검증하려면 다음 테스트를 실행한다.

```powershell
pytest app/tests/test_embedding_client.py app/tests/test_pgvector_ingest.py app/tests/test_pgvector_retriever.py
```

`/api/v1/review-object`의 외부 contract는 바뀌지 않는다. 검색 provider만 local에서 pgvector로 교체된다.

## Phase 9B Rhino Payload Contract 검증

Rhino Plugin skeleton이 생성할 payload와 backend `ReviewObjectRequest` schema가 맞는지 검증한다.

Canonical sample:

```text
plugin/RhinoMaterialInsight/Samples/review_object_payload.json
backend/data/rhino_plugin_review_object_payload.json
docs/rhino-payload-contract.md
```

검증:

```powershell
pytest app/tests/test_review_object_contract.py app/tests/test_review_api.py
```
