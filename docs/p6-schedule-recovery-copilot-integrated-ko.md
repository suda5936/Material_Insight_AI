# P6 Schedule Recovery Copilot 통합 구현 기준서

이 문서는 사용자가 제공한 P6 Schedule Recovery Copilot 설계도와 최종 보고서를 중복 없이 합쳐 정리한 한국어 구현 기준서다.

구현 판단은 이 통합본을 우선 기준으로 삼는다.

## 1. 서비스 정의

P6 Schedule Recovery Copilot은 건설 현장에서 공정 지연 문제가 발생했을 때 공정관리자가 P6 Critical Path 영향과 복구 대안을 빠르게 검토하도록 돕는 AI Agent MVP다.

한 문장 정의:

```text
현장 문제를 자연어로 입력하면 관련 Activity와 현장 문서를 검색하고,
결정론적 일정 엔진으로 Critical Path 영향을 계산한 뒤,
복구 대안 3개와 검토 보고서를 제공하는 공정관리 보조 Copilot.
```

중요한 제한:

- P6 운영 프로젝트를 자동 수정하지 않는다.
- AI는 최종 승인자가 아니다.
- 일정 계산은 LLM이 아니라 Python 코드가 수행한다.
- RAG는 근거 문서를 제공하지만 일정 수치를 계산하지 않는다.

## 2. 대상 사용자와 업무 배경

주 사용자:

- 시공사 공정관리자
- Project Controls Engineer
- Scheduler

보조 사용자:

- 현장소장
- 공사 담당자
- 프로젝트 관리자
- 협력업체 공정 담당자
- 감리 또는 발주처 일정 검토자

건설 현장에서는 자재 지연, 장비 고장, 품질 재시공, 설계 변경, 승인 지연, 인력 부족 등이 Critical Path 또는 near-critical 작업에 영향을 줄 수 있다. 이때 담당자는 Activity, 선후행 관계, Float, 실제 진도, 문서 근거, 복구 가능성, 승인 필요사항을 함께 검토해야 하므로 시간이 오래 걸린다.

## 3. MVP 목표

MVP는 다음 업무를 지원한다.

1. 자연어 현장 문제 구조화.
2. 관련 P6 Activity 후보 탐색.
3. 현장 문서와 과거 사례 검색.
4. FS 기반 CPM 일정 영향 계산.
5. 복구 시나리오 정확히 3개 생성.
6. 시나리오별 일정 회복 효과 계산.
7. 규칙 기반 검증.
8. 독립 Review Agent 검토.
9. 근거 문서가 연결된 Markdown 분석 보고서 생성.
10. Agent, RAG, 계산 로그 저장.

## 4. MVP 포함 범위

- 프로젝트 생성.
- Activity CSV import.
- Relationship CSV import.
- 현장 문서 TXT/MD import.
- 문서 chunking.
- Embedding 생성.
- PostgreSQL 저장.
- pg_trgm 기반 Activity 검색.
- pgvector 기반 문서 검색.
- 자연어 Issue 입력.
- Issue Mapping Agent.
- Recovery Planning Agent.
- Rule Validator.
- Review Agent.
- Human confirmation 상태.
- Markdown 보고서.
- 단위 및 통합 테스트.

## 5. MVP 제외 범위

- 운영 P6 프로젝트 직접 writeback.
- 완전한 XER parser.
- SS, FF, SF 관계 완전 지원.
- 복수 calendar.
- resource leveling.
- 비용 자동 산정.
- 핵심 MVP 흐름에서의 BIM/Rhino 연동.
- 사진 및 영상 분석.
- 계약 책임 자동 판단.
- 자동 승인.
- agent의 자유 토론식 의사결정.
- fine-tuning.
- 외부 vector DB 의존.

Rhino object sync는 기존 구현을 폐기하지 않고 보존하되, 핵심 MVP가 아니라 선택적 위치/context 보조 모듈로만 사용한다.

## 6. 기술 구성

| 영역 | 기준 |
|---|---|
| Backend | FastAPI, Python 3.12 |
| Database | PostgreSQL, pg_trgm, pgvector |
| ORM | SQLAlchemy Async |
| Migration | Alembic |
| Activity 검색 | PostgreSQL pg_trgm |
| 문서 검색 | pgvector |
| 일정 계산 | Python, NetworkX |
| Planner | OpenAI API |
| Mapper | vLLM Qwen |
| Reviewer | vLLM Gemma |
| Reviewer fallback | OpenAI API |

보완 사항:

- OpenAI는 `OPENAI_API_KEY` 기반 API 호출만 사용한다.
- vLLM은 현재 사용 가능한 Qwen, Gemma 모델만 전제로 한다.
- Embedding은 OpenAI embedding adapter를 우선 구현한다.
- vLLM embedding은 별도 embedding endpoint가 준비된 경우에만 확장한다.

## 7. 전체 처리 흐름

```text
Project 생성
-> Activity CSV 업로드
-> Relationship CSV 업로드
-> 현장 문서 TXT/MD 업로드
-> 문서 chunking 및 embedding
-> 자연어 issue 입력
-> Activity 후보 검색
-> RAG 근거 검색
-> Issue Mapping Agent
-> Human Activity Confirmation 필요 여부 판단
-> Baseline CPM 계산
-> Impact CPM 계산
-> Recovery Planning Agent
-> Rule Validator
-> Scenario Simulator
-> Review Agent
-> Markdown Report 생성
```

## 8. Agent 역할과 제한

### 8.1 Issue Mapping Agent

기본 모델: vLLM Qwen.

역할:

- 현장 문제를 구조화한다.
- issue type, 위치, 공종, 지연일, impact mode를 추출한다.
- SQL 후보와 RAG 근거를 바탕으로 Activity 후보를 재순위화한다.
- confidence와 missing information을 반환한다.

금지:

- 후보 목록 밖의 Activity ID 생성.
- 검색 결과 밖의 chunk ID 생성.
- critical 여부 추측.
- 프로젝트 지연일 계산.
- 지연일이 없을 때 임의 생성.

### 8.2 Recovery Planning Agent

기본 모델: OpenAI API.

역할:

- 일정 엔진의 impact 결과를 해석한다.
- 근거 문서를 참고하여 복구 시나리오를 만든다.
- 정확히 3개의 scenario를 반환한다.

허용 action:

- `REDUCE_START_BLOCK`
- `REDUCE_ACTIVITY_DURATION`

금지:

- ES, EF, LS, LF, Total Float, critical path, project delay, recovered days 계산.
- 허용되지 않은 action 생성.
- 현장 가능성이나 안전 승인 자동 확정.

### 8.3 Rule Validator

역할:

- agent 출력이 시스템 규칙을 지키는지 검사한다.
- activity ID와 evidence chunk ID가 allowlist 안에 있는지 확인한다.
- 복구 action type이 허용 범위 안에 있는지 확인한다.
- confidence가 낮으면 human confirmation을 요구한다.

### 8.4 Review Agent

기본 모델: vLLM Gemma.

Fallback: OpenAI API.

역할:

- mapping, scenario, evidence, rule validation 결과를 독립 검토한다.
- 누락된 근거, 과한 추정, 사람 판단이 필요한 항목을 표시한다.

금지:

- 계산 결과 수정.
- 존재하지 않는 evidence 생성.
- rule validator 결과 우회.

## 9. Human-in-the-loop 기준

Activity 자동 선택은 다음 조건을 모두 만족할 때만 허용한다.

- top 1 confidence >= 0.85
- top 1 confidence - top 2 confidence >= 0.10
- activity가 완료 상태가 아님
- activity ID가 현재 snapshot에 존재함

조건을 만족하지 않으면 상태는 다음과 같다.

```text
NEEDS_ACTIVITY_SELECTION
```

최종적으로 다음 판단은 사람이 한다.

- P6 반영 여부.
- 복구 시나리오 선택.
- safety 승인.
- quality 승인.
- cost 승인.
- contract/EOT 판단.

## 10. RAG 설계

RAG의 목적:

- 현장 문서와 과거 사례를 근거로 제공한다.
- Agent가 임의 판단하지 않도록 citation 범위를 제한한다.
- 보고서에 근거 문서를 연결한다.

RAG가 하지 않는 일:

- CPM 계산.
- critical path 판단.
- 계약 책임 판단.
- 안전/품질 승인.

입력 형식:

- TXT
- MD

Chunking:

- chunk size: 1200 characters
- overlap: 200 characters

필수 metadata:

- document type
- date
- approval status
- trade
- location
- source name

Retrieval:

1. project filter 적용.
2. metadata filter 적용.
3. vector top 20 검색.
4. threshold 적용.
5. metadata boost 적용.
6. 최종 top 8 반환.

Score:

```text
0.70 vector_similarity
+ 0.10 trade_match
+ 0.10 location_match
+ 0.05 approval_status_weight
+ 0.05 recency_weight
```

RAG 실패 처리:

- 관련 문서가 없으면 “관련 근거 없음”으로 표시한다.
- 근거가 없어도 일정 계산은 가능하다.
- 단, 보고서에는 근거 부족과 human review 필요성을 표시한다.

## 11. Schedule Engine 기준

지원 범위:

- FS relationship only.
- lag는 0 이상의 정수.
- duration은 정수 calendar day.
- 기본 calendar는 7-day calendar로 가정.
- schedule network는 DAG여야 한다.
- 일반 activity duration 최소값은 1.
- milestone duration은 0.
- completed activity remaining duration은 0.

Forward pass:

```text
ES = max(EF(predecessor) + lag)
EF = ES + remaining_duration
```

Backward pass:

```text
terminal LF = project_duration
LS = LF - remaining_duration
LF = min(LS(successor) - lag)
```

Float:

```text
Total Float = LS - ES
Critical = Total Float <= 0
```

Impact mode:

- `START_BLOCK`: 특정 Activity 시작 가능일이 지연된다.
- `DURATION_INCREASE`: 특정 Activity remaining duration이 증가한다.

Recovery simulation:

- `REDUCE_START_BLOCK`: `adjusted_block = max(0, issue_delay - reduction_days)`
- `REDUCE_ACTIVITY_DURATION`: `adjusted_duration = max(min_duration, current_duration - reduction_days)`

LLM 계산 금지 항목:

- ES
- EF
- LS
- LF
- Total Float
- project duration
- project delay
- critical path
- recovered days

## 12. 데이터 모델 초안

핵심 테이블:

- `projects`
- `schedule_snapshots`
- `activities`
- `relationships`
- `issues`
- `analysis_runs`
- `activity_matches`
- `scenario_runs`
- `agent_runs`
- `reports`

RAG 테이블:

- `knowledge_documents`
- `knowledge_chunks`
- `retrieval_runs`

구현 주의:

- schedule snapshot은 분석 재현성을 위해 불변에 가깝게 다룬다.
- analysis run은 사용한 snapshot, issue, retrieved chunks, agent outputs, calculation outputs를 추적해야 한다.
- agent output은 나중에 검토할 수 있도록 원문 JSON을 보존한다.

## 13. API 기준

Project:

- `POST /api/v1/projects`
- `GET /api/v1/projects`

Schedule:

- `POST /api/v1/projects/{project_id}/snapshots/import`
- `GET /api/v1/snapshots/{snapshot_id}/health`

Knowledge:

- `POST /api/v1/projects/{project_id}/knowledge/documents`
- `GET /api/v1/projects/{project_id}/knowledge/documents`
- `POST /api/v1/projects/{project_id}/knowledge/search`
- `DELETE /api/v1/knowledge/documents/{document_id}`

Analysis:

- `POST /api/v1/issues`
- `POST /api/v1/issues/{issue_id}/analyze`
- `POST /api/v1/issues/{issue_id}/select-activity`
- `GET /api/v1/analysis-runs/{analysis_run_id}`
- `GET /api/v1/analysis-runs/{analysis_run_id}/report.md`

## 14. 구현 Phase

### Phase 1 - Backend Foundation

- FastAPI metadata.
- Settings.
- SQLAlchemy Async.
- Alembic.
- Error handler.
- Logging.

### Phase 2 - Schedule Data

- Project model.
- Snapshot model.
- Activity import.
- Relationship import.
- Validation.
- Snapshot health.

### Phase 3 - Schedule Engine

- Graph DTO.
- Forward/backward pass.
- Float and critical path.
- Impact mode.
- Scenario simulation.

### Phase 4 - RAG

- Document upload.
- Chunking.
- Embedding interface.
- pgvector storage.
- Retrieval scoring.
- Evidence allowlist.

### Phase 5 - LLM Provider

- OpenAI adapter.
- vLLM adapter.
- Provider registry.
- JSON repair and fallback.

### Phase 6 - Agents

- Mapper.
- Planner.
- Rule Validator.
- Reviewer.
- Human selection flow.

### Phase 7 - Orchestrator and Report

- Analysis state machine.
- Trace persistence.
- Markdown report.
- End-to-end tests.

### Phase 8 - Frontend MVP

- Project selector.
- CSV import.
- Knowledge upload.
- Issue input.
- Activity selection.
- Scenario comparison.
- Report preview.

### Phase 9 - Demo and Final Verification

- Demo CSV.
- Demo documents.
- Demo issue.
- Expected output.
- Design-implementation alignment checklist.

## 15. 평가 지표

업무 효과:

- Activity 탐색 시간 감소.
- recovery scenario 작성 시간 감소.
- 보고서 초안 작성 시간 감소.
- human confirmation까지 걸리는 시간 감소.

Agent 품질:

- Activity mapping precision.
- missing information detection.
- evidence citation validity.
- JSON schema validity.
- hallucination rate.

RAG 품질:

- relevant chunk recall.
- citation correctness.
- no-evidence handling.
- metadata filter accuracy.

Schedule Engine:

- CPM calculation correctness.
- cycle detection.
- delay impact accuracy.
- scenario recovered-day calculation correctness.

## 16. 위험과 통제

| 위험 | 통제 |
|---|---|
| 잘못된 Activity 매핑 | confidence threshold와 human selection |
| LLM의 일정 수치 환각 | 일정 계산은 Python만 수행 |
| 존재하지 않는 근거 인용 | evidence allowlist 검증 |
| 현재 프로젝트와 다른 과거 사례 | metadata와 reviewer warning |
| 계약/안전 판단 오용 | human approval 필수 |
| P6와 MVP 계산 차이 | MVP 범위와 calendar 제한 명시 |

## 17. 최종 데모 기준

데모 데이터:

- Activity CSV.
- Relationship CSV.
- 회의록 또는 자재 지연 문서.
- 시공계획서 또는 승인 문서.
- 자연어 issue.

예시 issue:

```text
A동 12층 커튼월 자재 납품이 10일 지연되어 설치 시작이 지연될 가능성이 있습니다.
```

기대 결과:

- 관련 Activity 후보 제시.
- confidence가 부족하면 human selection 요구.
- RAG 근거 문서 표시.
- baseline/impact CPM 계산.
- critical path 영향 표시.
- 복구 scenario 3개 제시.
- scenario별 recovered days 계산.
- rule validation 결과 표시.
- reviewer warning 표시.
- Markdown report 생성.

## 18. 설계-구현 일치도 체크리스트

- [ ] Python 3.12 기준으로 실행된다.
- [ ] FastAPI backend 구조를 유지한다.
- [ ] PostgreSQL, pg_trgm, pgvector를 목표 구조로 둔다.
- [ ] Activity/Relationship CSV import가 구현된다.
- [ ] FS relationship만 MVP에서 허용한다.
- [ ] Schedule 계산은 LLM 없이 Python에서 수행된다.
- [ ] RAG는 근거 제공에만 사용된다.
- [ ] Planner는 정확히 3개 scenario를 반환한다.
- [ ] Human confirmation 상태가 구현된다.
- [ ] Report는 Markdown으로 생성된다.
- [ ] Agent/RAG/계산 trace가 저장된다.
- [ ] Live P6 writeback이 없다.
