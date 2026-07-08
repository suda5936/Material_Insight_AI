# Phase 03A Report: 샘플 문서 + Local Retrieval

## 1. Phase 목표

Phase 3A의 목표는 PostgreSQL이나 pgvector에 의존하기 전에, 샘플 문서 기반 검색 흐름을 빠르게 검증하는 것이다.

이번 phase에서는 Material Insight AI의 RAG 계층에 들어갈 샘플 문서 5종, 문서 메타데이터, section 단위 chunking, local keyword/metadata scoring 검색기를 구현했다. 또한 Phase 3A/4 설계 원칙에 맞춰 retrieval은 항상 실행하고, LLM prompt에 넣을 sources는 score threshold를 통과한 결과만 채택하도록 정리했다.

## 2. 수행 작업

- MVP 검색 대상 문서 5종을 작성했다.
- 문서별 메타데이터 YAML을 작성했다.
- 문서를 제목/section 단위로 chunking하는 로직을 구현했다.
- 객체 정보와 RuleResult를 검색 query terms로 변환하는 로직을 구현했다.
- metadata match, issue code match, token overlap을 조합한 local scoring을 구현했다.
- 검색 결과를 `RetrievedDocument` schema로 반환하도록 구현했다.
- `W-012` 샘플 객체를 대상으로 local retrieval script를 작성했다.
- Local Retrieval 테스트를 작성했다.
- `W-012` 검색 결과에서 `SPEC-INT-024`가 상위 결과로 나오도록 구성했다.
- 검색 결과가 없는 객체는 빈 결과를 반환하도록 테스트했다.
- 사용자 Python 3.12 venv 테스트 결과, 무관한 객체에도 문서 타입 가산점 때문에 결과가 반환되는 문제가 발견되어 scoring 로직을 수정했다.
- 후보 검색과 근거 채택을 분리했다. `search()`는 검색 후보를 반환하고, `search_relevant()`는 threshold를 통과한 근거 문서만 반환한다.
- 낮은 점수의 후보 문서가 있더라도 threshold를 통과하지 못하면 sources로 채택하지 않도록 테스트를 추가했다.

## 3. 생성/수정 파일

| 파일 | 설명 |
|---|---|
| `data/documents/document_metadata.yaml` | 샘플 문서 5종 메타데이터 |
| `data/documents/specs/spec_int_024_meeting_room_wall.md` | 회의실 구획벽 시방 기준 |
| `data/documents/standards/std_wall_general_office.md` | 일반 사무공간 내벽 설계 기준 |
| `data/documents/catalogs/cat_floor_finish.md` | 바닥 마감재 성능 카탈로그 |
| `data/documents/standards/check_ceiling.md` | 천장 마감 검토 체크리스트 |
| `data/documents/cases/case_prj_021_approved_wall.md` | 승인 프로젝트 사례 |
| `backend/app/services/local_retriever.py` | 파일 기반 Local Retrieval service |
| `backend/scripts/run_local_retrieval_sample.py` | `W-012` retrieval 실행 script |
| `backend/app/tests/test_local_retriever.py` | Local Retrieval unit test |
| `backend/README.md` | Phase 3A 검증 명령 추가 |
| `README.md` | 완료 phase와 다음 phase 업데이트 |
| `reports/phase-03a-local-retrieval-report.md` | Phase 3A 작업 보고서 |

## 4. 검증 결과

현재 Codex 터미널에서는 Python 3.12 venv와 설치된 Pydantic/FastAPI/PyYAML 환경을 직접 사용할 수 없으므로, 정적 검증을 우선 수행했다. 실제 runtime 검증은 사용자 Python 3.12 venv에서 수행하면 된다.

### 수행 완료

| 검증 | 결과 |
|---|---|
| Local Retrieval 관련 Python source syntax compile | 통과 |
| 샘플 Markdown 문서 개수 확인 | 5개 확인 |
| 문서 메타데이터 핵심 필드 확인 | `document_id`, `version`, `status`, `source` 확인 |
| `SPEC-INT-024` 메타데이터 존재 확인 | 확인 |
| `CAT-FLOOR-010` 메타데이터 존재 확인 | 확인 |
| 사용자 venv pytest 1차 실행 | 2 passed, 1 failed |
| 실패 원인 | 관련성 0점 문서에도 문서 타입 가산점이 붙음 |
| 수정 후 정적 검증 | 통과 |

실행한 정적 검증 명령:

```powershell
py -m py_compile backend\app\services\local_retriever.py backend\scripts\run_local_retrieval_sample.py backend\app\tests\test_local_retriever.py
```

샘플 문서 개수:

```text
5
```

### Python 3.12 venv에서 실행할 검증

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts/run_local_retrieval_sample.py
pytest app/tests/test_local_retriever.py
```

예상 핵심 결과:

```text
SPEC-INT-024 | 4.2 회의실 구획벽 | v2.1 | internal_project_spec | score=...
```

테스트 기대값:

- `W-012`는 `SPEC-INT-024`를 첫 번째 검색 결과로 반환한다.
- 화장실 바닥 카펫 객체는 `CAT-FLOOR-010`을 첫 번째 검색 결과로 반환한다.
- 관련 없는 객체는 빈 검색 결과를 반환한다.
- 낮은 점수의 후보 문서는 검색될 수 있지만, threshold 미통과 시 prompt sources로 채택하지 않는다.

사용자 venv에서 발견된 실패:

```text
test_unrelated_object_can_return_no_documents
AssertionError: assert [RetrievedDocument(...)] == []
```

수정 내용:

- token overlap, metadata match, issue code match가 모두 없어 score가 0인 경우 즉시 `0.0`을 반환한다.
- `project_specification`, `approved_case` 가산점은 기본 관련성이 있는 문서에만 적용한다.
- `search()`와 `search_relevant()`를 분리해 “retrieval always, augmentation conditional” 구조를 반영했다.

수정 후 재검증 명령:

```powershell
pytest app/tests/test_local_retriever.py
```

## 5. 설계 문서와의 일치 여부

Phase 3A 구현은 다음 설계 문서와 대조했다.

| 설계 문서 | 요구 사항 | 구현 반영 |
|---|---|---|
| `material_insight_implementation_guide.md` 8.1 | MVP 문서 데이터 5종 준비 | 시방서, 벽체 기준, 바닥 카탈로그, 천장 체크리스트, 과거 사례 작성 |
| `material_insight_implementation_guide.md` 8.2 | 문서 메타데이터 작성 | `document_metadata.yaml` 작성 |
| `material_insight_implementation_guide.md` 8.4 | active 문서 우선 검색 | `status=active` 문서만 검색 |
| `material_insight_implementation_guide.md` 8.4 | retrieval은 항상 실행, sources 채택은 threshold 기반 판단 | `search()`와 `search_relevant()` 분리 |
| `material_insight_implementation_guide.md` 8.4 | threshold 미통과 시 “근거 없음” 처리 | `search_relevant()`가 빈 결과 반환 |
| `material_insight_implementation_guide.md` 8.5 | `W-012`에 대해 회의실 구획벽 문서 상위 검색 | `test_w012_retrieves_meeting_room_wall_spec_first` 작성 |
| `material_insight_implementation_guide.md` 8.5 | 검색 결과에 `document_id`, `section`, `version`, `source`, `score` 포함 | `RetrievedDocument` 반환 |
| `12-implementation-phase-roadmap.md` Phase 3A | PostgreSQL 없이 local retrieval 구현 | `LocalRetriever` 구현 |
| `12-implementation-phase-roadmap.md` Phase 3A | 검색 결과 없으면 “근거 없음” 처리 가능 | 빈 결과 반환 테스트 작성 |

### 일치한 부분

- 문서 저장 위치는 `data/documents`를 사용했다.
- 문서 메타데이터는 YAML로 작성했다.
- 문서는 section 단위로 chunking한다.
- 검색 결과는 `RetrievedDocument` schema를 따른다.
- `W-012` 회의실 벽체는 `SPEC-INT-024` 문서와 연결된다.
- 검색 후보와 LLM prompt에 넣을 sources 채택 결과를 분리했다.
- threshold를 통과한 검색 결과만 이후 LLM prompt에 넣을 수 있는 구조로 반환된다.
- PostgreSQL/pgvector 없이도 검색 흐름을 검증할 수 있다.

### 의도적으로 아직 구현하지 않은 부분

- embedding model은 아직 사용하지 않았다. Phase 3A는 local keyword/metadata retrieval 목적이다.
- pgvector 저장은 아직 구현하지 않았다. Phase 3B 이후 확장한다.
- 검색 API endpoint는 아직 없다. Phase 4에서 review-object API에 연결한다.
- 검색 결과 기반 fallback recommendation은 아직 없다. Phase 4에서 구현한다.

## 6. 남은 이슈

- Python 3.12 venv에서 threshold 반영 후 `run_local_retrieval_sample.py`와 `pytest app/tests/test_local_retriever.py`를 실제 실행해야 한다.
- local scoring은 MVP 검증용이므로, 문서가 늘어나면 PostgreSQL/pgvector 또는 BM25 계층으로 교체할 필요가 있다.
- 문서 메타데이터 schema validation은 아직 별도로 없다.
- 검색 결과에 대한 snippet 길이 제한이나 highlighting은 아직 구현하지 않았다.
- inactive/deprecated 문서 테스트는 아직 없다.

## 7. 다음 Phase 제안

다음 phase는 **Phase 3B. PostgreSQL 저장 구조**다.

Phase 3B에서 진행할 작업:

1. PostgreSQL 연결 설정
2. 환경변수 기반 DB 설정
3. 문서 메타데이터 저장 table 설계
4. recommendation 저장 table 설계
5. review action log table 설계
6. DB 연결 실패 시 개발용 fallback 검토

주의할 점:

- Phase 3B에서는 아직 pgvector embedding 검색까지 무리하게 확장하지 않는다.
- 먼저 문서 메타데이터와 로그 저장 구조를 안정적으로 만든다.
- Phase 3A의 local retrieval은 유지해서 DB 연결이 없어도 데모 흐름이 깨지지 않게 한다.
