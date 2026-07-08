# 11. Material Insight AI 처리 흐름 다이어그램

## 11.1 전체 처리 흐름

```mermaid
flowchart LR
    A[Rhino 객체 선택]
    --> B[Plugin: 객체 속성 추출]
    --> C[Material Insight Payload 생성]
    --> D[FastAPI Review API]
    --> E[Object Normalizer]
    --> F[Rule Engine]
    --> G[RAG Retriever 항상 실행]
    --> H{관련도 threshold 통과?}
    H -->|Yes| J[관련 문서와 출처 채택]
    H -->|No| I[근거 없음으로 규칙 결과 정리]
    I --> K[Recommendation Orchestrator]
    J --> K
    F --> K
    K --> L[LLM Recommendation Layer]
    L --> M[구조화된 추천 결과]
    M --> N[Rhino Side Panel 표시]
    N --> O{사용자 판단}
    O -->|수용| P[승인값 반영]
    O -->|수정| Q[수정값 반영]
    O -->|보류| R[미결 상태 저장]
    O -->|무시| S[무시 사유 저장]
    O -->|전문가 검토 요청| T[검토 요청 생성]
    P --> U[Review Log 저장]
    Q --> U
    R --> U
    S --> U
    T --> U
```

---

## 11.2 Rhino Plugin 내부 흐름

```mermaid
flowchart TD
    A[사용자 명령 실행: MaterialInsightReview]
    --> B[검토할 객체 선택]
    --> C[RhinoObject 획득]
    --> D[ObjectAttributes 읽기]
    --> E[Geometry Summary 계산]
    --> F[UserString/UserDictionary 읽기]
    --> G[Layer/Material/Name 해석]
    --> H[Project Context 결합]
    --> I[Review API Payload 생성]
    --> J[FastAPI로 POST 요청]
    --> K[Recommendation 응답 수신]
    --> L[Side Panel에 결과 렌더링]
    --> M{사용자 액션}
    M -->|승인 또는 수정| N[객체 UserString 업데이트]
    M -->|보류 또는 무시| O[객체 상태 유지]
    M -->|전문가 검토 요청| P[검토 요청 상태 저장]
    N --> Q[Rhino View 갱신]
    O --> Q
    P --> Q
```

---

## 11.3 백엔드 Agent 처리 흐름

```mermaid
flowchart TD
    A[POST /api/v1/review-object]
    --> B[Request Schema Validation]
    --> C[Object Normalization]
    --> D[Rule Engine 실행]
    --> E[RuleResult 생성]
    --> F[검색 질의 생성]
    --> G[문서 메타데이터 필터]
    --> H[Vector 또는 Local Search 항상 실행]
    --> I[Retrieved Document Candidates]
    --> J{score threshold 통과?}
    J -->|Yes| K[Sources로 채택]
    J -->|No| L[근거 없음 상태 설정]
    K --> M[LLM Prompt 구성]
    L --> M
    E --> M
    M --> N[LLM JSON Recommendation]
    N --> O[Schema Validation]
    O --> P{검증 성공?}
    P -->|Yes| Q[Recommendation 저장]
    P -->|No| R[Fallback Result 생성]
    Q --> S[Response 반환]
    R --> S
```

---

## 11.4 Human-in-the-loop 흐름

```mermaid
flowchart LR
    A[AI 추천 및 경고]
    --> B[설계자 검토]
    B --> C{위험 수준}
    C -->|낮음| D[설계자 직접 수용 또는 수정]
    C -->|중간| E[시니어 검토 권장]
    C -->|높음| F[전문가 검토 필수]
    C -->|매우 높음| G[AI 자동 처리 금지]
    D --> H[사용자 액션 저장]
    E --> H
    F --> H
    G --> H
    H --> I[객체 검토 상태 업데이트]
    H --> J[Review Log 저장]
```

---

## 11.5 데이터 흐름 상세

```mermaid
sequenceDiagram
    participant U as Rhino 사용자
    participant P as Rhino Plugin
    participant A as FastAPI Backend
    participant R as Rule Engine
    participant V as Vector DB
    participant L as LLM
    participant D as Database

    U->>P: 객체 선택
    P->>P: ObjectAttributes, Geometry, UserString 추출
    P->>A: POST /api/v1/review-object
    A->>R: 규칙 검사 요청
    R-->>A: RuleResult 반환
    A->>V: 관련 문서 검색
    V-->>A: RetrievedDocument 반환
    A->>L: 객체 정보 + 규칙 결과 + 검색 문서 전달
    L-->>A: 추천/경고 JSON 반환
    A->>D: Recommendation 저장
    A-->>P: 검토 결과 반환
    P-->>U: Side Panel에 결과 표시
    U->>P: 수용/수정/보류/무시 선택
    P->>A: POST /api/v1/review-actions
    A->>D: ReviewAction 저장
    alt 승인 또는 수정
        P->>P: Rhino 객체 UserString 업데이트
    else 보류 또는 무시
        P->>P: 검토 상태만 기록
    end
```

---

## 11.6 예외 처리 흐름

```mermaid
flowchart TD
    A[객체 검토 요청]
    --> B{객체 유형과 공간 용도 존재?}
    B -->|No| C[추가 입력 요청]
    B -->|Yes| D[Rule Engine 실행]
    D --> E{RAG 검색 결과 존재?}
    E -->|No| F[근거 없음 표시 및 추천 제한]
    E -->|Yes| G[LLM 추천 생성]
    G --> H{LLM 응답 성공?}
    H -->|No| I[Rule Engine 결과만 표시]
    H -->|Yes| J[추천 결과 표시]
    J --> K{고위험 항목 포함?}
    K -->|Yes| L[전문가 검토 요청으로 전환]
    K -->|No| M[설계자 검토]
```

---

## 11.7 발표용 핵심 흐름

발표에서는 아래 문장과 함께 다이어그램을 설명하면 된다.

> Material Insight AI는 Rhino 객체를 직접 수정하는 자동 설계 도구가 아니라, 객체 정보를 읽고 규칙 검사와 문서 검색을 수행한 뒤, 근거가 포함된 추천을 Rhino 패널에 표시하는 Human-in-the-loop Agent다.

발표용 6단계:

1. Rhino에서 회의실 벽체 선택
2. Plugin이 객체 ID, 레이어, 재료, 두께, 공간 용도 추출
3. Rule Engine이 재료 누락과 두께 검토 필요 탐지
4. RAG는 항상 실행하고 score threshold를 통과한 시방서와 카탈로그만 근거로 채택
5. LLM이 추천과 경고를 근거와 함께 정리
6. 설계자가 수정 후 수용하고 로그 저장

---

## 11.8 구현 파일 매핑

| 처리 단계 | 구현 위치 예시 |
|---|---|
| Rhino 객체 선택 | `plugin/RhinoMaterialInsight/Commands/ReviewObjectCommand.cs` |
| 객체 속성 추출 | `plugin/RhinoMaterialInsight/Services/ObjectInspector.cs` |
| API 호출 | `plugin/RhinoMaterialInsight/Services/AgentApiClient.cs` |
| 결과 패널 | `plugin/RhinoMaterialInsight/Panels/ReviewPanel.cs` |
| Review API | `backend/app/api/routes_review.py` |
| 객체 정규화 | `backend/app/services/object_normalizer.py` |
| Rule Engine | `backend/app/services/rule_engine.py` |
| RAG 검색 | `backend/app/services/rag_retriever.py` |
| LLM 추천 | `backend/app/services/recommendation_orchestrator.py` |
| 사용자 액션 저장 | `backend/app/api/routes_actions.py` |
| 로그 저장 | `backend/app/services/review_logger.py` |

---

## 11.9 최종 요약 다이어그램

```mermaid
flowchart LR
    Rhino[Rhino Plugin]
    --> Extract[Object Metadata Extract]
    --> API[FastAPI Agent API]
    --> Rule[Rule Engine]
    --> RAG[RAG Search]
    --> LLM[LLM Recommendation]
    --> Panel[Rhino Review Panel]
    --> HITL[Designer Approval]
    --> Log[Review Log]

    HITL -->|Approved| Update[Update Rhino UserString]
    HITL -->|Hold/Ignore| Keep[Keep Object, Save Reason]
    HITL -->|High Risk| Expert[Expert Review Request]
```
