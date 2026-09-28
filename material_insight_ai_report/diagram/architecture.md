# P6 Schedule Recovery Copilot — 아키텍처 설계도

## 1. 전체 시스템 아키텍처

```mermaid
flowchart TB
    subgraph FE["Frontend (React + Vite + TS)"]
        UI["4단계 워크플로 UI<br/>프로젝트 → CSV Import → 문서 업로드 → 이슈 분석<br/>+ 데모 원클릭 로더"]
    end

    subgraph BE["Backend (FastAPI · Python 3.12)"]
        API["REST API 15개 엔드포인트"]

        subgraph ORCH["Analysis Orchestrator (상태 머신 = LangGraph StateGraph 패턴)"]
            GIN["① 입력 가드레일<br/>길이·프롬프트 인젝션 검사"]
            SRCH["② 후보/근거 검색<br/>Activity: pg_trgm(어휘)<br/>문서: pgvector(벡터)"]
            MAP["③ Issue Mapping Agent<br/>(vLLM Gemma)"]
            GOUT1["④ 출력 가드레일<br/>계산 금지 필드 차단"]
            HITL{"⑤ HITL 게이트<br/>conf≥0.85 & 격차≥0.10<br/>& 미완료 & 실존"}
            WAIT["NEEDS_ACTIVITY_SELECTION<br/>(사람 선택 대기 = interrupt)"]
            CPM1["⑥ CPM 엔진 (NetworkX)<br/>baseline / impact 계산<br/>★ LLM 미개입"]
            PLAN["⑦ Recovery Planning Agent<br/>(OpenAI) — 정확히 3개 시나리오"]
            RV["⑧ Rule Validator<br/>Activity·근거 allowlist<br/>action 화이트리스트"]
            CPM2["⑨ CPM 엔진<br/>시나리오별 회복일수 재계산"]
            REV["⑩ Review Agent<br/>(vLLM → OpenAI fallback)"]
            RPT["⑪ Markdown 보고서<br/>+ 근거 chunk 인용 연결"]
        end
    end

    subgraph DB["PostgreSQL (+pgvector, +pg_trgm)"]
        T1["일정: projects · snapshots(불변)<br/>activities · relationships"]
        T2["RAG: knowledge_documents<br/>knowledge_chunks(vector 1536)"]
        T3["Trace: issues · analysis_runs ·<br/>activity_matches · scenario_runs ·<br/>agent_runs(원문 보존) · reports ·<br/>retrieval_runs"]
    end

    subgraph LLM["LLM Providers (역할 라우팅 + fallback)"]
        L1["OpenAI API<br/>(Planner · Embedding)"]
        L2["vLLM Gemma (사내)<br/>(Mapper · Reviewer)"]
    end

    HUMAN["👤 공정관리자<br/>최종 판단: 시나리오 채택 · P6 반영 ·<br/>안전/품질/비용 승인 · EOT"]

    UI --> API --> GIN --> SRCH --> MAP --> GOUT1 --> HITL
    HITL -- 미달 --> WAIT -. 사람 선택 후 재개 .-> CPM1
    HITL -- 충족 --> CPM1 --> PLAN --> RV --> CPM2 --> REV --> RPT
    SRCH <--> DB
    ORCH <--> DB
    MAP & PLAN & REV <--> LLM
    RPT --> HUMAN
    WAIT --> HUMAN

    style CPM1 fill:#1a4731,color:#fff
    style CPM2 fill:#1a4731,color:#fff
    style GIN fill:#7c2d12,color:#fff
    style GOUT1 fill:#7c2d12,color:#fff
    style RV fill:#7c2d12,color:#fff
    style HITL fill:#78350f,color:#fff
    style HUMAN fill:#1e3a8a,color:#fff
```

- **초록** = 결정론적 계산(LLM 배제) · **적색** = 가드레일/검증 계층 · **황색** = Human-in-the-loop 분기 · **청색** = 사람의 최종 판단

## 2. 업무 흐름도 (사용자 관점)

```mermaid
sequenceDiagram
    actor U as 공정관리자
    participant C as Copilot
    participant E as CPM 엔진
    participant D as 문서저장소(RAG)

    U->>C: "A동 12층 커튼월 자재 10일 지연" (자연어)
    C->>C: 입력 가드레일 통과
    C->>D: 근거 문서 검색 (top20→θ0.35→boost→top8)
    D-->>C: 지연통보서·회의록·시공계획서 chunk
    C->>C: Mapper: 구조화 + 후보 재순위 (설치 0.95 / 납품 0.85)
    C-->>U: 격차 0.10 미만 → 후보 목록 제시 (자동선택 거부)
    U->>C: A1050(설치) 선택 ← 도메인 판단
    C->>E: baseline / impact CPM
    E-->>C: 68일 → 78일 (+10일, Critical)
    C->>C: Planner: 복구안 3개 제안 (근거 인용)
    C->>E: 시나리오별 회복일수 재계산
    E-->>C: +10일 / +6일 / +5일 (결정론)
    C->>C: Rule Validator + Reviewer(안전승인 경고)
    C-->>U: 근거 인용 연결된 Markdown 보고서
    U->>U: 시나리오 채택·상신 (사람 최종 판단)
```

## 3. 텍스트 폴백 (mermaid 미지원 환경용)

```text
사용자(자연어 이슈)
  → [입력 가드레일] → Activity 검색(pg_trgm) + RAG 검색(pgvector)
  → [Mapper·vLLM] → [출력 가드레일]
  → [HITL 게이트] ─ 미달 → NEEDS_ACTIVITY_SELECTION → 사람 선택 → 재개
  → [CPM 엔진] baseline/impact  (LLM 미개입 · 초록)
  → [Planner·OpenAI] 3개 시나리오 → [출력 가드레일] → [Rule Validator]
  → [CPM 엔진] 회복일수 재계산 → [Reviewer·vLLM→OpenAI]
  → Markdown 보고서(근거 인용) → 👤 사람 최종 판단
  (전 과정 trace: PostgreSQL 13개 테이블)
```
