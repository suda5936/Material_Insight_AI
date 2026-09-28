# P6 Schedule Recovery Copilot 처리 흐름 상세 설명

이 문서는 전체 처리 흐름에서 RAG가 무엇을 가져오는지, 그리고 Issue Mapping Agent 이후 단계들이 왜 필요한지 설명한다.

## 1. RAG 검색을 통해 얻는 것

RAG 검색은 일정 계산값을 얻는 단계가 아니다.

RAG가 가져오는 것은 **현장 문제를 해석하고 보고서에 근거로 붙일 수 있는 문서 조각**이다.

예를 들어 사용자가 다음과 같이 입력했다고 가정한다.

```text
A동 12층 커튼월 자재 납품이 10일 지연되었습니다.
```

RAG는 다음과 같은 문서를 검색한다.

- 자재 납기 지연 메일
- 공정회의록
- 작업일보
- RFI
- NCR
- 시공계획서
- 승인 지연 기록
- 과거 recovery plan
- 협력업체 공문

그리고 그 안에서 관련 문장 chunk를 가져온다.

예시:

```text
회의록 2026-07-03:
A동 12층 커튼월 unit 납품이 공급사 문제로 약 10일 지연될 가능성이 있음.

자재 납기 메일 2026-07-04:
CW-A-12 구간 자재 입고 예정일이 7월 10일에서 7월 20일로 변경됨.

시공계획서:
커튼월 설치 전 자재 반입 및 양중 가능 여부 확인 필요.
```

즉 RAG 결과는 다음 역할을 한다.

- 사용자의 issue가 실제 문서에 근거가 있는지 확인한다.
- 지연 원인, 위치, 공종, 기간, 관련 제약조건을 보강한다.
- Agent가 Activity를 매핑할 때 참고할 근거를 제공한다.
- Recovery Planning Agent가 복구 대안을 만들 때 참고한다.
- 최종 보고서에 “왜 이런 판단을 했는지” citation으로 연결한다.
- 근거가 없으면 “관련 근거 없음”이라고 표시한다.

중요한 제한:

```text
RAG는 CPM 계산을 하지 않는다.
RAG는 Critical Path를 판단하지 않는다.
RAG는 일정 지연일을 확정하지 않는다.
RAG는 근거 문서와 맥락을 제공한다.
```

## 2. Issue Mapping Agent 이후 단계 설명

### 2.1 Issue Mapping Agent

역할:

자연어 issue를 일정 분석에 사용할 수 있는 구조로 바꾼다.

수행 내용:

- issue type 추출
- 위치 추출
- 공종 추출
- 지연일 추출
- impact mode 판단
- Activity 후보 재순위화
- confidence 계산
- 부족한 정보 표시

예시:

```json
{
  "issue_type": "MATERIAL_DELAY",
  "location": "A동 12층",
  "trade": "Curtain Wall",
  "delay_days": 10,
  "impact_mode": "START_BLOCK",
  "ranked_activity_candidates": [
    {
      "activity_id": "CW-A-12-010",
      "confidence": 0.92
    }
  ],
  "missing_information": []
}
```

왜 필요한가:

사용자 입력은 자연어라서 바로 CPM 계산에 쓸 수 없다.

예를 들어 “커튼월 자재가 늦는다”는 말만으로는 어떤 Activity에 적용할지, 시작 지연인지 기간 증가인지 알 수 없다.

Issue Mapping Agent는 자연어 문제를 schedule data와 연결 가능한 형태로 변환한다.

### 2.2 Human Activity Confirmation 필요 여부 판단

역할:

AI가 고른 Activity를 바로 써도 되는지, 사람이 확인해야 하는지 결정한다.

왜 필요한가:

잘못된 Activity에 지연을 적용하면 이후 CPM 계산 전체가 틀어진다.

따라서 confidence가 낮거나 후보 간 차이가 작으면 사람이 선택해야 한다.

자동 선택 가능 조건 예시:

- top 1 confidence >= 0.85
- top 1과 top 2 차이 >= 0.10
- Activity가 완료 상태가 아님
- Activity ID가 실제 schedule snapshot 안에 존재함

조건을 만족하지 않으면 다음 상태를 반환한다.

```text
NEEDS_ACTIVITY_SELECTION
```

수행 내용:

- Activity 후보 confidence 검토
- 자동 선택 가능 여부 판단
- 필요 시 사용자에게 Activity 선택 요청

### 2.3 Baseline CPM 계산

역할:

문제가 발생하기 전 기존 일정의 CPM 상태를 계산한다.

수행 내용:

- Activity graph 생성
- FS 관계 기준 forward pass
- backward pass
- ES, EF, LS, LF 계산
- Total Float 계산
- Critical Path 도출
- baseline project duration 계산

왜 필요한가:

지연 영향은 “기존 일정과 비교”해야 알 수 있다.

Baseline이 없으면 지연 후 일정이 얼마나 나빠졌는지 판단할 기준이 없다.

출력 예시:

```text
기존 프로젝트 기간: 120일
대상 Activity ES: 40일
대상 Activity TF: 0일
Critical Path 포함 여부: Yes
```

### 2.4 Impact CPM 계산

역할:

Issue를 반영했을 때 일정이 어떻게 변하는지 계산한다.

수행 내용:

- 선택된 Activity에 지연 조건 적용
- `START_BLOCK`이면 시작 가능일을 delay days만큼 뒤로 미룸
- `DURATION_INCREASE`이면 remaining duration을 증가시킴
- 변경된 schedule graph로 CPM 재계산
- project delay 계산
- 변경된 Critical Path 확인

왜 필요한가:

현장 문제가 실제로 준공일에 영향을 주는지, 영향이 있다면 며칠인지 정량적으로 확인해야 한다.

출력 예시:

```text
기존 프로젝트 기간: 120일
Issue 반영 후 프로젝트 기간: 130일
Project delay: 10일
Critical Path 영향: 있음
```

### 2.5 Recovery Planning Agent

역할:

일정 지연을 줄이기 위한 복구 대안 3개를 생성한다.

수행 내용:

- Impact CPM 결과 해석
- RAG 근거 문서 참고
- 가능한 복구 action 제안
- 정확히 3개 scenario 생성
- 각 scenario의 가정, 필요 승인, 위험도 작성

허용 action 예시:

- `REDUCE_START_BLOCK`
- `REDUCE_ACTIVITY_DURATION`

왜 필요한가:

공정관리자는 단순히 “10일 지연됨”을 아는 것에서 끝나지 않는다.

현장에 보고하고 검토할 수 있는 복구 대안이 필요하다.

단, 이 Agent는 일정 수치를 계산하지 않는다.

“3일 회복된다” 같은 계산은 Scenario Simulator에서 Python 코드가 수행한다.

### 2.6 Rule Validator

역할:

Recovery Planning Agent의 출력이 시스템 규칙을 지켰는지 검사한다.

수행 내용:

- scenario가 정확히 3개인지 확인
- 허용된 action type만 썼는지 확인
- 존재하는 Activity ID만 참조했는지 확인
- RAG 검색 결과에 존재하는 evidence chunk ID만 인용했는지 확인
- LLM이 계산 금지 항목을 만들지 않았는지 확인
- 안전, 품질, 계약 승인을 자동 확정하지 않았는지 확인

왜 필요한가:

LLM은 그럴듯하지만 틀린 ID나 근거를 만들 수 있다.

Validator는 Agent 결과를 그대로 믿지 않기 위한 안전장치다.

### 2.7 Scenario Simulator

역할:

복구 scenario별 일정 회복 효과를 계산한다.

수행 내용:

- scenario action을 schedule graph에 적용
- CPM 재계산
- recovered days 계산
- 남은 project delay 계산
- scenario별 비교표 생성

왜 필요한가:

복구 대안은 정량적으로 비교되어야 한다.

예시:

```text
Scenario 1: 시작 지연 5일 단축
Recovered days: 5일
Remaining delay: 5일

Scenario 2: 설치 기간 3일 단축
Recovered days: 3일
Remaining delay: 7일

Scenario 3: 시작 지연 5일 단축 + 기간 3일 단축
Recovered days: 8일
Remaining delay: 2일
```

### 2.8 Review Agent

역할:

전체 분석 결과를 독립적으로 검토한다.

수행 내용:

- Activity mapping이 과도하게 확정됐는지 검토
- 근거 문서가 충분한지 검토
- recovery scenario의 위험한 가정 표시
- 안전, 품질, 계약 검토 필요사항 표시
- 사람이 확인해야 할 항목 요약

왜 필요한가:

Validator는 규칙 위반을 잡고, Review Agent는 실무적 위험과 설명의 부족함을 잡는다.

예시 warning:

```text
- 야간작업을 전제로 한 기간 단축은 안전관리자 승인 필요.
- 커튼월 양중 장비 가용성이 확인되지 않음.
- 공급사 납기 확약 문서가 부족함.
- 계약상 EOT 판단은 별도 검토 필요.
```

### 2.9 Markdown Report 생성

역할:

분석 결과를 사람이 보고 검토할 수 있는 보고서로 정리한다.

수행 내용:

- issue 요약
- 선택된 Activity
- RAG 근거 문서
- Baseline CPM 결과
- Impact CPM 결과
- Recovery scenario 3개
- scenario별 회복 효과
- Validator 결과
- Review Agent warning
- Human confirmation 항목
- 참고 문서 citation

왜 필요한가:

최종 사용자는 API JSON이 아니라 보고서 형태의 결과물이 필요하다.

공정회의, 내부 보고, 발표, 후속 검토에 바로 활용할 수 있어야 한다.

## 3. 전체 흐름 한 문장 요약

```text
RAG는 근거 문서를 찾고,
Issue Mapping Agent는 자연어 문제를 Activity와 일정 영향 조건으로 바꾸며,
CPM Engine은 실제 일정 영향을 계산하고,
Planning/Validation/Simulation/Review 단계는 사람이 검토 가능한 복구 대안과 보고서를 만든다.
```

## 4. 단계별 짧은 요약

```text
RAG = 근거 찾기
Mapping = 문제를 일정 데이터에 연결
Baseline/Impact CPM = 실제 지연 영향 계산
Planning = 복구안 생성
Validation = 규칙 위반 차단
Simulation = 복구 효과 계산
Review = 실무 리스크 검토
Report = 사람이 볼 수 있는 결과물 생성
```
