# Phase 05 Report: Multi-Provider LLM Recommendation

## 1. Phase 목표

Phase 5의 목표는 Phase 4에서 구현한 fallback recommendation 위에 교체 가능한 LLM provider 계층을 붙이는 것이다.

이번 phase에서는 OpenAI API, vLLM, mock provider를 같은 interface로 다룰 수 있게 만들고, LLM이 실패하거나 안전 규칙을 어기더라도 Rule Engine과 Retrieval 결과가 유지되도록 했다.

## 2. 수행 작업

- `LLMClient` provider interface를 추가했다.
- `MockLLMClient`를 추가해 기본 테스트와 오프라인 데모가 기존 fallback과 동일하게 동작하도록 했다.
- `OpenAIResponsesClient`를 추가했다.
- `VLLMChatCompletionsClient`를 추가했다.
- LLM system prompt 파일을 추가했다.
- Orchestrator가 fallback recommendation을 먼저 만든 뒤 LLM provider를 호출하도록 변경했다.
- LLM 결과가 오더라도 `recommendation_id`, `object_id`, `status`, `severity`, `detected_issues`, `required_action`, `sources`는 fallback 기준으로 다시 고정했다.
- LLM 호출 실패 시 fallback recommendation을 반환하고 disclaimer에 실패 사유를 남기도록 했다.
- `httpx`를 runtime dependency로 이동했다.
- Phase 5 테스트를 추가했다.

## 3. 생성/수정 파일

| 파일 | 설명 |
|---|---|
| `backend/app/services/llm_client.py` | mock/openai/vllm provider interface 및 구현 |
| `backend/app/prompts/recommendation_system.md` | LLM system prompt |
| `backend/app/services/recommendation_orchestrator.py` | fallback -> LLM -> constraint -> fallback-on-failure 흐름 |
| `backend/app/tests/test_llm_client.py` | LLM provider factory와 mock provider 테스트 |
| `backend/app/tests/test_recommendation_orchestrator.py` | LLM softening 방지 및 fallback 테스트 추가 |
| `backend/pyproject.toml` | `httpx` runtime dependency 반영 |
| `backend/README.md` | Phase 5 실행 및 provider 설정 안내 |
| `README.md` | 완료 phase와 다음 phase 업데이트 |
| `reports/phase-05-llm-recommendation-report.md` | Phase 5 작업 보고서 |

## 4. 검증 결과

작성한 테스트:

```powershell
pytest app/tests/test_llm_client.py app/tests/test_recommendation_orchestrator.py app/tests/test_review_api.py
```

테스트 기대값:

- 알 수 없는 provider는 `LLMClientError`를 발생시킨다.
- 기본 `mock` provider는 Phase 4 fallback 결과를 보존한다.
- LLM이 rule issue를 지우거나 status를 낮춰도 orchestrator가 protected field를 fallback 기준으로 복구한다.
- LLM provider 실패 시 API는 실패하지 않고 fallback result를 반환한다.

Codex 셸에서는 이전과 같이 사용자 Python 3.12 실행 권한 문제로 pytest를 직접 실행하지 못할 수 있다. 사용자 venv에서 위 명령으로 검증하면 된다.

## 5. 설계 문서와의 일치 여부

| 설계 문서 | 요구 사항 | 구현 반영 |
|---|---|---|
| `material_insight_implementation_guide.md` Step 6 | system prompt 작성 | `recommendation_system.md` 추가 |
| `material_insight_implementation_guide.md` Step 6 | JSON schema 출력 강제 | OpenAI Responses JSON schema, vLLM JSON object 요청 |
| `material_insight_implementation_guide.md` Step 6 | 실패 시 fallback 구현 | provider exception 시 fallback 반환 |
| `docs/12-implementation-phase-roadmap.md` Phase 5 | OpenAI/vLLM/mock provider 구조 | `build_llm_client()` 구현 |
| `docs/model-selection.md` | OpenAI 기본, Qwen 27B local fallback | `.env.example` 및 settings 구조와 일치 |

### 일치한 부분

- LLM은 Rule Engine 결과를 삭제하거나 완화할 수 없다.
- sources가 없을 때 confidence가 fallback보다 높아지지 않도록 제한했다.
- OpenAI는 API key와 model만 사용한다.
- vLLM은 `qwen-27b`, `gemma-4b` 중 선택 가능한 local provider로 둔다.
- provider 실패 시 Phase 4 fallback recommendation을 유지한다.

### 의도적으로 아직 구현하지 않은 부분

- 실제 OpenAI/vLLM 네트워크 호출 테스트는 API key와 vLLM server가 필요하므로 자동 테스트에 넣지 않았다.
- prompt 품질 튜닝과 평가셋은 Phase 10 통합 검증에서 보강한다.

## 6. 남은 이슈

- 사용자 환경에서 OpenAI API key 또는 vLLM server를 설정한 뒤 실제 provider smoke test를 수행해야 한다.
- OpenAI structured output schema가 실제 API에서 거부되는 경우를 대비해 Phase 5 보강에서 schema 축소 fallback을 둘 수 있다.

## 7. 다음 Phase 제안

다음 phase는 **Phase 6. Review Action Logging**이다.

Phase 6에서 진행할 작업:

1. `/api/v1/review-actions` 구현
2. `ReviewActionRequest`를 DB record로 저장
3. recommendation id, object id, user id, action, edited values, reason, sources 기록
4. 사용자 승인 없이 Rhino 객체가 자동 수정되지 않는 구조 유지
