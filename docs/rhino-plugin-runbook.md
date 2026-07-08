# Rhino Plugin Runbook

이 문서는 Rhino에서 Material Insight plugin을 로드하고 객체 검토를 실행하는 절차를 정리한다.

## 1. Backend 실행

먼저 FastAPI backend를 실행한다.

```powershell
cd C:\Users\user\Documents\Codex\2026-07-08\c-users-user-desktop-material-insight\backend
python -m uvicorn app.main:app --reload
```

정상 실행 후 Rhino plugin이 객체를 검토하면 backend 터미널에 다음과 같은 로그가 표시된다.

```text
POST /api/v1/review-object HTTP/1.1" 200 OK
```

## 2. Rhino Plugin 빌드

```powershell
cd C:\Users\user\Documents\Codex\2026-07-08\c-users-user-desktop-material-insight\plugin\RhinoMaterialInsight
dotnet build
```

빌드 후 plugin 파일은 다음 위치에 생성된다.

```text
C:\Users\user\Documents\Codex\2026-07-08\c-users-user-desktop-material-insight\plugin\RhinoMaterialInsight\bin\Debug\net7.0-windows\RhinoMaterialInsight.rhp
```

## 3. Rhino에서 Plugin 로드

Rhino 응용프로그램을 실행한다.

Rhino 명령창에 입력한다.

```text
PlugInManager
```

Plugin Manager 창에서 다음 순서로 진행한다.

```text
Install 클릭
RhinoMaterialInsight.rhp 선택
```

또는 `.rhp` 파일을 Rhino 창에 드래그 앤 드롭해도 된다.

## 4. 테스트 객체 생성

Rhino 명령창에 입력한다.

```text
_Box
```

박스를 끝까지 생성한다.

1. 첫 점 클릭
2. 반대 점 클릭
3. 높이 지정
4. 객체가 실제로 화면에 생성되었는지 확인

객체 생성 중인 상태에서는 plugin 검토를 실행할 수 없다. 생성이 끝나면 `Esc`를 눌러 현재 명령을 종료한다.

## 5. Material Insight 명령 실행

Rhino 명령창에 정확히 입력한다.

```text
MaterialInsightReview
```

아래 문구가 표시되면 plugin 명령이 실행된 상태다.

```text
Select an object to review with Material Insight:
```

그 상태에서 생성한 객체를 클릭하고 `Enter`를 누른다.

## 6. 정상 실행 확인

Rhino command line에 다음과 비슷한 출력이 표시되면 plugin이 Rhino 객체를 읽은 것이다.

```text
Material Insight object: ..., type=missing, space=missing, material=missing
Material Insight: sending review request to backend in background...
Material Insight: backend response received.
```

Backend 터미널에는 다음 로그가 표시되어야 한다.

```text
POST /api/v1/review-object HTTP/1.1" 200 OK
```

이 상태면 Rhino Plugin에서 backend `/api/v1/review-object` 호출까지 성공한 것이다.

## 7. UserText가 없는 객체의 의미

기본 Box 객체는 일반 Rhino geometry이므로 다음 값이 없다.

- `object_type`
- `space_type`
- `material`
- `thickness_mm`

그래서 처음에는 다음처럼 표시될 수 있다.

```text
type=missing, space=missing, material=missing
```

이는 plugin 실패가 아니라 Rhino 객체에 업무용 UserText가 아직 없다는 뜻이다.

## 8. 속성 있는 객체로 테스트

더 실제 검토에 가깝게 테스트하려면 객체에 UserText를 추가한다.

1. 박스 선택
2. Rhino 명령창에 입력

```text
SetUserText
```

아래 key/value를 추가한다.

```text
object_type
interior_wall
```

```text
space_type
meeting_room
```

```text
thickness_mm
75
```

```text
review_status
pending
```

```text
acoustic_required
true
```

이후 다시 실행한다.

```text
MaterialInsightReview
```

정상이라면 Rhino 출력이 다음 방향으로 바뀐다.

```text
type=interior_wall, space=meeting_room, material=missing
```

이 상태면 Rhino Plugin, backend API, Rule/RAG/Recommendation 흐름이 연결된 것이다.

## 9. 멈춤처럼 보일 때

Rhino가 멈춘 것처럼 보이면 먼저 최신 plugin을 다시 빌드하고 Rhino를 재시작했는지 확인한다. 최신 plugin은 backend 통신을 백그라운드에서 수행하므로, API 응답을 기다리는 동안 Rhino UI가 계속 반응해야 한다.

Plugin API client는 8초 timeout을 사용한다. backend가 꺼져 있거나 응답하지 않으면 잠시 후 Rhino command line에 오류가 표시된다.

확인할 것:

- backend가 실행 중인가
- backend 주소가 `http://localhost:8000`인가
- Rhino에서 객체 생성이 완료된 상태인가
- `MaterialInsightReview` 명령어 철자가 정확한가

정확한 명령어:

```text
MaterialInsightReview
```
