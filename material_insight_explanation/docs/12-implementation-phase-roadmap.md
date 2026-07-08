# 12. 구현 페이즈 로드맵

## 12.1 운영 원칙

Material Insight AI 구현은 전체 기능을 한 번에 완성하지 않고, 검토 가능한 페이즈 단위로 진행한다. 각 페이즈가 끝날 때마다 작업 내용, 산출물, 검증 결과, 남은 이슈를 Markdown report로 작성한다.

페이즈는 고정된 계약이 아니라 진행 중 필요에 따라 추가하거나 수정할 수 있다. 단, 변경이 발생하면 해당 phase report에 변경 이유와 영향 범위를 기록한다.

---

## 12.2 사용 가능한 서비스 반영

현재 활용 가능한 서비스는 다음과 같다.

| 서비스 | 활용 위치 | 전략 |
|---|---|---|
| OpenAI API key | LLM Recommendation Layer | 기본 LLM provider로 사용 |
| vLLM gemma 4b | LLM fallback 또는 경량 테스트 | 비용 절감 및 로컬 대체 경로로 활용 가능 |
| vLLM qwen 27b | 고성능 local/vLLM provider | OpenAI 대체 provider로 확장 가능 |
| PostgreSQL server | 문서 메타데이터, 로그, 추후 vector search | Phase 3B 이후 연결 |
| Shell server | 원격 실행 또는 배포 | MVP 초기에는 필수 아님 |

LLM 계층은 특정 모델에 종속되지 않도록 provider interface를 분리한다.

```text
LLMProvider
  - openai
  - vllm-gemma
  - vllm-qwen
  - mock
```

이 구조를 통해 OpenAI API를 기본값으로 사용하되, vLLM 모델로 교체 가능한 형태를 유지한다.

---

## 12.3 전체 페이즈 요약

| Phase | 이름 | 핵심 목표 | Report |
|---:|---|---|---|
| 0 | 프로젝트 골격 및 기준 고정 | 폴더 구조, README, report 템플릿 준비 | `reports/phase-00-project-setup-report.md` |
| 1 | 백엔드 Skeleton + 데이터 스키마 | FastAPI 기본 앱과 Pydantic 모델 구현 | `reports/phase-01-backend-schema-report.md` |
| 2 | 샘플 객체 + Rule Engine | LLM 없이 누락·위험 탐지 | `reports/phase-02-rule-engine-report.md` |
| 3A | 샘플 문서 + Local Retrieval | pgvector 없이 문서 검색 흐름 검증 | `reports/phase-03a-local-retrieval-report.md` |
| 3B | PostgreSQL 저장 구조 | 문서 메타데이터와 로그 저장 기반 마련 | `reports/phase-03b-postgresql-storage-report.md` |
| 4 | Review Object API End-to-End | 객체 하나를 입력해 검토 결과 반환 | `reports/phase-04-review-object-api-report.md` |
| 5 | Multi-Provider LLM Recommendation | OpenAI/vLLM/mock provider 구조와 추천 생성 | `reports/phase-05-llm-recommendation-report.md` |
| 6 | Review Action Logging | HITL 사용자 액션 저장 | `reports/phase-06-review-logging-report.md` |
| 7 | 전체 모델 QA API | 여러 객체 일괄 검사 및 요약 | `reports/phase-07-scan-model-report.md` |
| 8 | Mock Plugin UI | Rhino 없이 발표 가능한 UI 데모 | `reports/phase-08-mock-plugin-ui-report.md` |
| 9 | Rhino Plugin Skeleton | 실제 Rhino 연동 경계와 C# 구조 제시 | `reports/phase-09-rhino-plugin-skeleton-report.md` |
| 10 | 통합 테스트 + 발표용 데모 | 최종 검증, README, 시연 시나리오 정리 | `reports/phase-10-integration-demo-report.md` |

---

## 12.4 Phase 0. 프로젝트 골격 및 기준 고정

### 목표

구현 기준을 흔들리지 않게 고정하고, 이후 페이즈 산출물이 들어갈 위치를 명확히 만든다.

### 주요 작업

1. 프로젝트 폴더 구조 생성
2. `backend`, `data`, `docs`, `reports`, `frontend/mock-plugin-ui`, `plugin` 기본 구조 생성
3. README 초안 작성
4. 구현 범위와 제외 범위 명시
5. phase report 템플릿 생성

### 검토 기준

- 폴더 구조가 구현 가이드와 일치하는가
- 이후 페이즈별 산출물 위치가 명확한가
- report 템플릿이 재사용 가능하게 작성되었는가

### Report

```text
reports/phase-00-project-setup-report.md
```

---

## 12.5 Phase 1. 백엔드 Skeleton + 데이터 스키마

### 목표

Agent가 받을 입력과 내보낼 출력을 코드로 고정한다.

### 주요 작업

1. FastAPI 앱 생성
2. `/health` API 구현
3. Pydantic 모델 구현
   - `DesignObjectInput`
   - `ProjectContext`
   - `RuleResult`
   - `RetrievedDocument`
   - `RecommendationResult`
   - `ReviewActionRequest`
4. 샘플 request validation 확인

### 검토 기준

- `W-012` 객체 JSON이 validation을 통과하는가
- API 응답 구조가 구현 가이드와 일치하는가
- backend 실행 방법이 README에 기록되었는가

### Report

```text
reports/phase-01-backend-schema-report.md
```

---

## 12.6 Phase 2. 샘플 객체 + Rule Engine

### 목표

LLM 없이도 재료 누락, 두께 검토 필요, 공간 용도 누락, 전문가 검토 필요 같은 핵심 문제를 탐지한다.

### 주요 작업

1. 샘플 객체 JSON 10개 작성
2. YAML 규칙 파일 작성
3. Rule Engine 구현
4. `material_missing`, `thickness_review_required`, `space_type_missing`, `expert_review_required` 탐지
5. Rule Engine 테스트 작성

### 검토 기준

- 회의실 벽체 `W-012`에서 재료 누락과 두께 검토 필요가 정확히 나오는가
- 정보 부족 객체는 확정 추천하지 않고 추가 입력 요청으로 분류되는가
- Rule Engine 결과가 LLM 없이도 기본 경고로 활용 가능한가

### Report

```text
reports/phase-02-rule-engine-report.md
```

---

## 12.7 Phase 3A. 샘플 문서 + Local Retrieval

### 목표

PostgreSQL이나 pgvector에 의존하기 전에, 샘플 문서 검색 흐름을 빠르게 검증한다.

### 주요 작업

1. 샘플 시방서, 카탈로그, 사내 기준 문서 작성
2. 문서 메타데이터 작성
3. 문서 chunking 구현
4. local keyword 또는 vector-lite 검색 구현
5. 검색 결과에 `document_id`, `section`, `version`, `source` 포함

### 검토 기준

- `W-012` 질의에서 회의실 구획벽 문서가 검색되는가
- 검색 결과가 없으면 “근거 없음”으로 처리되는가
- 검색 결과가 LLM prompt에 넣기 좋은 구조로 반환되는가

### Report

```text
reports/phase-03a-local-retrieval-report.md
```

---

## 12.8 Phase 3B. PostgreSQL 저장 구조

### 목표

PostgreSQL 서버를 활용해 문서 메타데이터, 추천 결과, 사용자 액션 로그를 저장할 기반을 만든다.

### 주요 작업

1. PostgreSQL 연결 설정
2. 환경변수 기반 DB 설정
3. 문서 메타데이터 테이블 설계
4. recommendation 테이블 설계
5. review action 로그 테이블 설계
6. 추후 pgvector 확장 가능한 구조 고려

### 검토 기준

- 로컬 환경변수로 PostgreSQL 연결이 가능한가
- 문서 메타데이터와 review action을 저장할 수 있는가
- DB 연결 실패 시 개발용 fallback을 둘 수 있는가

### Report

```text
reports/phase-03b-postgresql-storage-report.md
```

---

## 12.9 Phase 4. Review Object API End-to-End

### 목표

객체 하나를 넣으면 규칙 검사, 문서 검색, 추천 결과가 한 번에 나오게 만든다.

### 주요 작업

1. `/api/v1/review-object` 구현
2. Object normalizer 구현
3. Rule Engine 연결
4. Local Retrieval 또는 PostgreSQL 검색 연결
5. LLM 없이도 fallback recommendation 생성
6. 응답 JSON을 구현 가이드 형식과 일치시킴

### 검토 기준

- `POST /api/v1/review-object` 한 번으로 `review_required` 결과가 나오는가
- 출처 문서와 required action이 포함되는가
- API 결과가 Mock Plugin UI 또는 Rhino Plugin에서 바로 사용할 수 있는가

### Report

```text
reports/phase-04-review-object-api-report.md
```

---

## 12.10 Phase 5. Multi-Provider LLM Recommendation

### 목표

OpenAI API를 기본 provider로 사용하되, vLLM과 mock provider로 교체 가능한 LLM 계층을 만든다.

### 주요 작업

1. LLM provider interface 설계
2. OpenAI provider 구현
3. vLLM provider 구조 구현
4. mock provider 구현
5. system prompt 작성
6. user prompt template 작성
7. JSON schema 기반 추천 결과 생성
8. LLM 실패 시 fallback 유지

### 검토 기준

- LLM이 Rule Engine 결과를 덮어쓰지 않는가
- 검색 문서에 없는 수치를 임의 생성하지 않는가
- provider 설정으로 `openai`, `vllm`, `mock` 경로를 선택할 수 있는가
- LLM 장애 시에도 API가 실패하지 않는가

### Report

```text
reports/phase-05-llm-recommendation-report.md
```

---

## 12.11 Phase 6. Review Action Logging

### 목표

Human-in-the-loop 흐름을 구현하고 사용자의 결정을 저장한다.

### 주요 작업

1. `/api/v1/review-actions` 구현
2. 수용, 수정, 보류, 무시, 전문가 검토 요청 저장
3. 추천 ID, 객체 ID, 사용자, 수정값, 사유, 시간 기록
4. PostgreSQL 또는 개발용 JSON 저장소 연결

### 검토 기준

- 사용자가 `edit` 액션으로 재료와 두께를 수정 저장할 수 있는가
- 변경 전후 값과 사유가 남는가
- AI 추천이 사용자 승인 없이 객체에 자동 반영되지 않는 구조인가

### Report

```text
reports/phase-06-review-logging-report.md
```

---

## 12.12 Phase 7. 전체 모델 QA API

### 목표

단일 객체가 아니라 여러 객체를 검사하는 데모를 구현한다.

### 주요 작업

1. `/api/v1/scan-model` 구현
2. 객체 배열 입력
3. 각 객체에 Rule Engine 일괄 실행
4. severity별 정렬
5. 요약 카운트 반환

### 검토 기준

- 재료 미지정, 두께 미입력, 공간 용도 누락, 전문가 검토 필요 건수가 집계되는가
- 발표용 QA 목록이 생성되는가
- 우선순위가 높은 항목부터 정렬되는가

### Report

```text
reports/phase-07-scan-model-report.md
```

---

## 12.13 Phase 8. Mock Plugin UI

### 목표

Rhino가 없어도 발표 가능한 화면을 구현한다.

### 주요 작업

1. 샘플 객체 선택 화면
2. 객체 정보 패널
3. AI 검토 결과 패널
4. 출처 문서 패널
5. 수용, 수정, 보류, 무시 버튼
6. 전체 모델 QA 화면

### 검토 기준

- `W-012` 선택, 검토 결과 표시, 수정 후 수용, 로그 저장 흐름이 가능한가
- Rhino Plugin의 대체 데모로 설명 가능한가
- UI가 구현 가이드의 Review Panel 역할과 일치하는가

### Report

```text
reports/phase-08-mock-plugin-ui-report.md
```

---

## 12.14 Phase 9. Rhino Plugin Skeleton

### 목표

실제 Rhino 연동 가능성을 코드 구조로 보여준다.

### 주요 작업

1. `plugin/RhinoMaterialInsight` skeleton 작성
2. `MaterialInsightReview` 명령 설계
3. Object Inspector 의사 구현
4. API client 구조 작성
5. README에 실제 Rhino 연동 방법 작성

### 검토 기준

- Rhino가 없어도 구조와 책임이 명확한가
- Rhino 설치 시 어떤 파일을 어디서 확장하면 되는지 설명되는가
- 객체 선택, 속성 추출, API 호출, 결과 표시 흐름이 코드 구조에 반영되는가

### Report

```text
reports/phase-09-rhino-plugin-skeleton-report.md
```

---

## 12.15 Phase 10. 통합 테스트 + 발표용 데모 정리

### 목표

과제 제출과 시연이 가능한 상태로 전체 구현을 정리한다.

### 주요 작업

1. 핵심 API 테스트
2. 데모 시나리오 문서 작성
3. README 실행 방법 정리
4. 설계-구현 매핑표 작성
5. 최종 한계와 향후 확장 정리
6. 발표용 핵심 흐름 검증

### 검토 기준

- 보고서 설계 항목과 실제 구현 파일이 매핑되는가
- `객체 선택 -> 누락 탐지 -> 문서 검색 -> 추천 -> 승인 로그` 흐름을 설명할 수 있는가
- 실패 시나리오와 안전장치가 준비되어 있는가

### Report

```text
reports/phase-10-integration-demo-report.md
```

---

## 12.16 Phase Report 공통 템플릿

각 페이즈 report는 다음 형식을 따른다.

```markdown
# Phase XX Report: 제목

## 1. Phase 목표

## 2. 수행 작업

## 3. 생성/수정 파일

## 4. 검증 결과

## 5. 설계 문서와의 일치 여부

## 6. 남은 이슈

## 7. 다음 Phase 제안
```

---

## 12.17 우선 구현 전략

초기에는 LLM과 PostgreSQL에 의존하지 않는 구조를 먼저 완성한다.

권장 순서:

1. Rule Engine으로 확정 가능한 검토를 먼저 구현
2. Local Retrieval로 문서 검색 흐름 검증
3. Review Object API로 End-to-End skeleton 완성
4. 그 뒤 PostgreSQL과 LLM provider를 붙임
5. 마지막에 Mock UI와 Rhino Plugin Skeleton을 연결

이 방식은 외부 서비스 연결이 늦어져도 핵심 Agent 구조가 먼저 동작하도록 보장한다.

---

## 12.18 최종 구현 목표

최종 MVP는 다음 흐름을 시연할 수 있어야 한다.

```text
W-012 회의실 벽체 선택
-> 객체 메타데이터 입력
-> Rule Engine이 재료 누락과 두께 검토 필요 탐지
-> RAG가 관련 시방서 검색
-> LLM 또는 fallback recommender가 추천과 경고 생성
-> 사용자가 재료와 두께를 수정 후 수용
-> Review Action 로그 저장
-> 전체 모델 QA에서 누락 객체 요약 확인
```

이 흐름이 구현되면, Material Insight AI는 단순 챗봇이 아니라 Rhino/CAD 객체 중심의 Human-in-the-loop AI Agent로 설명할 수 있다.
