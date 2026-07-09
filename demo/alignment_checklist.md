# 설계-구현 일치도 체크리스트

설계 기준서(`docs/p6-schedule-recovery-copilot-integrated-ko.md`) 18절 체크리스트를
실제 구현과 대조한 결과다.

| # | 설계 요구 | 상태 | 구현 근거 |
|---|---|---|---|
| 1 | Python 3.12 기준 실행 | ✅ | `backend/pyproject.toml` `requires-python = ">=3.12"` |
| 2 | FastAPI backend 구조 유지 | ✅ | `backend/app/main.py`, `app/api/*` |
| 3 | PostgreSQL + pg_trgm + pgvector | ✅ | 마이그레이션 0002(vector)/0003(pg_trgm), `app/db/models.py` `Vector` 컬럼 |
| 4 | Activity/Relationship CSV import | ✅ | `app/services/schedule_import.py`, `POST /snapshots/import` |
| 5 | FS relationship만 허용 | ✅ | `schedule_import.ALLOWED_RELATIONSHIP_TYPES = {"FS"}` |
| 6 | 일정 계산은 LLM 없이 Python | ✅ | `app/services/schedule_engine.py` (NetworkX CPM), 에이전트는 수치 계산 금지 |
| 7 | RAG는 근거 제공에만 사용 | ✅ | `app/services/retrieval.py`, evidence allowlist(`app/services/evidence.py`) |
| 8 | Planner는 정확히 3개 scenario | ✅ | `app/services/agents/planner.py` `REQUIRED_SCENARIO_COUNT = 3`, rule validator 검증 |
| 9 | Human confirmation 상태 구현 | ✅ | `app/services/agents/human_selection.py`, `NEEDS_ACTIVITY_SELECTION` 상태 + `select-activity` API |
| 10 | Report는 Markdown 생성 | ✅ | `app/services/report.py`, `GET /analysis-runs/{id}/report.md` |
| 11 | Agent/RAG/계산 trace 저장 | ✅ | `agent_runs`, `retrieval_runs`, `analysis_runs`(baseline/impact JSON), `scenario_runs` 테이블 |
| 12 | Live P6 writeback 없음 | ✅ | writeback 코드 부재. 시스템은 분석/보고서만 생성, 최종 판단은 사람 |

## Agent 제한 준수

| 제한 | 상태 | 근거 |
|---|---|---|
| Mapper는 후보 밖 activity_id 생성 금지 | ✅ | 프롬프트 하드룰 + Rule Validator `activity_not_in_allowlist` |
| Mapper는 검색 밖 chunk_id 생성 금지 | ✅ | Rule Validator `evidence_not_in_allowlist` |
| Mapper는 critical/지연일 계산 금지 | ✅ | 프롬프트 명시, 수치는 엔진 계산 |
| Planner는 일정 수치(ES/EF/TF/recovered) 계산 금지 | ✅ | 프롬프트 명시, `simulate_scenario`가 계산 |
| Planner는 허용 action만 | ✅ | `RecoveryActionType` Enum + Rule Validator |
| Reviewer는 계산 결과 수정/우회 금지 | ✅ | Reviewer는 warning만 생성, 계산에 미접근 |

## Human-in-the-loop 게이트 (설계 9절)

| 조건 | 구현 |
|---|---|
| top1 confidence ≥ 0.85 | `human_selection.MIN_TOP1_CONFIDENCE = 0.85` |
| top1 − top2 ≥ 0.10 | `human_selection.MIN_CONFIDENCE_MARGIN = 0.10` |
| activity 미완료 | `is_completed` 검사 |
| activity가 snapshot에 존재 | snapshot 활동 목록 대조 |
| 미달 시 상태 | `NEEDS_ACTIVITY_SELECTION` |

## 검증

- 단위/통합 테스트: `backend/app/tests/` 96개 통과.
- 실 서버 E2E: 프로젝트→스냅샷→문서→이슈→분석→보고서 전 구간을
  실제 PostgreSQL·OpenAI 임베딩·vLLM/OpenAI 에이전트로 확인.
