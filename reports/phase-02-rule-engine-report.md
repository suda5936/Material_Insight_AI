# Phase 02 Report: 샘플 객체 + Rule Engine

## 1. Phase 목표

Phase 2의 목표는 LLM 없이도 Material Insight AI가 명확한 누락과 위험을 탐지할 수 있도록 샘플 객체와 Rule Engine을 구현하는 것이다.

이번 phase에서는 샘플 Rhino/CAD 객체 10개, YAML 기반 규칙 파일, Rule Engine service, 샘플 실행 스크립트, Rule Engine 테스트를 작성했다.

## 2. 수행 작업

- 샘플 객체 JSON 10개를 작성했다.
- YAML 규칙 파일을 작성했다.
- Rule Engine service를 구현했다.
- field path 기반 값 조회를 구현했다.
- `all`, `any` 조건 처리를 구현했다.
- `is_null`, `is_not_null`, `equals`, `not_equals`, `less_than`, `greater_than`, `contains` operator를 구현했다.
- `DesignObjectInput`을 입력으로 받고 `RuleResult` 목록을 출력하도록 구현했다.
- 전체 샘플 객체를 평가하는 script를 작성했다.
- Rule Engine unit test를 작성했다.
- Rule Engine에 필요한 `PyYAML`을 requirements와 pyproject에 추가했다.
- `backend` 폴더에서 스크립트를 직접 실행해도 `app` package를 찾을 수 있도록 script import path를 보정했다.

## 3. 생성/수정 파일

| 파일 | 설명 |
|---|---|
| `backend/requirements.txt` | `PyYAML>=6.0.2` 추가 |
| `backend/pyproject.toml` | `PyYAML>=6.0.2` dependency 추가 |
| `backend/README.md` | Rule Engine 검증 명령 추가 |
| `README.md` | 완료 phase를 Phase 2까지 업데이트 |
| `backend/app/services/__init__.py` | service package 선언 |
| `backend/app/services/rule_engine.py` | YAML 기반 Rule Engine 구현 |
| `backend/scripts/run_rule_engine_sample.py` | 샘플 객체 전체 Rule Engine 실행 script |
| `backend/scripts/validate_sample_request.py` | 직접 실행 시 `app` package import 가능하도록 path 보정 |
| `backend/app/tests/test_rule_engine.py` | Rule Engine unit test |
| `data/rules/material_insight_rules.yaml` | Material Insight AI rule set |
| `data/sample_objects/wall_meeting_room_missing_material.json` | `W-012` 핵심 데모 객체 |
| `data/sample_objects/wall_meeting_room_valid.json` | 정상 회의실 벽체 |
| `data/sample_objects/object_unknown_context.json` | 객체 유형/공간 용도 부족 사례 |
| `data/sample_objects/floor_restroom_carpet.json` | 습식 공간 부적절 마감 검토 사례 |
| `data/sample_objects/ceiling_office_missing_material.json` | 천장 재료 누락 사례 |
| `data/sample_objects/slab_load_bearing.json` | 구조 전문가 검토 필요 슬래브 |
| `data/sample_objects/wall_corridor_missing_thickness.json` | 벽체 두께 누락 사례 |
| `data/sample_objects/wall_office_missing_space_type.json` | 공간 용도 누락 사례 |
| `data/sample_objects/wall_fire_rating_missing.json` | 내화 성능 전문가 검토 필요 사례 |
| `data/sample_objects/floor_office_valid.json` | 정상 바닥 마감 사례 |
| `reports/phase-02-rule-engine-report.md` | Phase 2 작업 보고서 |

## 4. 검증 결과

사용자 Python 3.12 venv에서 실제 Rule Engine script와 pytest 검증을 수행했다.

### 수행 완료

| 검증 | 결과 |
|---|---|
| Rule Engine 관련 Python source syntax compile | 통과 |
| 샘플 객체 JSON 개수 확인 | 10개 확인 |
| YAML 규칙 핵심 issue code 포함 여부 확인 | `material_missing`, `thickness_review_required`, `space_type_missing`, `expert_review_required` 확인 |
| `backend` 폴더 직접 실행 import path | `app` package import 경로 보정 완료 |
| `python scripts/run_rule_engine_sample.py` | 정상 실행 |
| `pytest app/tests/test_rule_engine.py` | 5 passed |

실행한 정적 검증 명령:

```powershell
py -m py_compile backend\app\services\rule_engine.py backend\scripts\run_rule_engine_sample.py backend\app\tests\test_rule_engine.py
```

샘플 객체 개수:

```text
10
```

### Python 3.12 venv 실행 결과

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts/run_rule_engine_sample.py
pytest app/tests/test_rule_engine.py
```

실제 Rule Engine script 결과:

```text
C-030: material_missing
F-021: no_issues
F-020: material_performance_review_required
OBJ-UNKNOWN: object_type_missing, space_type_missing
S-040: expert_review_required
W-015: thickness_missing
W-017: expert_review_required
W-012: material_missing, thickness_review_required, acoustic_review_required
W-013: acoustic_review_required
W-016: space_type_missing
```

실제 pytest 결과:

```text
5 passed
```

## 5. 설계 문서와의 일치 여부

Phase 2 구현은 다음 설계 문서와 대조했다.

| 설계 문서 | 요구 사항 | 구현 반영 |
|---|---|---|
| `material_insight_implementation_guide.md` Step 3 | YAML 규칙 로더와 Rule Engine 구현 | `backend/app/services/rule_engine.py` |
| `material_insight_implementation_guide.md` Step 3 | `is_null`, `equals`, `less_than`, `greater_than` operator | 구현 완료 |
| `material_insight_implementation_guide.md` Step 3 | `all`, `any` 조건 처리 | 구현 완료 |
| `material_insight_implementation_guide.md` Step 3 | `W-012`에서 `material_missing`, `thickness_review_required` 탐지 | 테스트 작성 |
| `12-implementation-phase-roadmap.md` Phase 2 | 샘플 객체 JSON 10개 작성 | `data/sample_objects/*.json` 10개 작성 |
| `12-implementation-phase-roadmap.md` Phase 2 | 정보 부족 객체는 확정 추천 금지 | `object_type_missing`, `space_type_missing` 규칙 작성 |
| `12-implementation-phase-roadmap.md` Phase 2 | 전문가 검토 필요 탐지 | `expert_review_required` 규칙 작성 |

### 일치한 부분

- Rule Engine은 LLM보다 먼저 실행되는 결정적 검사 계층으로 구현했다.
- Rule Engine 결과는 `RuleResult` Pydantic schema로 반환된다.
- 명확한 누락과 위험을 LLM 없이 탐지할 수 있다.
- `W-012`는 핵심 데모 객체로 유지했고, 재료 누락과 회의실 벽체 두께 검토 필요를 탐지하도록 했다.
- 구조/내화 관련 고위험 항목은 `requires_expert_review=true`로 표시한다.
- 객체 유형이나 공간 용도가 부족하면 확정 추천 대신 추가 입력이 필요한 상태로 분류할 수 있다.

### 의도적으로 아직 구현하지 않은 부분

- Rule Engine은 아직 API route에 연결하지 않았다. Phase 4에서 `/api/v1/review-object`에 연결한다.
- Rule Engine 결과를 추천 문장으로 바꾸는 fallback recommender는 아직 없다. Phase 4에서 구현한다.
- RAG 검색은 아직 없다. Phase 3A에서 local retrieval을 구현한다.
- DB 저장은 아직 없다. Phase 3B와 Phase 6에서 구현한다.

## 6. 남은 이슈

- Rule severity 우선순위 정렬은 아직 구현하지 않았다. Phase 4 또는 Phase 7에서 필요하다.
- rule file schema validation은 아직 별도로 없다. 규칙이 늘어나면 추가하는 것이 좋다.
- `review_status` 누락 검사는 아직 rule로 넣지 않았다. 필요하면 Phase 2 보강 또는 Phase 7 QA에서 추가할 수 있다.
- 동일 유형 객체 간 속성 불일치 검사는 단일 객체 Rule Engine 범위를 넘어가므로 Phase 7 전체 모델 QA에서 다루는 것이 적절하다.

## 7. 다음 Phase 제안

다음 phase는 **Phase 3A. 샘플 문서 + Local Retrieval**이다.

Phase 3A에서 진행할 작업:

1. 회의실 구획벽 시방서 샘플 작성
2. 일반 벽체 기준 샘플 작성
3. 바닥 마감재 카탈로그 샘플 작성
4. 천장 체크리스트 샘플 작성
5. 과거 승인 사례 샘플 작성
6. 문서 메타데이터 작성
7. PostgreSQL 없이 동작하는 local retrieval 구현
8. `W-012` 질의에서 회의실 구획벽 문서가 검색되는지 검증

주의할 점:

- Phase 3A에서는 아직 pgvector에 의존하지 않는다.
- 검색 결과에는 `document_id`, `section`, `version`, `source`가 포함되어야 한다.
- 검색 결과가 없는 경우 “근거 없음”을 반환해야 한다.
