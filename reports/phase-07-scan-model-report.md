# Phase 07 Report: 전체 모델 QA API

## 1. Phase 목표

Phase 7의 목표는 단일 객체 검토를 넘어 여러 객체를 한 번에 검사하고, 누락과 위험 항목을 우선순위 목록과 요약 카운트로 반환하는 것이다.

이번 phase에서는 `/api/v1/scan-model` API를 구현해 발표용 “전체 모델 누락 검사” 시나리오의 백엔드 흐름을 만들었다.

## 2. 수행 작업

- `ScanModelRequest`, `ScanObjectResult`, `ScanSummary`, `ScanModelResponse` 모델을 추가했다.
- `ModelScanner` 서비스를 추가했다.
- Rule Engine을 각 객체에 일괄 실행하도록 구성했다.
- required action, severity, issue count 기준으로 결과를 정렬했다.
- issue code별 count, severity별 count, required action별 count를 반환하도록 했다.
- `/api/v1/scan-model` API route를 추가했다.
- FastAPI app에 scan router를 등록했다.
- model scanner 단위 테스트와 API 테스트를 추가했다.
- README에 Phase 7 검증 명령을 추가했다.

## 3. 생성/수정 파일

| 파일 | 설명 |
|---|---|
| `backend/app/models/scan.py` | scan-model request/response schema |
| `backend/app/services/model_scanner.py` | 여러 객체 Rule Engine 일괄 검사 및 요약 |
| `backend/app/api/routes_scan.py` | `POST /api/v1/scan-model` API |
| `backend/app/main.py` | scan router 등록 |
| `backend/app/tests/test_model_scanner.py` | scanner 단위 테스트 |
| `backend/app/tests/test_scan_api.py` | scan-model API 테스트 |
| `backend/README.md` | Phase 7 검증 안내 |
| `README.md` | 완료 phase와 다음 phase 업데이트 |
| `reports/phase-07-scan-model-report.md` | Phase 7 작업 보고서 |

## 4. 검증 결과

작성한 테스트:

```powershell
pytest app/tests/test_model_scanner.py app/tests/test_scan_api.py
```

테스트 기대값:

- 여러 sample object를 한 번에 입력할 수 있다.
- `material_missing`, `expert_review_required` 등 issue code별 count가 반환된다.
- issue가 있는 객체 수가 집계된다.
- expert review 항목이 최상위에 오고, 그 다음 severity와 issue count 기준으로 정렬된다.
- `/api/v1/scan-model` 호출 시 summary와 results가 반환된다.

Codex 셸에서는 Python 3.12 실행 권한 문제로 pytest를 직접 실행하지 못할 수 있다. 사용자 venv에서 위 명령으로 검증하면 된다.

## 5. 설계 문서와의 일치 여부

| 설계 문서 | 요구 사항 | 구현 반영 |
|---|---|---|
| `material_insight_implementation_guide.md` Step 10 | 객체 배열 입력 | `ScanModelRequest.objects` |
| `material_insight_implementation_guide.md` Step 10 | 각 객체에 Rule Engine 실행 | `ModelScanner.scan()` |
| `material_insight_implementation_guide.md` Step 10 | severity별 정렬 | required action + severity rank + issue count 정렬 |
| `material_insight_implementation_guide.md` Step 10 | 요약 카운트 생성 | `ScanSummary` |
| `docs/12-implementation-phase-roadmap.md` Phase 7 | `/api/v1/scan-model` 구현 | `routes_scan.py` |

### 일치한 부분

- 전체 모델을 자동 설계하지 않고, 객체별 누락과 위험을 QA 목록으로 반환한다.
- Rule Engine 기반의 결정적 검사만 수행한다.
- LLM이나 RAG를 호출하지 않아 전체 스캔이 가볍고 예측 가능하다.
- 발표용 QA 목록에 필요한 issue count와 severity count를 제공한다.
- 전문가 검토 필요 항목은 정보 부족 항목보다 먼저 노출한다.

### 의도적으로 아직 구현하지 않은 부분

- RAG/LLM은 전체 모델 스캔에 연결하지 않았다. Phase 7의 목적은 누락/위험 탐지 요약이다.
- DB 저장은 하지 않는다. 필요한 경우 Phase 10 통합 단계에서 scan result 저장을 별도 결정한다.
- UI 표시는 Phase 8 Mock Plugin UI에서 구현한다.

## 6. 남은 이슈

- Mock Plugin UI에서 전체 모델 QA 목록을 이 API에 연결해야 한다.
- 발표 시 high severity와 expert review 항목이 먼저 보이도록 UI 정렬 표현을 맞춰야 한다.

## 7. 다음 Phase 제안

다음 phase는 **Phase 8. Mock Plugin UI**다.

Phase 8에서 진행할 작업:

1. 샘플 객체 선택 화면
2. 단일 객체 검토 결과 패널
3. sources 표시 패널
4. review action 버튼과 저장 호출
5. 전체 모델 QA 목록 화면
