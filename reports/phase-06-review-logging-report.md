# Phase 06 Report: Review Action Logging

## 1. Phase 목표

Phase 6의 목표는 Human-in-the-loop 흐름에서 사용자의 수용, 수정, 보류, 무시, 전문가 검토 요청을 저장하는 것이다.

이번 phase에서는 `/api/v1/review-actions` API와 DB 저장 서비스를 구현했다. 중요한 제약은 AI 추천이 사용자 승인 없이 Rhino 객체에 자동 반영되지 않고, 사용자의 결정만 로그로 남기는 것이다.

## 2. 수행 작업

- `ReviewActionResponse` 모델을 추가했다.
- `ReviewActionRequest`의 `object_id`, `sources` 필드를 Phase 6 저장 흐름에 사용했다.
- `review_logger.py` 서비스를 추가해 `ReviewActionRecord`를 저장하도록 했다.
- `/api/v1/review-actions` API route를 추가했다.
- FastAPI app에 review action router를 등록했다.
- review action 저장 단위 테스트를 추가했다.
- review action API 테스트를 추가했다.
- backend README에 Phase 6 검증 명령을 추가했다.

## 3. 생성/수정 파일

| 파일 | 설명 |
|---|---|
| `backend/app/models/review_action.py` | `ReviewActionResponse` 추가 |
| `backend/app/services/review_logger.py` | Review Action DB 저장 서비스 |
| `backend/app/api/routes_actions.py` | `POST /api/v1/review-actions` API |
| `backend/app/main.py` | actions router 등록 |
| `backend/app/tests/test_review_logger.py` | 저장 서비스 단위 테스트 |
| `backend/app/tests/test_review_actions_api.py` | API 테스트 |
| `backend/README.md` | Phase 6 검증 안내 |
| `README.md` | 완료 phase와 다음 phase 업데이트 |
| `reports/phase-06-review-logging-report.md` | Phase 6 작업 보고서 |

## 4. 검증 결과

작성한 테스트:

```powershell
pytest app/tests/test_review_logger.py app/tests/test_review_actions_api.py
```

테스트 기대값:

- `save_review_action()`이 `ReviewActionRecord`를 DB에 저장한다.
- 저장 응답은 `review_action_id`, `status=saved`를 반환한다.
- `/api/v1/review-actions` 호출 시 200 응답을 반환한다.
- 수정값, 사유, 출처가 request payload로 전달 가능하다.

Codex 셸에서는 Python 3.12 실행 권한 문제로 pytest를 직접 실행하지 못할 수 있다. 사용자 venv에서 위 명령으로 검증하면 된다.

## 5. 설계 문서와의 일치 여부

| 설계 문서 | 요구 사항 | 구현 반영 |
|---|---|---|
| `material_insight_implementation_guide.md` Step 7 | 사용자 수용·수정·보류·무시·검토 요청 저장 | `ReviewActionRequest.action`과 `/review-actions` 구현 |
| `material_insight_implementation_guide.md` Step 7 | recommendation_id, object_id, user_id, action, edited_values, reason, sources, timestamp 저장 | `ReviewActionRecord`와 `payload.sources` 저장 |
| `material_insight_implementation_guide.md` 10.3 | `POST /api/v1/review-actions` response에 `review_action_id`, `status` 포함 | `ReviewActionResponse` 구현 |
| `docs/12-implementation-phase-roadmap.md` Phase 6 | PostgreSQL 또는 개발용 저장소 연결 | SQLAlchemy session 기반 저장 |

### 일치한 부분

- 사용자 action은 별도 로그로 저장된다.
- 수정값은 `edited_values`에 남긴다.
- 출처 문서는 `payload.sources`에 저장된다.
- Rhino 객체는 자동 수정하지 않는다.

### 의도적으로 아직 구현하지 않은 부분

- 저장된 action 조회 API는 아직 없다.
- recommendation 존재 여부를 DB에서 강제 검증하지 않는다. MVP에서는 mock/Rhino UI가 받은 `recommendation_id`를 그대로 저장한다.
- 실제 Rhino 객체 업데이트는 Phase 9 plugin skeleton에서 사용자 승인 이후 동작으로만 다룬다.

## 6. 남은 이슈

- Phase 8 Mock Plugin UI에서 수용/수정 버튼이 이 API를 호출하도록 연결해야 한다.
- Phase 10 통합 테스트에서 review action 로그 조회 또는 DB 확인 절차를 데모 문서에 넣는 것이 좋다.

## 7. 다음 Phase 제안

다음 phase는 **Phase 7. 전체 모델 QA API**다.

Phase 7에서 진행할 작업:

1. `/api/v1/scan-model` 구현
2. 객체 배열 입력 모델 정의
3. 각 객체에 Rule Engine 일괄 실행
4. severity별 정렬과 summary count 반환
5. 발표용 전체 모델 누락 검사 시나리오 준비
