# Phase 04 Report: Review Object API End-to-End

## 1. Phase 목표

Phase 4의 목표는 객체 하나를 입력하면 Rule Engine, Retrieval, threshold 기반 sources 채택, fallback recommendation까지 한 번에 연결되는 `/api/v1/review-object` API를 구현하는 것이다.

이번 phase에서는 LLM provider를 아직 붙이지 않고, Phase 3A에서 정리한 원칙인 “retrieval은 항상 실행, augmentation은 조건부 채택”을 API 응답 흐름에 반영했다.

## 2. 수행 작업

- `RecommendationOrchestrator`를 추가해 Rule Engine과 Local Retrieval을 연결했다.
- Rule Engine을 먼저 실행하고, 그 결과와 객체 정보를 기반으로 Local Retrieval을 항상 실행하도록 구성했다.
- `search_relevant()`를 사용해 threshold를 통과한 문서만 `sources`로 채택했다.
- threshold를 통과한 문서가 없으면 `sources=[]`, 낮은 confidence, “근거 없음” disclaimer를 반환하도록 했다.
- LLM이 없는 Phase 4 범위에 맞춰 fallback recommendation을 생성했다.
- `/api/v1/review-object` FastAPI route를 추가했다.
- `RecommendationResult`에 `recommendation_id`, `object_id`를 추가해 구현 가이드의 응답 형태와 맞췄다.
- Orchestrator 단위 테스트와 API 테스트를 추가했다.
- README에 Phase 4 검증 방법을 추가했다.

## 3. 생성/수정 파일

| 파일 | 설명 |
|---|---|
| `backend/app/services/recommendation_orchestrator.py` | Rule Engine, Retrieval, fallback recommendation 연결 |
| `backend/app/api/routes_review.py` | `POST /api/v1/review-object` route |
| `backend/app/main.py` | review router 등록 |
| `backend/app/models/recommendation.py` | `recommendation_id`, `object_id` 응답 필드 추가 |
| `backend/app/tests/test_recommendation_orchestrator.py` | orchestrator end-to-end 단위 테스트 |
| `backend/app/tests/test_review_api.py` | FastAPI review-object API 테스트 |
| `backend/README.md` | Phase 4 실행 및 검증 방법 추가 |
| `README.md` | 완료 phase와 다음 phase 업데이트 |
| `reports/phase-04-review-object-api-report.md` | Phase 4 작업 보고서 |

## 4. 검증 결과

### 작성한 테스트

```powershell
pytest app/tests/test_recommendation_orchestrator.py app/tests/test_review_api.py
```

테스트 기대값:

- `W-012` 샘플 request는 `review_required`를 반환한다.
- `material_missing`, `thickness_review_required`가 detected issue에 포함된다.
- threshold를 통과한 `SPEC-INT-024`가 `sources`에 포함된다.
- 객체 유형이 없어 검색 근거가 채택되지 않는 경우 `sources=[]`, 낮은 confidence, “No relevant document” disclaimer를 반환한다.

### 현재 환경에서의 실행 상태

Codex 셸에서는 `backend/.venv/Scripts/python.exe`와 `C:\Users\user\AppData\Local\Programs\Python\Python312\python.exe`가 존재하는 것을 확인했다. 다만 이 Codex 프로세스에서는 해당 Python 실행 파일 접근이 거부되어 pytest를 직접 실행하지 못했다.

확인된 오류:

```text
Unable to create process using '"C:\Users\user\AppData\Local\Programs\Python\Python312\python.exe" ...'
Access is denied when executing `C:\Users\user\AppData\Local\Programs\Python\Python312\python.exe`.
```

따라서 이 turn에서는 테스트 파일 작성과 코드 경로 검토까지 수행했고, 실제 pytest 실행은 사용자 Python 3.12 venv에서 재실행해야 한다.

사용자 환경에서 실행할 명령:

```powershell
cd C:\Users\user\Documents\Codex\2026-07-08\c-users-user-desktop-material-insight\backend
python -m pytest app/tests/test_recommendation_orchestrator.py app/tests/test_review_api.py
```

## 5. 설계 문서와의 일치 여부

| 설계 문서 | 요구 사항 | 구현 반영 |
|---|---|---|
| `material_insight_implementation_guide.md` Step 5 | 객체 입력에서 최종 추천 결과까지 흐름 연결 | `RecommendationOrchestrator.review_object()` 구현 |
| `material_insight_implementation_guide.md` Step 5 | 객체 validation, rule check, document search, response 반환 | FastAPI route + Pydantic request/response 연결 |
| `material_insight_implementation_guide.md` 8.4 | Retrieval은 항상 실행 | Orchestrator에서 Rule Engine 이후 항상 `search_relevant()` 호출 |
| `material_insight_implementation_guide.md` 8.4 | sources는 relevance threshold 기반 채택 | `LocalRetriever.search_relevant()` 사용 |
| `material_insight_implementation_guide.md` 9.4 | 근거 문서가 없을 때 확정 추천 생성 금지 | `sources=[]`, 낮은 confidence, disclaimer 반환 |
| `docs/11-processing-flow-diagram.md` | Rule Engine -> Retrieval always -> threshold -> prompt/result | 코드 흐름을 동일하게 구성 |
| `docs/12-implementation-phase-roadmap.md` Phase 4 | `/api/v1/review-object` 구현 | `routes_review.py` 추가 |

### 일치한 부분

- Rule Engine 결과를 LLM/fallback이 삭제하거나 완화하지 않는다.
- Retrieval 실행 여부가 아니라 sources 채택 여부에 threshold를 적용한다.
- 관련 근거가 없으면 근거 기반 추천처럼 보이지 않도록 confidence와 disclaimer를 낮춘다.
- Rhino 객체를 자동 수정하지 않고, response만 반환하는 Human-in-the-loop 구조를 유지한다.

### 의도적으로 아직 구현하지 않은 부분

- 실제 LLM provider 호출은 Phase 5 범위로 남겼다.
- PostgreSQL에 recommendation을 저장하는 처리는 아직 연결하지 않았다.
- object normalizer는 별도 서비스로 분리하지 않고 Pydantic validation과 기존 schema를 우선 사용했다.
- Review Action Logging은 Phase 6에서 구현한다.

## 6. 남은 이슈

- 사용자 Python 3.12 venv에서 Phase 4 테스트를 실제 실행해야 한다.
- fallback recommendation의 문장은 MVP 안전성을 우선해 보수적으로 작성되어 있다.
- 다음 phase에서 LLM provider를 붙일 때도 Rule Engine 결과와 threshold 미통과 상태를 prompt에서 강하게 고정해야 한다.

## 7. 다음 Phase 제안

다음 phase는 **Phase 5. Multi-Provider LLM Recommendation**이다.

Phase 5에서 진행할 작업:

1. LLM provider interface 정의
2. OpenAI provider 구현
3. vLLM provider 확장 지점 마련
4. mock provider 유지
5. system prompt와 user prompt template 작성
6. JSON schema validation 및 LLM 실패 fallback 연결
7. “sources가 없으면 근거 기반 추천 금지” 규칙을 prompt와 코드 양쪽에 반영
