# Final Validation Checklist

Phase 10 최종 검증 체크리스트다.

## 1. Backend

```powershell
cd backend
python scripts/validate_sample_request.py
python scripts/run_rule_engine_sample.py
python scripts/run_local_retrieval_sample.py
python scripts/build_rag_chunks.py
pytest
```

개별 핵심 테스트:

```powershell
pytest app/tests/test_recommendation_orchestrator.py app/tests/test_review_api.py
pytest app/tests/test_review_actions_api.py app/tests/test_scan_api.py
pytest app/tests/test_review_object_contract.py
```

## 2. Mock Plugin UI

```powershell
cd frontend/mock-plugin-ui
python -m http.server 8001
```

확인:

- 객체 선택 가능
- `AI 검토` 호출 가능
- sources 표시
- review action 저장 가능
- 전체 모델 QA 표시 가능

## 3. Rhino Plugin

```powershell
cd plugin/RhinoMaterialInsight
dotnet build
```

확인:

- `.rhp` 생성
- Rhino `PlugInManager`에서 로드 가능
- `MaterialInsightReview` 명령 실행 가능
- 객체 선택 가능
- backend `POST /api/v1/review-object 200 OK` 확인
- Mock UI `Rhino 결과 불러오기`로 최신 recommendation 표시 확인
- Rhino UI가 API 통신 중 먹통이 되지 않음

## 4. pgvector

PostgreSQL/pgvector 사용 시:

```powershell
cd backend
python scripts/build_rag_chunks.py
python scripts/ingest_rag_chunks_pgvector.py
```

환경 변수:

```text
DATABASE_URL=postgresql+psycopg://...
RAG_RETRIEVER_PROVIDER=pgvector
EMBEDDING_PROVIDER=local_hash
EMBEDDING_DIMENSIONS=64
PGVECTOR_MIN_RELEVANCE_SCORE=5.0
```

## 5. 제출 전 확인

- `README.md` 최신 상태
- `docs/demo-scenario.md` 존재
- `docs/design-implementation-mapping.md` 존재
- `docs/rhino-plugin-runbook.md` 존재
- phase별 report 존재
- 실제 Rhino API 호출 성공 내용 report 반영
