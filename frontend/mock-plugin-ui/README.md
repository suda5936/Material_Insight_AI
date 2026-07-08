# Material Insight Mock Plugin UI

Rhino 없이 backend API 흐름을 시연하기 위한 정적 UI다.

## 실행

Backend를 먼저 실행한다.

```powershell
cd backend
uvicorn app.main:app --reload
```

UI는 정적 서버로 실행한다.

```powershell
cd frontend/mock-plugin-ui
python -m http.server 8001
```

브라우저에서 아래 주소를 연다.

```text
http://localhost:8001
```

## 연결 API

- `GET /health`
- `POST /api/v1/review-object`
- `GET /api/v1/latest-review`
- `POST /api/v1/review-actions`
- `POST /api/v1/scan-model`

## 데모 흐름

1. 객체 목록에서 `W-012` 선택
2. `AI 검토` 실행
3. 검토 결과와 근거 문서 확인
4. `수정 저장` 또는 `전문가 검토` 액션 저장
5. `전체 검사`로 모델 QA 목록 확인

## Rhino 연동 결과 표시

Rhino Plugin에서 `MaterialInsightReview`를 실행하면 backend의 최신 review 결과가 갱신된다.

Mock UI는 4초마다 `GET /api/v1/latest-review`를 확인하고, 새 결과가 있으면 AI 검토 결과 패널에 표시한다.

수동으로 확인하려면 `Rhino 결과 불러오기` 버튼을 누른다.
