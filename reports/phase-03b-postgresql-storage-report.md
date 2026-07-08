# Phase 03B Report: PostgreSQL 저장 구조

## 1. Phase 목표

Phase 3B의 목표는 PostgreSQL 서버를 활용할 수 있도록 문서 메타데이터, 추천 결과, 사용자 액션 로그 저장 기반을 만드는 것이다.

이번 phase에서는 `DATABASE_URL` 기반 DB 설정, SQLAlchemy 세션, 핵심 테이블 schema, DB 초기화 스크립트, 문서 메타데이터 seed 스크립트, DB schema 테스트를 구현했다. PostgreSQL 연결 정보가 없거나 비어 있으면 개발용 SQLite fallback을 사용하도록 설계했다.

## 2. 수행 작업

- `DATABASE_URL` 기반 설정 구조를 만들었다.
- `.env.example`을 작성했다.
- PostgreSQL driver인 `psycopg[binary]`를 추가했다.
- SQLAlchemy 2.x 기반 DB 세션 구조를 만들었다.
- 핵심 저장 테이블 3개를 설계했다.
  - `document_metadata`
  - `recommendations`
  - `review_actions`
- DB 초기화 스크립트를 작성했다.
- 문서 메타데이터 YAML을 DB에 seed하는 스크립트를 작성했다.
- DB 연결 확인 스크립트를 작성했다.
- SQLite in-memory 기반 DB schema 테스트를 작성했다.
- README에 PostgreSQL/SQLite fallback 실행 방법을 추가했다.

## 3. 생성/수정 파일

| 파일 | 설명 |
|---|---|
| `backend/.env.example` | `DATABASE_URL` 설정 예시 |
| `backend/requirements.txt` | `pydantic-settings`, `SQLAlchemy`, `psycopg[binary]` 추가 |
| `backend/pyproject.toml` | DB 관련 dependency 추가 |
| `backend/app/core/__init__.py` | core package 선언 |
| `backend/app/core/config.py` | 환경변수 기반 설정 |
| `backend/app/db/__init__.py` | db package 선언 |
| `backend/app/db/session.py` | SQLAlchemy engine/session 생성 |
| `backend/app/db/schema.py` | DB table schema 정의 |
| `backend/scripts/check_db.py` | DB 연결 확인 script |
| `backend/scripts/init_db.py` | DB table 생성 script |
| `backend/scripts/seed_document_metadata.py` | 문서 메타데이터 seed script |
| `backend/app/tests/test_db_schema.py` | DB schema 생성 및 insert 테스트 |
| `backend/README.md` | Phase 3B DB 검증 명령 추가 |
| `README.md` | 완료 phase와 다음 phase 업데이트 |
| `reports/phase-03b-postgresql-storage-report.md` | Phase 3B 작업 보고서 |

## 4. 검증 결과

### 수행 완료

| 검증 | 결과 |
|---|---|
| DB 관련 Python source syntax compile | 통과 |
| DB dependency 선언 확인 | `pydantic-settings`, `SQLAlchemy`, `psycopg[binary]` 확인 |
| DB package 파일 확인 | `schema.py`, `session.py`, `__init__.py` 확인 |

실행한 정적 검증 명령:

```powershell
py -m py_compile backend\app\core\config.py backend\app\db\session.py backend\app\db\schema.py backend\scripts\check_db.py backend\scripts\init_db.py backend\scripts\seed_document_metadata.py backend\app\tests\test_db_schema.py
```

### Codex 터미널 venv 실행 상태

Codex 터미널에서 `backend/.venv/Scripts/python.exe` 실행을 시도했지만, 다음 오류로 실제 pytest 실행은 수행하지 못했다.

```text
Unable to create process using '"C:\Users\user\AppData\Local\Programs\Python\Python312\python.exe" ...'
```

사용자 VSCode/PowerShell 환경에서는 Python 3.12 interpreter가 정상 설정되어 있으므로 아래 명령으로 실제 검증을 수행하면 된다.

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts/check_db.py
python scripts/init_db.py
python scripts/seed_document_metadata.py
pytest app/tests/test_db_schema.py
```

PostgreSQL을 사용할 경우 `.env`에 다음 값을 설정한다.

```text
DATABASE_URL=postgresql+psycopg://material_user:material_password@localhost:5432/material_insight
```

`DATABASE_URL`을 비워두면 개발용 SQLite fallback을 사용한다.

## 5. 설계 문서와의 일치 여부

Phase 3B 구현은 다음 설계 문서와 대조했다.

| 설계 문서 | 요구 사항 | 구현 반영 |
|---|---|---|
| `12-implementation-phase-roadmap.md` Phase 3B | PostgreSQL 연결 설정 | `DATABASE_URL` 기반 설정 구현 |
| `12-implementation-phase-roadmap.md` Phase 3B | 환경변수 기반 DB 설정 | `backend/.env.example`, `app/core/config.py` |
| `12-implementation-phase-roadmap.md` Phase 3B | 문서 메타데이터 테이블 설계 | `DocumentMetadataRecord` |
| `12-implementation-phase-roadmap.md` Phase 3B | recommendation 테이블 설계 | `RecommendationRecord` |
| `12-implementation-phase-roadmap.md` Phase 3B | review action 로그 테이블 설계 | `ReviewActionRecord` |
| `12-implementation-phase-roadmap.md` Phase 3B | 개발용 fallback | `sqlite:///./dev_material_insight.db` fallback |
| `material_insight_implementation_guide.md` | PostgreSQL 메타데이터/로그 저장 | SQLAlchemy schema와 session 구조 |

### 일치한 부분

- PostgreSQL을 기본 목표로 하되 환경변수 기반으로 연결하도록 했다.
- DB 연결 정보는 코드에 하드코딩하지 않았다.
- 문서 메타데이터, 추천 결과, 사용자 액션 로그가 분리된 테이블로 설계되었다.
- Phase 3A의 local retrieval은 유지되므로 DB 연결 실패가 검색 데모를 막지 않는다.
- SQLite fallback으로 개발 환경에서 구조 검증이 가능하다.

### 의도적으로 아직 구현하지 않은 부분

- pgvector extension과 embedding 저장은 아직 구현하지 않았다.
- Alembic migration은 아직 도입하지 않았다.
- API route와 DB 저장 연결은 아직 구현하지 않았다.
- Review Action 실제 저장 API는 Phase 6에서 구현한다.
- Recommendation 생성과 저장은 Phase 4~5 이후 연결한다.

## 6. 남은 이슈

- 사용자 PostgreSQL 서버의 실제 `DATABASE_URL` 값을 설정해야 한다.
- 실제 PostgreSQL에 table 생성과 seed가 정상 동작하는지 사용자 환경에서 검증해야 한다.
- PostgreSQL schema migration 전략은 추후 Alembic 도입 여부를 결정해야 한다.
- `document_metadata.keywords` 등 JSON 컬럼의 색인 전략은 Phase 3B에서는 다루지 않았다.
- pgvector는 Phase 3B 범위에서 제외했고, local retrieval을 우선 유지한다.

## 7. 다음 Phase 제안

다음 phase는 **Phase 4. Review Object API End-to-End**다.

Phase 4에서 진행할 작업:

1. `/api/v1/review-object` endpoint 구현
2. `ReviewObjectRequest` validation 연결
3. Rule Engine 실행 연결
4. Local Retriever 실행 연결
5. LLM 없이 fallback recommendation 생성
6. `RecommendationResult` 응답 반환
7. 필요 시 recommendation DB 저장은 선택적으로 연결

주의할 점:

- Phase 4의 핵심은 API 한 번으로 `W-012 -> review_required` 결과가 나오는 것이다.
- LLM은 아직 붙이지 않는다.
- 검색 결과가 없으면 근거 없음과 추천 제한을 명확히 표시해야 한다.
