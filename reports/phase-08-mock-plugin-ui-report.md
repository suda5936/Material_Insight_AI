# Phase 8. Mock Plugin UI Report

## 1. 목표

Rhino를 실행하지 않아도 발표와 검토가 가능한 Mock Plugin UI를 구현한다.

이 UI는 실제 Rhino plugin의 대체물이 아니라, backend API와 agent workflow를 화면으로 검증하기 위한 데모 패널이다.

## 2. 작업 내용

### 2.1 정적 Mock Plugin UI 구현

`frontend/mock-plugin-ui`에 빌드 과정 없는 정적 UI를 추가했다.

구성 파일은 다음과 같다.

- `index.html`
- `styles.css`
- `app.js`
- `README.md`

### 2.2 화면 구성

설계 문서 `08-demo.md`의 화면 구성을 기준으로 다음 패널을 구현했다.

- 객체 목록
- 객체 정보 패널
- Review Payload preview
- AI 검토 결과 패널
- 출처 문서 표시 영역
- 사용자 액션 버튼
- 전체 모델 QA 결과 패널

### 2.3 Backend API 연결

Mock UI는 다음 API를 호출한다.

- `GET /health`
- `POST /api/v1/review-object`
- `POST /api/v1/review-actions`
- `POST /api/v1/scan-model`

기본 backend 주소는 다음과 같다.

```text
http://localhost:8000
```

### 2.4 CORS 설정 추가

정적 UI가 별도 localhost origin에서 backend를 호출할 수 있도록 CORS 설정을 추가했다.

수정 파일:

- `backend/app/core/config.py`
- `backend/app/main.py`
- `backend/.env.example`
- `backend/app/tests/test_config.py`

기본 허용 origin:

```text
http://localhost:5173
http://127.0.0.1:5173
http://localhost:8001
http://127.0.0.1:8001
```

## 3. 데모 흐름

1. Backend 실행
2. Mock UI 실행
3. `W-012` 객체 선택
4. `AI 검토` 실행
5. 누락 재료, 차음 검토, 근거 문서 확인
6. 수용, 수정 저장, 보류, 무시, 전문가 검토 액션 중 하나 저장
7. `전체 검사` 실행
8. 모델 QA 우선순위 목록 확인

## 4. 실행 방법

Backend:

```powershell
cd backend
uvicorn app.main:app --reload
```

Mock UI:

```powershell
cd frontend/mock-plugin-ui
python -m http.server 8001
```

브라우저:

```text
http://localhost:8001
```

## 5. 설계 문서 일치성 검토

### 일치한 점

- `08-demo.md`의 객체 정보, AI 검토 결과, 사용자 액션, 전체 모델 QA 화면을 모두 반영했다.
- `review-object`, `review-actions`, `scan-model` API를 실제 호출하는 흐름으로 구현했다.
- Rhino 객체 payload를 임의 변경하지 않고, 기존 backend `ReviewObjectRequest` 구조에 맞춘 데모 객체를 사용했다.
- 사용자 승인 없는 자동 Rhino 객체 수정은 수행하지 않고, action log 저장만 수행한다.
- Phase 7B까지의 RAG source 표시 흐름을 UI에서 확인할 수 있게 했다.

### 의도적으로 남긴 범위

- Rhino viewport overlay는 구현하지 않았다.
- 실제 Rhino object selection은 Phase 9 Rhino Plugin Skeleton에서 다룬다.
- 프론트엔드 빌드 도구는 도입하지 않았다. MVP 발표 안정성을 위해 정적 HTML/CSS/JS로 유지했다.

## 6. 검증 결과

정적 UI JavaScript 구문 검사는 통과했다.

```powershell
node --check frontend\mock-plugin-ui\app.js
```

현재 Codex 실행 세션에서는 Python 실행 파일을 사용할 수 없어 정적 서버와 backend 테스트를 직접 실행하지 못했다.

사용자 로컬 Python 3.12 환경에서는 다음 명령으로 확인하면 된다.

```powershell
cd backend
pytest app/tests/test_config.py
uvicorn app.main:app --reload
```

다른 터미널:

```powershell
cd frontend/mock-plugin-ui
python -m http.server 8001
```

## 7. 산출물

- `frontend/mock-plugin-ui/index.html`
- `frontend/mock-plugin-ui/styles.css`
- `frontend/mock-plugin-ui/app.js`
- `frontend/mock-plugin-ui/README.md`
- `backend/app/core/config.py`
- `backend/app/main.py`
- `backend/.env.example`
- `backend/app/tests/test_config.py`
- `backend/README.md`
- `README.md`
- `material_insight_explanation/docs/12-implementation-phase-roadmap.md`

## 8. 다음 단계

다음 phase는 `Phase 8B. pgvector RAG 전환`이다.

Phase 8B에서는 `data/processed/rag_chunks.jsonl`을 PostgreSQL/pgvector에 적재하고, 현재 Local Retrieval을 vector search 기반으로 교체 가능한 구조로 확장한다.
