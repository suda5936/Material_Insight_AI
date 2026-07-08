# Material Insight AI MVP

Rhino/CAD 객체의 재료, 두께, 성능 검토를 지원하는 Human-in-the-loop AI Agent MVP 구현 프로젝트다.

이 저장소의 구현 목표는 `material_insight_explanation`에 정리된 설계 문서와 구현 가이드를 실제 실행 가능한 단계로 옮기는 것이다. 전체 구현은 한 번에 진행하지 않고 phase 단위로 나누어 검토하며, 각 phase가 끝날 때마다 `reports/`에 Markdown report를 남긴다.

## 구현 방향

Material Insight AI는 자동 설계 도구가 아니다. Rhino/CAD 객체에서 추출한 메타데이터를 바탕으로 명확한 누락과 위험은 Rule Engine이 먼저 검사하고, 관련 시방서와 카탈로그는 Retrieval/RAG 계층이 항상 검색한다. LLM에는 score threshold를 통과한 근거만 전달하고, 근거가 부족하면 “근거 없음” 상태로 규칙 결과를 정리한다.

최종 반영은 항상 설계자의 승인 이후에만 수행한다.

## 현재 진행 상태

완료된 단계:

- **Phase 0. 프로젝트 골격 및 기준 고정**
- **Phase 1. 백엔드 Skeleton + 데이터 스키마**
- **Phase 2. 샘플 객체 + Rule Engine**
- **Phase 3A. 샘플 문서 + Local Retrieval**
- **Phase 3B. PostgreSQL 저장 구조**
- **Phase 4. Review Object API End-to-End**
- **Phase 5. Multi-Provider LLM Recommendation**
- **Phase 6. Review Action Logging**
- **Phase 7. 전체 모델 QA API**
- **Phase 7B. Material Knowledge Preprocessing**
- **Phase 8. Mock Plugin UI**
- **Phase 8B. pgvector RAG 전환**
- **Phase 9. Rhino Plugin Skeleton**
- **Phase 9B. Rhino Payload Contract Test**
- **Phase 10. 통합 테스트 + 발표용 데모**

최종 정리:

- `docs/demo-scenario.md`
- `docs/design-implementation-mapping.md`
- `docs/final-validation-checklist.md`
- `docs/project-implementation-summary.md`

## 폴더 구조

```text
.
├── backend/                     # FastAPI Agent Backend
├── data/                        # 샘플 객체, 규칙, 문서 데이터
├── docs/                        # 구현 중 생성되는 API/데모 문서
├── frontend/mock-plugin-ui/     # Rhino 없이 시연 가능한 Mock Plugin UI
├── infra/                       # Docker, DB 등 실행 인프라 설정
├── material_insight_explanation/# 과제 보고서, 설계 문서, 구현 가이드
├── plugin/                      # Rhino Plugin skeleton
├── reports/                     # phase별 작업 보고서
└── work/                        # 임시 작업 공간
```

## Phase 운영 원칙

1. 각 phase는 독립적으로 검토 가능한 산출물을 만든다.
2. phase가 끝나면 `reports/phase-XX-...-report.md`를 작성한다.
3. 진행 중 필요한 경우 phase를 추가하거나 수정할 수 있다.
4. phase 변경 사항은 해당 report에 이유와 영향 범위를 기록한다.
5. 구현은 설계 문서와의 일치도를 최우선으로 둔다.

## 핵심 설계 문서

- `material_insight_explanation/material_insight_implementation_guide.md`
- `material_insight_explanation/docs/10-rhino-plugin-access.md`
- `material_insight_explanation/docs/11-processing-flow-diagram.md`
- `material_insight_explanation/docs/12-implementation-phase-roadmap.md`
- `docs/model-selection.md`
- `docs/rhino-payload-contract.md`
- `docs/rhino-plugin-runbook.md`
- `docs/demo-scenario.md`
- `docs/design-implementation-mapping.md`
- `docs/final-validation-checklist.md`

## MVP 핵심 흐름

```text
Rhino/Mock Plugin 객체 입력
-> 객체 메타데이터 표준화
-> Rule Engine 누락/위험 검사
-> Retrieval/RAG 문서 검색 항상 실행
-> score threshold 기반 sources 채택
-> LLM 또는 fallback 추천 생성
-> 사용자 수용/수정/보류/무시
-> Review Action 로그 저장
```

## 구현 범위

### 포함

- FastAPI 백엔드
- Pydantic 데이터 스키마
- YAML 기반 Rule Engine
- 샘플 객체와 샘플 문서
- Local Retrieval 및 PostgreSQL 저장 구조
- Multi-provider LLM interface
- Review Action Logging
- Mock Plugin UI
- pgvector RAG 전환
- Rhino Plugin skeleton

### 제외

- 구조 안전성 자동 확정
- 법규 적합성 최종 판정
- 제조사 제품 자동 발주
- 사용자 승인 없는 Rhino 객체 자동 수정
- 전체 건물 자동 설계

## 다음 단계

현재 MVP는 backend, Mock Plugin UI, Rhino Plugin skeleton, 실제 Rhino 객체 선택 API 호출, RAG/pgvector 전환 구조까지 Phase 10 기준으로 정리된 상태다. 이후 확장은 Rhino dock panel UI, 실제 승인 버튼 기반 객체 업데이트, 운영용 pgvector 데이터 적재, 기업 문서 수집 pipeline 순서로 진행한다.
