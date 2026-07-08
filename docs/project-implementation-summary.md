# Material Insight AI 구현 요약

이 문서는 지금까지 구현한 Material Insight AI MVP의 전체 진행 상황, 실행 방법, 테스트 방법, Rhino 연동 상태, 남은 확인 사항을 정리한다.

## 1. 프로젝트 목표

Material Insight AI는 Rhino/CAD 객체의 재료, 두께, 성능 검토를 지원하는 Human-in-the-loop AI Agent MVP다.

핵심 목표:

- Rhino 또는 Mock UI에서 객체 선택
- 객체 메타데이터를 backend `review-object` payload로 변환
- Rule Engine으로 누락/위험 탐지
- Retrieval/RAG로 근거 문서 검색
- LLM 또는 fallback recommendation 생성
- 사용자 수용/수정/보류/무시/전문가 검토 요청 저장
- 실제 Rhino plugin과 backend API 연결 확인

## 2. 완료된 Phase

| Phase | 내용 | 상태 |
|---:|---|---|
| 0 | 프로젝트 구조와 report 기준 생성 | 완료 |
| 1 | FastAPI backend skeleton과 Pydantic schema | 완료 |
| 2 | 샘플 객체와 YAML Rule Engine | 완료 |
| 3A | 샘플 문서와 Local Retrieval | 완료 |
| 3B | PostgreSQL 저장 구조 | 완료 |
| 4 | `/api/v1/review-object` end-to-end API | 완료 |
| 5 | OpenAI/vLLM/mock LLM provider layer | 완료 |
| 6 | `/api/v1/review-actions` HITL 로그 저장 | 완료 |
| 7 | `/api/v1/scan-model` 전체 모델 QA API | 완료 |
| 7B | 재료 카탈로그와 RAG chunk 전처리 | 완료 |
| 8 | Mock Plugin UI | 완료 |
| 8B | pgvector RAG 전환 구조 | 완료 |
| 9 | Rhino Plugin Skeleton | 완료 |
| 9B | Rhino payload contract test | 완료 |
| 10 | 통합 테스트와 발표용 데모 문서 | 완료 |

## 3. 주요 구현 파일

### Backend

```text
backend/app/main.py
backend/app/api/routes_review.py
backend/app/api/routes_actions.py
backend/app/api/routes_scan.py
backend/app/models/object.py
backend/app/models/recommendation.py
backend/app/models/review_action.py
backend/app/models/scan.py
backend/app/services/rule_engine.py
backend/app/services/local_retriever.py
backend/app/services/recommendation_orchestrator.py
backend/app/services/llm_client.py
backend/app/services/review_logger.py
backend/app/services/model_scanner.py
backend/app/services/embedding_client.py
backend/app/services/pgvector_retriever.py
```

### Data

```text
data/rules/material_insight_rules.yaml
data/sample_objects/*.json
data/documents/**/*
data/materials/material_catalog.yaml
data/materials/performance_tags.yaml
data/processed/rag_chunks.jsonl
```

### Scripts

```text
backend/scripts/run_rule_engine_sample.py
backend/scripts/run_local_retrieval_sample.py
backend/scripts/build_rag_chunks.py
backend/scripts/ingest_rag_chunks_pgvector.py
```

### Mock UI

```text
frontend/mock-plugin-ui/index.html
frontend/mock-plugin-ui/styles.css
frontend/mock-plugin-ui/app.js
```

### Rhino Plugin

```text
plugin/RhinoMaterialInsight/RhinoMaterialInsight.csproj
plugin/RhinoMaterialInsight/RhinoMaterialInsightPlugin.cs
plugin/RhinoMaterialInsight/Commands/MaterialInsightReviewCommand.cs
plugin/RhinoMaterialInsight/Models/MaterialInsightModels.cs
plugin/RhinoMaterialInsight/Services/MaterialInsightObjectInspector.cs
plugin/RhinoMaterialInsight/Services/MaterialInsightApiClient.cs
plugin/RhinoMaterialInsight/Services/MaterialInsightObjectUpdater.cs
plugin/RhinoMaterialInsight/Panels/MaterialInsightReviewPanel.cs
plugin/RhinoMaterialInsight/Samples/review_object_payload.json
```

## 4. 구현된 API

| API | 설명 |
|---|---|
| `GET /health` | backend 상태 확인 |
| `POST /api/v1/review-object` | 객체 하나 검토 |
| `GET /api/v1/latest-review` | 가장 최근 review-object 결과 조회 |
| `POST /api/v1/review-actions` | 사용자 판단 저장 |
| `POST /api/v1/scan-model` | 여러 객체 일괄 QA |

## 5. 핵심 처리 흐름

```text
Rhino 또는 Mock UI 객체 입력
-> ReviewObjectRequest validation
-> Rule Engine 실행
-> Retrieval/RAG 항상 실행
-> relevance score threshold 통과 sources만 채택
-> LLM 또는 fallback recommendation 생성
-> 결과 표시
-> 사용자 action 저장
```

## 6. Rhino Plugin 실제 연동 상태

사용자 로컬 환경에서 다음이 확인되었다.

- `.NET SDK` 설치
- `dotnet restore` 성공
- `dotnet build` 성공
- Rhino에서 `.rhp` plugin 로드
- `MaterialInsightReview` 명령 실행
- Rhino 객체 선택
- backend `/api/v1/review-object` 호출 성공

확인된 backend 로그:

```text
POST /api/v1/review-object HTTP/1.1" 200 OK
```

초기에는 backend API 통신 이후 Rhino가 먹통처럼 보이는 문제가 있었고, 이를 해결하기 위해 plugin의 backend 호출을 background async 방식으로 변경했다.

현재 예상 Rhino command line:

```text
Material Insight object: ..., type=interior_wall, space=meeting_room, material=missing
Material Insight: sending review request to backend in background...
Material Insight: backend response received.
```

## 7. Rhino 결과를 Frontend로 표시하는 구조

전체 과정 테스트를 위해 backend에 최신 review 결과 조회 API를 추가했다.

```text
GET /api/v1/latest-review
```

흐름:

```text
Rhino에서 객체 선택
-> Rhino Plugin이 /api/v1/review-object 호출
-> Backend가 recommendation 생성
-> Backend가 최신 review 결과를 메모리에 저장
-> Mock UI가 /api/v1/latest-review polling
-> Mock UI AI 검토 결과 패널에 표시
```

Mock UI에는 다음 버튼이 추가되었다.

```text
Rhino 결과 불러오기
```

또한 4초마다 자동 polling을 수행한다.

## 8. 실행 방법

### Backend 실행

```powershell
cd C:\Users\user\Documents\Codex\2026-07-08\c-users-user-desktop-material-insight\backend
python -m uvicorn app.main:app --reload
```

### Mock UI 실행

```powershell
cd C:\Users\user\Documents\Codex\2026-07-08\c-users-user-desktop-material-insight\frontend\mock-plugin-ui
python -m http.server 8001
```

브라우저:

```text
http://localhost:8001
```

### Rhino Plugin 빌드

```powershell
cd C:\Users\user\Documents\Codex\2026-07-08\c-users-user-desktop-material-insight\plugin\RhinoMaterialInsight
dotnet build
```

Rhino에서 로드할 파일:

```text
plugin/RhinoMaterialInsight/bin/Debug/net7.0-windows/RhinoMaterialInsight.rhp
```

## 9. 전체 과정 테스트 방법

1. Backend 실행
2. Mock UI 실행
3. Rhino 실행
4. `PlugInManager`로 `.rhp` 로드
5. Rhino에서 Box 생성
6. 객체에 UserText 추가

예시:

```text
object_type=interior_wall
space_type=meeting_room
thickness_mm=75
review_status=pending
acoustic_required=true
```

7. Rhino 명령 실행

```text
MaterialInsightReview
```

8. backend 로그 확인

```text
POST /api/v1/review-object HTTP/1.1" 200 OK
```

9. Mock UI에서 `Rhino 결과 불러오기` 클릭
10. AI 검토 결과 패널에 recommendation 표시 확인

직접 확인 URL:

```text
http://localhost:8000/api/v1/latest-review
```

Rhino 검토 이후 이 URL이 `null`이 아니라 recommendation JSON을 반환해야 한다.

## 10. 테스트 명령

### Backend 전체 테스트

```powershell
cd backend
python -m pytest
```

### 핵심 테스트

```powershell
python -m pytest app/tests/test_recommendation_orchestrator.py app/tests/test_review_api.py
python -m pytest app/tests/test_review_actions_api.py app/tests/test_scan_api.py
python -m pytest app/tests/test_review_object_contract.py
```

### Mock UI JS 검사

```powershell
node --check frontend\mock-plugin-ui\app.js
```

### Rhino Plugin 빌드

```powershell
cd plugin/RhinoMaterialInsight
dotnet build
```

## 11. 현재 확인된 사항

| 항목 | 상태 |
|---|---|
| Rule Engine | 구현 및 테스트 가능 |
| Local Retrieval | 구현 및 테스트 가능 |
| Review Object API | 구현 및 실제 Rhino 호출 성공 |
| Review Action API | 구현 |
| Scan Model API | 구현 |
| LLM Provider Layer | OpenAI/vLLM/mock 구조 구현 |
| Material Knowledge Preprocessing | 구현 |
| pgvector 전환 구조 | 구현 |
| Mock UI | 구현 |
| Rhino Plugin | 빌드 및 실제 API 호출 성공 |
| Rhino -> Frontend 최신 결과 표시 | latest-review bridge 구현 |

## 12. 주의 사항

- Rhino plugin은 현재 command line 기반 결과 표시 placeholder다.
- 실제 dock panel UI는 아직 구현하지 않았다.
- Rhino 객체 업데이트는 사용자 승인 이후에만 수행해야 한다.
- AI 추천은 자동으로 Rhino 객체에 반영하지 않는다.
- `latest-review`는 MVP demo용 메모리 저장 방식이다. 서버 재시작 시 초기화된다.
- 여러 사용자가 동시에 쓰는 운영 환경에서는 DB/session 기반 latest review 저장으로 바꿔야 한다.
- pgvector는 구조와 ingest script까지 구현했으며 실제 운영 데이터 검증은 별도 단계다.

## 13. 최종 데모 권장 구성

가장 안정적인 발표 순서:

1. Mock UI에서 `W-012` 선택
2. `AI 검토` 클릭
3. Rule/RAG/Recommendation 결과와 sources 표시
4. `전체 검사`로 모델 QA 표시
5. Rhino에서 `MaterialInsightReview` 실행
6. backend `POST /api/v1/review-object 200 OK` 확인
7. Mock UI에서 `Rhino 결과 불러오기` 클릭
8. Rhino 객체 기반 recommendation이 frontend에 표시되는지 확인

## 14. 관련 문서

```text
README.md
docs/demo-scenario.md
docs/design-implementation-mapping.md
docs/final-validation-checklist.md
docs/rhino-plugin-runbook.md
docs/rhino-payload-contract.md
reports/phase-10-integration-demo-report.md
```
