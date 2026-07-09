# 데모 예상 결과

이 문서는 `demo/` 데이터셋으로 분석을 실행했을 때 기대되는 결과를 정리한 것이다.
일정 수치(공기, 지연일, recovered days)는 **결정론적 CPM 엔진**이 계산하므로
LLM 응답과 무관하게 항상 동일해야 한다. LLM(매핑/시나리오 설명/검토)의
문장 표현은 실행마다 달라질 수 있다.

## 입력 요약

- Activity 9개, Relationship 9개, DAG 정상.
- 이슈: "A동 12층 커튼월 자재 납품이 10일 지연되어 설치 시작이 지연될 가능성이 있습니다."

## 1. 이슈 구조화 (Issue Mapping Agent)

- issue type: 자재 지연(material delay) 계열
- 위치: A동 12층 / A-12F
- 공종: 커튼월(curtain wall)
- 지연일(delay_days): **10** (이슈 텍스트에 명시)
- impact mode: **START_BLOCK** (설치 "시작"이 지연)

## 2. Activity 매핑 및 human selection

- 최상위 후보: **A1050 (A동 12층 커튼월 설치)**
- 자재 지연이 설치 "시작"을 막는 구조이므로 A1050가 대상.
- confidence가 충분히 높으면(top1 ≥ 0.85, margin ≥ 0.10, 미완료, snapshot 존재)
  자동 선택(AUTO_SELECTED). 그렇지 않으면 `NEEDS_ACTIVITY_SELECTION` 상태가 되고
  사용자가 A1050를 직접 선택.

## 3. RAG 근거

- 관련 문서: 자재 지연 통보서(01), 공정 회의록(02), 커튼월 시공계획서(03).
- 공종(curtain wall)·위치(A-12F) metadata boost로 상위 노출.

## 4. 일정 영향 (결정론적 CPM — 고정값)

| 항목 | 값 |
|---|---|
| baseline 공기 | **68일** |
| impact 공기 | **78일** |
| 프로젝트 지연 | **10일** |
| A1050 Total Float (impact) | 0 |
| A1050 critical | 예 |

Critical Path: A1000 → A1010 → A1020 → A1030 → A1050 → A1060 → A1080

## 5. 복구 시나리오 (정확히 3개, recovered days 고정값)

Planner는 아래 action/reduction 조합을 제안하고, recovered days는 엔진이 계산한다.
(설명 문장은 실행마다 달라질 수 있으나 아래 수치는 reduction 값이 같으면 동일)

| action | reduction | 시나리오 공기 | recovered days |
|---|---|---|---|
| REDUCE_START_BLOCK | 10 | 68 | **10** |
| REDUCE_START_BLOCK | 5 | 73 | **5** |
| REDUCE_ACTIVITY_DURATION | 6 | 72 | **6** |

> 참고: Planner가 다른 reduction 값을 제안하면 recovered days도 그에 맞게
> 엔진이 재계산한다. 핵심은 "REDUCE_START_BLOCK reduction=10 → 10일 전량 회복"처럼
> 수치가 결정론적으로 재현된다는 점이다.

## 6. 규칙 검증 (Rule Validator)

- activity/evidence allowlist 및 action type 위반 없음 → passed = true.
- 자동 선택 조건 미달 또는 missing information 존재 시
  requires_human_confirmation = true.

## 7. 독립 검토 (Review Agent)

- 근거 충분성, 과한 추정, 사람 판단 필요 항목(안전/품질/비용/EOT)을 경고로 표시.
- 인력 증원(크래싱) 시나리오는 안전·품질 승인 필요를 지적하는 것이 정상.

## 8. 최종 판단

- P6 반영 여부, 복구 시나리오 선택, safety/quality/cost 승인, contract/EOT 판단은
  모두 사람이 결정한다. (시스템은 자동 확정하지 않음)
