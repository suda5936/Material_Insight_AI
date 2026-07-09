# P6 Schedule Recovery Copilot

이 프로젝트는 건설 공정관리자를 위한 **Critical Path 지연 복구 의사결정 보조 AI Agent**를 구현하기 위한 작업 공간이다.

핵심 목표는 다음과 같다.

```text
시공 중 Critical Path 지연 문제가 발생했을 때,
공정관리자가 관련 Activity를 찾고,
일정 영향을 계산하고,
복구 시나리오를 비교하고,
사람이 검토할 수 있는 보고서 초안을 빠르게 만들도록 돕는다.
```

이 시스템은 P6를 자동으로 수정하는 도구가 아니다.

AI가 최종 결정을 내리지도 않는다.

AI는 현장 문제를 구조화하고, 근거 문서를 찾고, 복구안 초안을 만들고, 검토 포인트를 정리한다.  
일정 계산과 최종 판단은 각각 **Python 코드**와 **사람**이 담당한다.

## 현재 봐야 할 문서

`docs` 폴더에는 현재 핵심 문서만 남겨두었다.

- `docs/p6-schedule-recovery-copilot-integrated-ko.md`  
  전체 설계 기준서. 서비스 정의, MVP 범위, Agent 역할, RAG, Schedule Engine, API 기준이 들어 있다.

- `docs/p6-schedule-recovery-copilot-phase-summary-ko.md`  
  Phase별 구현 계획. 앞으로 어떤 순서로 개발할지 정리한 문서다.

- `docs/p6-copilot-processing-flow-explanation-ko.md`  
  RAG가 무엇을 가져오는지, Issue Mapping 이후 각 단계가 왜 필요한지 설명한 문서다.

## MVP 전체 흐름

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

## 핵심 설계 원칙

- LLM은 해석, 생성, 검토를 담당한다.
- ES, EF, LS, LF, Total Float, Critical Path, Project Delay, Recovered Days 계산은 Python 코드가 수행한다.
- RAG는 근거 문서를 찾는 역할만 한다.
- RAG는 CPM 계산이나 Critical Path 판단을 하지 않는다.
- MVP는 FS 관계, 0 이상 lag, 정수 duration, 7-day calendar 가정을 사용한다.
- MVP는 P6 운영 프로젝트에 직접 writeback하지 않는다.
- Activity 선택, 복구안 선택, P6 반영, 안전, 품질, 비용, 계약 판단은 사람이 최종 확인한다.

## MVP 포함 범위

- 프로젝트 생성
- Activity CSV import
- Relationship CSV import
- 현장 문서 TXT/MD import
- 문서 chunking
- embedding 생성
- PostgreSQL 저장
- pg_trgm 기반 Activity 검색
- pgvector 기반 문서 검색
- 자연어 Issue 입력
- Issue Mapping Agent
- Recovery Planning Agent
- Rule Validator
- Review Agent
- Human confirmation 상태
- Markdown 보고서
- 단위 및 통합 테스트

## MVP 제외 범위

- XER 파일 직접 파싱
- 운영 P6 프로젝트 자동 수정
- SS, FF, SF 관계 완전 지원
- 복수 calendar
- resource leveling
- 비용 자동 산정
- 계약 책임 자동 판단
- 안전/품질 자동 승인
- 사진/영상 분석
- 핵심 흐름에서의 BIM/Rhino 연동

## P6 데이터 입력 방식

현재 MVP는 XER 파일을 직접 받지 않는다.

대신 다음 흐름을 사용한다.

```text
P6
-> Activity / Relationship 데이터를 Spreadsheet 또는 Excel로 export
-> 필요한 컬럼 정리
-> CSV로 저장
-> 시스템 import
-> 내부 schedule graph 생성
-> Python 코드로 CPM 계산
```

즉, MVP는 `P6 export 데이터 -> CSV -> 내부 CPM graph` 구조다.

XER parser는 향후 확장 기능으로 둔다.

## 보존된 선택 모듈

기존 Rhino 객체 탐지/선택 기능은 완전히 삭제하지 않고 별도 선택 모듈로 보존했다.

```text
modules/rhino-object-sync/
```

이 모듈은 Material Review용이 아니다.

현재 역할은 공정 이슈와 관련된 위치/context를 보조적으로 연결하는 것이다.

예시:

```text
Rhino에서 영향 객체 선택
-> object_id / layer / bbox / location context 저장
-> 해당 정보를 CP delay issue의 보조 context로 사용
```

단, Rhino 정보는 Schedule Engine의 핵심 계산 입력이 아니다.

## 주요 폴더

```text
backend/                     FastAPI 백엔드
frontend/mock-plugin-ui/     기존 브라우저 UI, 추후 P6 Copilot용으로 재구성 예정
plugin/RhinoMaterialInsight/ 보존된 Rhino plugin 구현
modules/rhino-object-sync/   Rhino object sync 선택 모듈 설명
docs/                        현재 P6 Copilot 핵심 문서
reports/                     현재 Phase report
deliverables/                과제 제출용 Word/PPTX 산출물
```

## 다음 구현 방향

1. Rhino sync는 선택 context 모듈로 유지한다.
2. Project / Schedule Snapshot / Activity / Relationship import를 구현한다.
3. CSV validation과 snapshot health API를 만든다.
4. Python 기반 CPM Schedule Engine을 구현한다.
5. Project-scoped RAG와 evidence validation을 구현한다.
6. Mapper, Planner, Rule Validator, Reviewer를 연결한다.
7. Orchestrator와 Markdown report를 만든다.
8. Frontend를 P6 Copilot 흐름에 맞게 재구성한다.
