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
pytest app/tests/test_recommendation_orchestrator.py app/tests/test_review_api.py
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
