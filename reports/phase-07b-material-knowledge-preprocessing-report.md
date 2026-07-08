# Phase 7B. Material Knowledge Preprocessing Report

## 1. 목표

RAG/vector DB에 넣을 재료 지식과 기존 문서 지식을 같은 chunk schema로 전처리하는 기반을 만든다.

이 phase는 Phase 3A의 Local Retrieval과 Phase 3B의 PostgreSQL/pgvector 확장 사이를 연결한다. MVP에서는 로컬 JSON/YAML 기반으로 검증하고, 이후 pgvector 적재 시 같은 schema를 재사용한다.

## 2. 작업 내용

### 2.1 Material catalog 추가

`data/materials/material_catalog.yaml`을 추가했다.

초기 MVP 범위의 재료는 다음 객체 타입 중심으로 구성했다.

- `interior_wall`
- `floor_finish`
- `ceiling_finish`

각 재료 항목은 다음 정보를 가진다.

- `material_id`
- `name`
- `korean_name`
- `object_types`
- `space_types`
- `performance_tags`
- `recommended_use`
- `caution_notes`
- `source_type`
- `source`
- `version`
- `effective_date`
- `status`

### 2.2 Performance tag 사전 추가

`data/materials/performance_tags.yaml`을 추가했다.

Rule Engine, Retrieval, LLM prompt에서 공통으로 사용할 수 있도록 성능 태그를 명시했다.

- `acoustic`
- `fire`
- `wet_area`
- `maintenance`
- `durability`
- `lightweight`
- `constructability`
- `privacy`
- `comfort`

### 2.3 RAG chunk builder 추가

`backend/scripts/build_rag_chunks.py`를 추가했다.

이 스크립트는 다음 두 소스를 읽어 동일한 JSONL schema로 변환한다.

- `data/documents/document_metadata.yaml`
- `data/materials/material_catalog.yaml`

출력 위치는 다음과 같다.

```text
data/processed/rag_chunks.jsonl
```

### 2.4 테스트 추가

`backend/app/tests/test_rag_chunk_builder.py`를 추가했다.

검증 내용은 다음과 같다.

- material catalog가 chunk로 변환되는가
- 문서 chunk와 재료 chunk가 공통 필드를 가지는가
- chunk text가 비어 있지 않은가

## 3. 데이터 수집 방향성

RAG vector DB에는 단순히 “문서 파일”만 넣는 것이 아니라, 객체 검토에 필요한 재료 후보와 성능 검토 근거를 함께 넣어야 한다.

MVP 이후 데이터 수집은 다음 순서가 적절하다.

1. 사내 표준 시방서와 프로젝트 승인 사례를 우선 수집한다.
2. 각 문서에 `object_type`, `space_type`, `performance_tags`를 수동 태깅한다.
3. 제조사 카탈로그는 출처, 버전, 유효일자, 적용 조건이 확인되는 항목만 넣는다.
4. 승인된 프로젝트 사례는 “추천 근거”가 아니라 “참고 사례”로 구분한다.
5. 성능 수치, 법규 적합성, 내화 등급은 근거 문서가 없으면 임의로 생성하지 않는다.
6. 검색 결과는 항상 반환 후보로 만들되, threshold를 통과한 항목만 LLM prompt의 sources로 채택한다.

초기 카탈로그는 MVP 데모용 sample data이므로 실제 프로젝트 적용 전에는 검증된 사내 문서 또는 제조사 자료로 교체해야 한다.

## 4. 설계 문서 일치성 검토

### 일치한 점

- `07-rag-hitl.md`의 “근거 기반 추천” 흐름과 일치한다.
- Phase 3A에서 정한 “retrieval은 항상 실행, augmentation은 threshold 기반 채택” 원칙을 유지했다.
- `05-mvp-design.md`의 재료, 두께, 성능 검토 중심 범위를 벗어나지 않았다.
- Rhino 객체 payload를 직접 바꾸지 않고, backend 내부 검색 지식 계층만 확장했다.
- 사용자 승인 없는 자동 수정은 여전히 수행하지 않는다.

### 의도적으로 남긴 범위

- 실제 embedding 생성은 아직 구현하지 않았다.
- pgvector 적재는 다음 DB/vector phase에서 진행한다.
- 제조사 PDF 파싱, OCR, 웹 수집은 MVP 초기 범위에서 제외했다.

## 5. 검증 방법

```powershell
cd backend
python scripts/build_rag_chunks.py
pytest app/tests/test_rag_chunk_builder.py
```

## 6. 검증 결과

현재 Codex 실행 세션에서는 `python`, `py -3.12`, `.venv\Scripts\python.exe`가 모두 정상 실행되지 않았다. `.venv`는 사용자 PC의 Python 3.12 경로를 가리키고 있으나, 이 세션에서는 해당 실행 파일을 프로세스로 만들 수 없어 테스트를 완료하지 못했다.

사용자 로컬 VS Code/PowerShell의 Python 3.12 interpreter 환경에서는 아래 명령으로 검증하면 된다.

```powershell
cd backend
python scripts/build_rag_chunks.py
pytest app/tests/test_rag_chunk_builder.py
```

예상 결과는 `data/processed/rag_chunks.jsonl` 생성과 rag chunk builder 테스트 통과다.

## 7. 산출물

- `data/materials/material_catalog.yaml`
- `data/materials/performance_tags.yaml`
- `backend/scripts/build_rag_chunks.py`
- `backend/app/tests/test_rag_chunk_builder.py`
- `backend/README.md`
- `README.md`
- `material_insight_explanation/docs/12-implementation-phase-roadmap.md`

## 8. 다음 단계 제안

Phase 8에서는 Mock Plugin UI에서 review 결과, sources, scan-model 결과를 시각적으로 확인할 수 있게 구현한다.

별도 후속 phase로는 `Phase 8B` 또는 `Phase 9B`에서 pgvector embedding 적재와 검색 교체를 진행하는 것이 적절하다.
