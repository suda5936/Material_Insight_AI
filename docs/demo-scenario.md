# Demo Scenario

Material Insight AI MVP 발표와 시연을 위한 데모 순서다.

## 1. 데모 목표

단순 챗봇이 아니라 Rhino/CAD 객체를 중심으로 동작하는 Human-in-the-loop AI Agent임을 보여준다.

핵심 메시지:

- Rhino 객체에서 필요한 메타데이터만 추출한다.
- Rule Engine이 명확한 누락과 위험을 먼저 잡는다.
- Retrieval/RAG는 항상 실행되지만, 근거로 채택되는 sources는 threshold를 통과해야 한다.
- LLM 또는 fallback 추천은 Rule 결과를 덮어쓰지 않는다.
- 사용자의 수용, 수정, 보류, 무시, 전문가 검토 요청은 로그로 저장된다.

## 2. 사전 준비

Backend 실행:

```powershell
cd C:\Users\user\Documents\Codex\2026-07-08\c-users-user-desktop-material-insight\backend
python -m uvicorn app.main:app --reload
```

Mock UI 실행:

```powershell
cd C:\Users\user\Documents\Codex\2026-07-08\c-users-user-desktop-material-insight\frontend\mock-plugin-ui
python -m http.server 8001
```

Mock UI 주소:

```text
http://localhost:8001
```

Rhino plugin 빌드:

```powershell
cd C:\Users\user\Documents\Codex\2026-07-08\c-users-user-desktop-material-insight\plugin\RhinoMaterialInsight
dotnet build
```

Rhino plugin:

```text
plugin/RhinoMaterialInsight/bin/Debug/net7.0-windows/RhinoMaterialInsight.rhp
```

## 3. 시나리오 A. Mock Plugin UI

1. 브라우저에서 `http://localhost:8001` 접속
2. 객체 목록에서 `W-012` 선택
3. Review Payload 확인
4. `AI 검토` 클릭
5. 결과 확인

확인할 내용:

- `material_missing`
- `thickness_review_required`
- 관련 source 문서 `SPEC-INT-024`
- confidence와 required action

6. 메모 입력
7. `수정 저장` 또는 `전문가 검토` 클릭
8. `전체 검사` 클릭
9. 전체 모델 QA 우선순위 목록 확인

## 4. 시나리오 B. 실제 Rhino Plugin

1. Rhino 실행
2. `PlugInManager`로 `.rhp` 로드
3. `_Box`로 테스트 객체 생성
4. 객체 선택
5. `SetUserText`로 업무 속성 추가

예시:

```text
object_type=interior_wall
space_type=meeting_room
thickness_mm=75
review_status=pending
acoustic_required=true
```

6. 명령 실행

```text
MaterialInsightReview
```

7. 객체 선택 후 Enter
8. Rhino command line 확인

예상 출력:

```text
Material Insight object: ..., type=interior_wall, space=meeting_room, material=missing
Material Insight: sending review request to backend in background...
Material Insight: backend response received.
```

Backend 예상 로그:

```text
POST /api/v1/review-object HTTP/1.1" 200 OK
```

9. Mock UI로 돌아가 `Rhino 결과 불러오기` 클릭
10. Rhino에서 선택한 객체의 recommendation이 AI 검토 결과 패널에 표시되는지 확인

Mock UI는 4초마다 `GET /api/v1/latest-review`를 polling하므로, 수동 버튼을 누르지 않아도 최신 결과가 표시될 수 있다.

## 5. 시나리오 C. RAG/pgvector 설명

Phase 7B/8B는 발표에서 구조 설명 중심으로 다룬다.

1. `data/materials/material_catalog.yaml` 설명
2. `backend/scripts/build_rag_chunks.py` 설명
3. `data/processed/rag_chunks.jsonl` 설명
4. `backend/scripts/ingest_rag_chunks_pgvector.py` 설명
5. `RAG_RETRIEVER_PROVIDER=local/pgvector` 전환 구조 설명

핵심은 API contract를 바꾸지 않고 검색 구현만 교체할 수 있다는 점이다.

## 6. 실패/안전 시나리오

| 상황 | 기대 동작 |
|---|---|
| 관련 문서 없음 | `sources=[]`, 낮은 confidence, 근거 없음 disclaimer |
| LLM 실패 | Rule/fallback recommendation 반환 |
| 구조/내화/법규 위험 | `expert_review`로 전환 |
| Rhino UserText 없음 | `type=missing`, `space=missing`, 추가 입력 필요 |
| backend 미실행 | plugin 8초 timeout 후 오류 표시 |

## 7. 발표용 2분 흐름

1. Mock UI에서 `W-012` 선택
2. `AI 검토`로 Rule/RAG/Recommendation 결과 표시
3. sources와 disclaimer 설명
4. `전체 검사`로 QA 목록 표시
5. Rhino에서 `MaterialInsightReview` 실행해 실제 객체 기반 API 호출 확인
6. backend `POST /api/v1/review-object 200 OK` 로그 확인

## 8. 발표용 5분 흐름

1. 아키텍처 설명
2. Mock UI end-to-end 시연
3. Rhino plugin 실제 호출 시연
4. pgvector 전환 구조 설명
5. HITL/안전장치 설명
6. 설계-구현 매핑표로 구현 일치성 마무리
