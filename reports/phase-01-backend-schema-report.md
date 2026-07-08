# Phase 01 Report: 백엔드 Skeleton + 데이터 스키마

## 1. Phase 목표

Phase 1의 목표는 Material Insight AI Agent Backend의 최소 실행 구조와 데이터 계약을 코드로 고정하는 것이다.

이번 phase에서는 FastAPI app skeleton, `/health` API, Pydantic schema, 샘플 `review-object` request, 기본 테스트 파일을 작성했다. Rule Engine, RAG, LLM, DB 연결은 아직 구현하지 않았다.

사용자 요청에 따라 Python 기준 버전은 **Python 3.12**로 고정했다.

## 2. 수행 작업

- `backend/pyproject.toml`을 작성했다.
- `backend/requirements.txt`를 작성했다.
- Python 요구 버전을 `>=3.12`로 설정했다.
- FastAPI app entrypoint를 작성했다.
- `/health` API route를 작성했다.
- 공통 Pydantic base model을 작성했다.
- 구현 가이드의 핵심 schema를 Pydantic 모델로 작성했다.
  - `ProjectContext`
  - `GeometrySummary`
  - `DesignObjectInput`
  - `ReviewObjectRequest`
  - `RuleResult`
  - `RetrievedDocument`
  - `RecommendationResult`
  - `ReviewActionRequest`
- `W-012` 회의실 벽체 샘플 요청 JSON을 작성했다.
- 샘플 요청 validation script를 작성했다.
- `/health`와 schema validation 테스트 파일을 작성했다.
- Python 캐시와 가상환경 파일을 추적하지 않도록 `.gitignore`를 추가했다.

## 3. 생성/수정 파일

| 파일 | 설명 |
|---|---|
| `.gitignore` | Python cache, 가상환경, env 파일 ignore 설정 |
| `backend/README.md` | 백엔드 실행 방법과 Phase 1 범위 정리 |
| `backend/pyproject.toml` | Python 3.12 기반 FastAPI/Pydantic 프로젝트 설정 |
| `backend/requirements.txt` | venv에서 설치할 runtime/test package 목록 |
| `backend/app/__init__.py` | backend package 선언 |
| `backend/app/main.py` | FastAPI app 생성 및 router 등록 |
| `backend/app/api/__init__.py` | API package 선언 |
| `backend/app/api/routes_health.py` | `/health` API 구현 |
| `backend/app/models/__init__.py` | 주요 schema export |
| `backend/app/models/common.py` | 공통 APIModel 및 HealthResponse |
| `backend/app/models/object.py` | Project/Object/Geometry/ReviewObjectRequest schema |
| `backend/app/models/rule.py` | RuleResult schema |
| `backend/app/models/document.py` | RetrievedDocument schema |
| `backend/app/models/recommendation.py` | RecommendationResult schema |
| `backend/app/models/review_action.py` | ReviewActionRequest schema |
| `backend/data/sample_review_object_request.json` | `W-012` 샘플 객체 검토 요청 |
| `backend/scripts/validate_sample_request.py` | 샘플 요청 validation script |
| `backend/app/tests/test_health.py` | `/health` API 테스트 |
| `backend/app/tests/test_schema.py` | 샘플 요청 schema validation 테스트 |
| `reports/phase-01-backend-schema-report.md` | Phase 1 작업 보고서 |

## 4. 검증 결과

현재 환경에서는 `python` 명령이 없고, `py` 런처로 확인되는 Python은 3.7.8이다. 또한 FastAPI와 Pydantic이 설치되어 있지 않다.

따라서 이번 phase에서 수행한 검증은 다음과 같다.

### 수행 완료

| 검증 | 결과 |
|---|---|
| Python source syntax compile | 통과 |
| `backend/pyproject.toml` Python 요구 버전 확인 | `>=3.12` 확인 |
| 샘플 JSON 구조 확인 | `object_id=W-012`, `object_type=interior_wall`, `space_type=meeting_room`, `thickness_mm=75` 확인 |
| 설계 문서의 schema 이름과 구현 파일 대조 | 일치 |

실행한 검증 명령:

```powershell
py -m py_compile backend\app\main.py backend\app\api\routes_health.py backend\app\models\__init__.py backend\app\models\common.py backend\app\models\object.py backend\app\models\rule.py backend\app\models\document.py backend\app\models\recommendation.py backend\app\models\review_action.py backend\scripts\validate_sample_request.py
```

### Python 3.12 환경에서 추가 실행 필요

아래 검증은 Python 3.12와 의존성 설치 후 실행해야 한다.

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python scripts/validate_sample_request.py
pytest
uvicorn app.main:app --reload
```

그 후 브라우저 또는 API client에서 다음 endpoint를 확인한다.

```text
GET /health
```

예상 응답:

```json
{
  "status": "ok",
  "service": "material-insight-backend"
}
```

## 5. 설계 문서와의 일치 여부

Phase 1 구현은 다음 설계 문서와 대조했다.

| 설계 문서 | 요구 사항 | 구현 반영 |
|---|---|---|
| `material_insight_implementation_guide.md` Step 1 | FastAPI 프로젝트 생성, health check API | `backend/app/main.py`, `routes_health.py` 구현 |
| `material_insight_implementation_guide.md` Step 2 | Pydantic schema 작성 | `backend/app/models/*.py` 구현 |
| `material_insight_implementation_guide.md` 6장 | 핵심 데이터 모델 정의 | 모델명과 주요 필드 반영 |
| `material_insight_implementation_guide.md` 10장 | `/api/v1/review-object` request 구조 | `ReviewObjectRequest`와 샘플 JSON으로 입력 구조 고정 |
| `12-implementation-phase-roadmap.md` Phase 1 | FastAPI skeleton + 데이터 스키마 | Phase 1 목표와 일치 |

### 일치한 부분

- `DesignObjectInput`에 객체 ID, 타입, 레이어, 이름, 재료, 두께, 공간 용도, 검토 상태, geometry, user attributes를 포함했다.
- `ProjectContext`에 프로젝트 ID, 유형, 설계 단계, 건물 용도, 지역, 우선순위를 포함했다.
- `RuleResult`에 severity, issue code, message, field, RAG 필요 여부, 전문가 검토 필요 여부를 포함했다.
- `RetrievedDocument`에 document ID, title, section, chunk, type, version, status, source, score를 포함했다.
- `RecommendationResult`에 status, severity, summary, issues, material candidates, thickness guidance, notes, action, confidence, sources, disclaimers를 포함했다.
- `ReviewActionRequest`에 recommendation ID, user ID, action, edited values, reason을 포함했다.
- `W-012` 샘플 객체는 구현 가이드의 필수 데모 입력과 일치한다.

### 의도적으로 아직 구현하지 않은 부분

- `/api/v1/review-object` endpoint는 아직 구현하지 않았다. Phase 4에서 구현한다.
- Rule Engine은 아직 구현하지 않았다. Phase 2에서 구현한다.
- RAG 검색은 아직 구현하지 않았다. Phase 3A/3B에서 구현한다.
- LLM provider는 아직 구현하지 않았다. Phase 5에서 구현한다.
- Review Action 저장은 아직 구현하지 않았다. Phase 6에서 구현한다.

## 6. 남은 이슈

- 현재 로컬 실행 환경에 Python 3.12가 확인되지 않았다.
- FastAPI/Pydantic 의존성이 아직 설치되지 않아 실제 app 실행과 pytest는 수행하지 못했다.
- `ReviewObjectRequest`는 작성했지만 `/api/v1/review-object` API route는 아직 없다.
- DB 설정과 환경변수 구조는 아직 없다.
- Pydantic schema는 Phase 2 이후 Rule Engine 구현 중 일부 필드가 보강될 수 있다.

## 7. 다음 Phase 제안

다음 phase는 **Phase 2. 샘플 객체 + Rule Engine**이다.

Phase 2에서 진행할 작업:

1. `data/sample_objects/`에 샘플 객체 10개 작성
2. `data/rules/`에 YAML 규칙 작성
3. Rule Engine service 구현
4. `material_missing`, `thickness_review_required`, `space_type_missing`, `expert_review_required` 탐지
5. Rule Engine unit test 작성

주의할 점:

- LLM 없이도 기본 경고가 가능해야 한다.
- Rule Engine 결과는 이후 LLM이 덮어쓰지 못하는 구조로 유지해야 한다.
- `W-012`는 반드시 `material_missing`과 `thickness_review_required`를 반환해야 한다.
