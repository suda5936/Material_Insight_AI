# Design Implementation Mapping

이 문서는 설계 문서의 주요 요구사항과 실제 구현 파일의 대응 관계를 정리한다.

## 1. 핵심 설계 원칙

| 설계 원칙 | 구현 반영 | 주요 파일 |
|---|---|---|
| Rhino/CAD 객체 중심 검토 | `ReviewObjectRequest`와 `DesignObjectInput`을 중심 schema로 고정 | `backend/app/models/object.py` |
| Rule Engine 우선 실행 | 추천 전 `RuleEngine.evaluate()` 실행 | `backend/app/services/rule_engine.py`, `backend/app/services/recommendation_orchestrator.py` |
| Retrieval은 항상 실행 | Rule 결과 이후 retriever가 항상 호출됨 | `backend/app/services/recommendation_orchestrator.py` |
| Sources 채택은 threshold 기반 | `search_relevant()`로 score threshold 통과 문서만 채택 | `backend/app/services/local_retriever.py`, `backend/app/services/pgvector_retriever.py` |
| 근거 없는 확정 추천 금지 | sources가 없으면 confidence 낮춤, disclaimer 추가 | `backend/app/services/recommendation_orchestrator.py` |
| LLM이 Rule 결과를 완화하지 않음 | LLM 출력의 protected fields를 fallback/rule 결과로 덮어씀 | `backend/app/services/recommendation_orchestrator.py` |
| Human-in-the-loop | 사용자 action을 별도 API로 저장, 자동 Rhino 수정 금지 | `backend/app/api/routes_actions.py`, `backend/app/services/review_logger.py` |
| 실제 Rhino 연결 가능성 | C# plugin skeleton과 `.rhp` 빌드/로드 흐름 제공 | `plugin/RhinoMaterialInsight` |
| Rhino payload는 내부 API 계약 | 공식 Rhino JSON이 아닌 Material Insight payload로 문서화/테스트 | `docs/rhino-payload-contract.md`, `backend/app/tests/test_review_object_contract.py` |

## 2. 설계 문서별 매핑

| 설계 문서 | 요구사항 | 구현 |
|---|---|---|
| `05-mvp-design.md` | 객체 선택, 속성 추출, Rule/RAG/LLM, 사용자 판단 | Backend API, Mock UI, Rhino plugin skeleton |
| `06-architecture.md` | Rhino Plugin, Object Inspector, Rule Engine, RAG, LLM, Logging 분리 | `plugin/RhinoMaterialInsight`, `backend/app/services/*` |
| `07-rag-hitl.md` | 근거 기반 추천과 HITL 안전장치 | threshold sources, review-actions API |
| `08-demo.md` | 객체 정보, AI 검토 결과, 사용자 액션, 전체 QA 화면 | `frontend/mock-plugin-ui` |
| `10-rhino-plugin-access.md` | RhinoCommon으로 객체 속성 추출, 내부 payload 변환 | `MaterialInsightObjectInspector.cs` |
| `11-processing-flow-diagram.md` | Rule -> Retrieval -> threshold -> Recommendation -> Log | `RecommendationOrchestrator`, API routes |
| `12-implementation-phase-roadmap.md` | Phase별 구현과 report 작성 | `reports/phase-*.md` |

## 3. API 구현 매핑

| API | 목적 | 구현 파일 | 테스트 |
|---|---|---|---|
| `GET /health` | backend 상태 확인 | `backend/app/api/routes_health.py` | `backend/app/tests/test_health.py` |
| `POST /api/v1/review-object` | 단일 객체 검토 | `backend/app/api/routes_review.py` | `backend/app/tests/test_review_api.py` |
| `POST /api/v1/review-actions` | 사용자 판단 저장 | `backend/app/api/routes_actions.py` | `backend/app/tests/test_review_actions_api.py` |
| `POST /api/v1/scan-model` | 전체 모델 QA | `backend/app/api/routes_scan.py` | `backend/app/tests/test_scan_api.py` |

## 4. 데이터 계층 매핑

| 데이터 | 목적 | 파일 |
|---|---|---|
| Sample Rhino payload | Rhino plugin/backend 계약 검증 | `backend/data/rhino_plugin_review_object_payload.json`, `plugin/RhinoMaterialInsight/Samples/review_object_payload.json` |
| Sample objects | Rule/Retrieval/Scan 테스트 | `data/sample_objects/*.json` |
| Rule YAML | 누락/위험 탐지 규칙 | `data/rules/material_insight_rules.yaml` |
| Sample documents | Local Retrieval 근거 문서 | `data/documents/**/*` |
| Material catalog | RAG/vector DB 재료 지식 | `data/materials/material_catalog.yaml` |
| RAG chunks | pgvector 적재 입력 | `data/processed/rag_chunks.jsonl` |

## 5. Rhino 구현 매핑

| Rhino 책임 | 구현 파일 | 설명 |
|---|---|---|
| Plugin entry | `RhinoMaterialInsightPlugin.cs` | Rhino plugin entry |
| 명령 실행 | `Commands/MaterialInsightReviewCommand.cs` | 객체 선택, backend 요청, 결과 표시 |
| 객체 추출 | `Services/MaterialInsightObjectInspector.cs` | RhinoObject를 review payload로 변환 |
| API 호출 | `Services/MaterialInsightApiClient.cs` | FastAPI backend 호출, 8초 timeout |
| 사용자 승인 후 업데이트 | `Services/MaterialInsightObjectUpdater.cs` | UserString 수정 로직 분리 |
| 결과 표시 placeholder | `Panels/MaterialInsightReviewPanel.cs` | Rhino command line 출력 |

## 6. 현재 검증 상태

| 항목 | 상태 |
|---|---|
| Backend unit/API tests | 사용자 환경에서 개별 phase별 통과 확인, 일부 신규 test는 로컬 재실행 필요 |
| Mock Plugin UI | 정적 JS 구문 검사 통과, backend API 연결 구조 구현 |
| Rhino plugin build | 사용자 로컬에서 `dotnet restore/build` 성공 |
| Rhino plugin API call | 실제 Rhino에서 객체 선택 후 `/api/v1/review-object` 200 OK 확인 |
| Rhino UI freeze 대응 | backend 통신을 background async로 변경, Rhino 재빌드/재로드 필요 |
| pgvector ingest | 구조와 script 구현, 실제 PostgreSQL 적재는 환경 준비 후 실행 |

## 7. 남은 한계

- Rhino dock panel UI는 placeholder 수준이다.
- 실제 Rhino 객체에 추천값을 반영하는 버튼 UI는 아직 없다.
- pgvector는 적재 script와 retriever 구조까지 구현했고, 실제 운영 데이터 검증은 남아 있다.
- OpenAI/vLLM 실제 호출은 설정으로 가능하지만, 기본 테스트는 `mock` provider 중심이다.
- 구조, 내화, 법규 판단은 최종 판정하지 않고 전문가 검토로 넘긴다.
