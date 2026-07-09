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

## 실행 방법

```bash
cd backend
source ./.venv/Scripts/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

```bash
cd frontend
npm run dev
```
서버가 뜨면 `http://127.0.0.1:8000/health` 에서 상태를 확인할 수 있다.

실행 후 바로 데모 데이터 불러오기를 사용하면 레포지토리안에있는 데모파일들로 테스트 할 수 있습니다.

지연 이슈 분석 입력칸 예시 : A동 12층 커튼월 자재 납품이 10일 지연되어 설치 시작이 지연될 가능성이 있습니다.

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
- 핵심 흐름에서의 BIM/3D 모델 연동

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

## 주요 폴더

```text
backend/                     FastAPI 백엔드
docs/                        현재 P6 Copilot 핵심 문서
deliverables/                과제 제출용 Word/PPTX 산출물
tools/                       보고서/PPTX 생성 스크립트
```

## 다음 구현 방향

1. Project / Schedule Snapshot / Activity / Relationship import를 구현한다.
2. CSV validation과 snapshot health API를 만든다.
3. Python 기반 CPM Schedule Engine을 구현한다.
4. Project-scoped RAG와 evidence validation을 구현한다.
5. Mapper, Planner, Rule Validator, Reviewer를 연결한다.
6. Orchestrator와 Markdown report를 만든다.
7. Frontend를 P6 Copilot 흐름에 맞게 새로 만든다.
