# Phase 9B. Rhino Payload Contract Test Report

## 1. 목표

Rhino Plugin skeleton이 생성할 `review-object` payload와 backend `ReviewObjectRequest` schema가 실제로 맞는지 테스트로 고정한다.

이 phase는 Rhino 실행이나 `dotnet build` 없이도 진행 가능한 contract 검증 단계다.

## 2. 작업 내용

### 2.1 Plugin canonical sample 추가

다음 파일을 추가했다.

```text
plugin/RhinoMaterialInsight/Samples/review_object_payload.json
```

이 샘플은 Phase 9의 `MaterialInsightObjectInspector`가 생성해야 하는 payload 형태를 나타낸다.

### 2.2 Backend mirror sample 업데이트

다음 파일을 plugin sample과 같은 계약으로 업데이트했다.

```text
backend/data/rhino_plugin_review_object_payload.json
```

주요 반영 사항:

- `bbox.min`, `bbox.max` 예시 추가
- `layer`를 nested layer 예시인 `A-WALL::PARTITION`으로 변경
- `user_attributes.material_insight_object_id` 추가

### 2.3 Contract 문서 추가

다음 문서를 추가했다.

```text
docs/rhino-payload-contract.md
```

문서에는 다음 내용을 명시했다.

- 이 payload는 Rhino 공식 JSON이 아님
- Material Insight 내부 `review-object` API 계약임
- 필수 필드와 optional 필드
- Rhino UserString 기반 `thickness_mm` string 허용
- unknown field는 backend에서 거부됨
- canonical sample 위치

### 2.4 Backend contract test 확장

`backend/app/tests/test_review_object_contract.py`를 확장했다.

검증 내용:

- backend sample payload validation
- plugin sample payload validation
- `thickness_mm` numeric string coercion
- 최소 payload에서 optional field 처리
- unknown contract field reject
- C# DTO의 `JsonPropertyName`이 backend snake_case field와 일치하는지 확인

### 2.5 API-level contract test 추가

`backend/app/tests/test_review_api.py`에 plugin sample이 실제 `/api/v1/review-object` API를 통과하는지 확인하는 테스트를 추가했다.

## 3. 설계 문서 일치성 검토

### 일치한 점

- `10-rhino-plugin-access.md`의 “Rhino 공식 JSON이 아니라 Material Insight 내부 API 계약” 설명을 유지했다.
- Plugin sample과 backend sample이 같은 payload 구조를 공유한다.
- `object_id`, `object_type`, `space_type`, `material`, `thickness_mm`, `geometry`, `user_attributes` 핵심 필드를 검증한다.
- backend schema가 unknown field를 거부하므로 payload drift를 조기에 잡을 수 있다.
- Rhino UserString 특성을 고려해 `thickness_mm` string 입력도 backend에서 허용한다.

### 의도적으로 남긴 범위

- 실제 Rhino object에서 C# inspector가 payload를 생성하는 runtime test는 Rhino 설치 이후 수행한다.
- `dotnet build` 검증은 .NET SDK 설치 이후 수행한다.
- 실제 Rhino panel button과 review action submit UI는 Phase 10 이후 확장 후보로 남긴다.

## 4. 검증 방법

```powershell
cd backend
pytest app/tests/test_review_object_contract.py app/tests/test_review_api.py
```

## 5. 검증 결과

현재 Codex 실행 세션에서는 Python 실행 파일을 사용할 수 없어 pytest를 직접 실행하지 못했다.

사용자 로컬 Python 3.12 환경에서 위 명령으로 검증하면 된다.

## 6. 산출물

- `plugin/RhinoMaterialInsight/Samples/review_object_payload.json`
- `docs/rhino-payload-contract.md`
- `backend/data/rhino_plugin_review_object_payload.json`
- `backend/app/tests/test_review_object_contract.py`
- `backend/app/tests/test_review_api.py`
- `backend/README.md`
- `README.md`

## 7. 다음 단계

다음 phase는 `Phase 10. 통합 테스트 + 발표용 데모`다.

Phase 10에서는 지금까지 구현한 backend, Mock Plugin UI, pgvector 전환 구조, Rhino Plugin skeleton, payload contract를 최종 데모 흐름으로 묶고 설계-구현 매핑표를 정리한다.
