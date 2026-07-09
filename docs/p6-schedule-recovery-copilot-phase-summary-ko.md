# P6 Schedule Recovery Copilot Phase 정리

이 문서는 새 설계도와 최종 보고서를 기준으로 MVP 구현 순서를 한국어로 정리한 것이다.

## Phase 1 - 백엔드 기초 구조

목표: 새 P6 Copilot 설계에 맞는 백엔드 기반을 만든다.

작업:

- FastAPI 앱 이름과 설명 정리.
- Python 3.12 기준 의존성 정리.
- 환경설정 추가.
- SQLAlchemy Async DB 세션 구성.
- Alembic 마이그레이션 뼈대 추가.
- Schedule Engine 구현을 위한 NetworkX 의존성 추가.
- 공통 API 에러 응답 구조 추가.
- 기존 Rhino object sync는 옵션 모듈로 유지.

현재 상태: 진행 완료. 테스트 실패 1건은 `DATABASE_URL` 빈 문자열 fallback 문제였고 수정 완료.

## Phase 2 - 프로젝트 및 스케줄 Snapshot Import

목표: P6 또는 일정 관리 도구에서 내보낸 CSV를 프로젝트 스냅샷으로 저장한다.

작업:

- Project 모델.
- Schedule Snapshot 모델.
- Activity 모델.
- Relationship 모델.
- Activity CSV import.
- Relationship CSV import.
- FS 관계만 허용.
- 음수 lag, 중복 activity id, 누락된 predecessor/successor, cycle 후보 등을 검증.
- Snapshot health API 작성.

완료 기준:

- 샘플 activity CSV와 relationship CSV를 import할 수 있어야 한다.
- 잘못된 CSV는 명확한 validation error를 반환해야 한다.
- snapshot health가 activity 수, relationship 수, DAG 가능 여부를 보여줘야 한다.

## Phase 3 - Deterministic Schedule Engine

목표: LLM이 아니라 Python 코드로 CPM 계산을 수행한다.

작업:

- Schedule graph 구성.
- DAG 검증.
- Forward pass: ES, EF 계산.
- Backward pass: LS, LF 계산.
- Total Float 계산.
- Critical Path 도출.
- START_BLOCK 영향 계산.
- DURATION_INCREASE 영향 계산.
- Recovery scenario simulation.

완료 기준:

- LLM 없이 일정 계산이 재현 가능해야 한다.
- 선형/분기/병렬/마일스톤/완료 작업/lag/cycle 테스트가 있어야 한다.

## Phase 4 - Project-Scoped RAG

목표: 현장 문서와 승인 문서를 프로젝트 단위 근거로 검색한다.

작업:

- TXT/MD 문서 업로드.
- 1200자 chunk, 200자 overlap.
- 문서 metadata 저장.
- embedding service interface.
- pgvector 저장 구조.
- project filter 기반 검색.
- top 20 검색 후 threshold 및 metadata boost 적용.
- 최종 top 8 반환.
- evidence allowlist 검증.

완료 기준:

- 관련 문서가 있으면 evidence chunk가 반환되어야 한다.
- 관련도가 낮으면 “관련 근거 없음”으로 처리해야 한다.
- agent가 없는 evidence id를 만들면 reject해야 한다.

## Phase 5 - LLM Provider Layer

목표: OpenAI API, vLLM Qwen, vLLM Gemma 호출을 독립적으로 관리한다.

작업:

- 공통 LLM request/response 타입.
- OpenAI adapter.
- vLLM OpenAI-compatible adapter.
- provider registry.
- JSON 응답 parsing/repair.
- timeout/fallback 정책.
- 테스트에서는 fake provider 사용.

완료 기준:

- Qwen, Gemma, OpenAI를 설정으로 분리할 수 있어야 한다.
- 네트워크 없이도 provider layer 테스트가 가능해야 한다.

## Phase 6 - Agent 구현

목표: Mapper, Planner, Reviewer 역할을 명확히 나눠 구현한다.

작업:

- Issue Mapping Agent.
- Recovery Planning Agent.
- Rule Validator.
- Review Agent.
- human selection state.

Agent 제한:

- Mapper는 activity id를 만들 수 없다.
- Planner는 정확히 3개 scenario만 만든다.
- Planner는 schedule date나 recovered day를 계산하지 않는다.
- Reviewer는 deterministic calculation 결과를 수정할 수 없다.

완료 기준:

- 신뢰도가 부족하면 `NEEDS_ACTIVITY_SELECTION` 상태가 나와야 한다.
- Planner 결과는 허용된 action type만 포함해야 한다.

## Phase 7 - Orchestrator 및 Report

목표: 전체 분석 흐름을 하나의 실행 단위로 연결한다.

작업:

- Issue 생성.
- Analysis run state machine.
- Activity candidates 저장.
- RAG retrieval trace 저장.
- Schedule calculation trace 저장.
- Scenario results 저장.
- Agent runs 저장.
- Markdown report 생성.

완료 기준:

- issue analyze API 하나로 mapping, retrieval, calculation, scenario, review가 이어져야 한다.
- 분석 결과를 조회할 수 있어야 한다.
- Markdown report를 받을 수 있어야 한다.

## Phase 8 - Frontend MVP

목표: 사용자가 브라우저에서 전체 MVP 흐름을 실행할 수 있게 한다.

작업:

- Project 선택/생성.
- Activity CSV import.
- Relationship CSV import.
- Knowledge document upload.
- Delay issue 입력.
- Activity candidate 선택.
- Recovery scenario 비교.
- Human confirmation 표시.
- Markdown report preview.
- 선택적으로 Rhino object context 표시.

완료 기준:

- 사용자가 API를 직접 호출하지 않고도 데모를 끝까지 진행할 수 있어야 한다.

## Phase 9 - Demo Dataset 및 최종 검증

목표: 과제 제출과 발표에 사용할 수 있는 안정적인 데모 패키지를 만든다.

작업:

- 샘플 activity CSV.
- 샘플 relationship CSV.
- 샘플 field document.
- 샘플 delay issue.
- 예상 결과 문서.
- 최종 시연 절차.
- 설계-구현 일치도 체크리스트.

완료 기준:

- Python 3.12 환경에서 설치와 테스트가 재현되어야 한다.
- 설계 문서의 핵심 조건과 구현 결과가 서로 맞아야 한다.
