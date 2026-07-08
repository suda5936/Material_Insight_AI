# Phase 9. Rhino Plugin Skeleton Report

## 1. 목표

실제 Rhino 연동 가능성을 코드 구조로 제시한다.

이번 phase는 완성된 Rhino UI plugin이 아니라, RhinoCommon 기반으로 어떤 객체 데이터를 읽고 backend API에 어떻게 전달할지 명확히 하는 skeleton 단계다.

## 2. 작업 내용

### 2.1 Rhino plugin project skeleton 추가

`plugin/RhinoMaterialInsight`에 C# project skeleton을 추가했다.

주요 파일:

- `RhinoMaterialInsight.csproj`
- `RhinoMaterialInsightPlugin.cs`
- `Commands/MaterialInsightReviewCommand.cs`
- `Models/MaterialInsightModels.cs`
- `Services/MaterialInsightObjectInspector.cs`
- `Services/MaterialInsightApiClient.cs`
- `Services/MaterialInsightObjectUpdater.cs`
- `Panels/MaterialInsightReviewPanel.cs`
- `README.md`

### 2.2 MaterialInsightReview command 추가

`MaterialInsightReviewCommand`는 다음 흐름을 코드로 표현한다.

1. Rhino 객체 선택
2. `MaterialInsightObjectInspector`로 review payload 생성
3. `/api/v1/review-object` 호출
4. 추천 결과 표시

### 2.3 Object Inspector 추가

`MaterialInsightObjectInspector`는 Rhino 객체를 Material Insight 내부 API 계약으로 변환한다.

RhinoCommon 접근 항목:

- `rhinoObject.Id`
- `attributes.Name`
- `attributes.LayerIndex`
- `attributes.GetUserString(...)`
- `attributes.GetUserStrings()`
- `rhinoObject.GetMaterial(...)`
- `geometry.ObjectType`
- `geometry.GetBoundingBox(...)`
- `AreaMassProperties`
- `VolumeMassProperties`

### 2.4 API client 추가

`MaterialInsightApiClient`는 backend API client 역할을 한다.

연결 API:

- `POST /api/v1/review-object`
- `POST /api/v1/review-actions`

기본 backend 주소:

```text
http://localhost:8000
```

### 2.5 사용자 승인 이후 속성 업데이트 분리

`MaterialInsightObjectUpdater`를 별도 서비스로 분리했다.

이 클래스는 사용자가 수용 또는 수정 저장을 명시한 뒤에만 다음 UserString을 업데이트하도록 설계했다.

- `material`
- `thickness_mm`
- `review_status`
- `last_review_id`
- `last_review_summary`

AI 추천을 자동 반영하지 않는 Human-in-the-loop 원칙을 코드 구조에 반영했다.

### 2.6 Panel placeholder 추가

`MaterialInsightReviewPanel`은 현재 Rhino command line 출력 기반 placeholder다.

실제 Rhino panel UI는 추후 Eto.Forms 또는 WPF로 확장할 수 있다.

## 3. 설계 문서 일치성 검토

### 일치한 점

- `10-rhino-plugin-access.md`의 Rhino 객체 추출 필드와 payload mapping을 반영했다.
- Rhino 공식 JSON이 아니라 Material Insight 내부 `review-object` payload를 생성하도록 구성했다.
- `05-mvp-design.md`의 Object Inspector, Review Panel, Feedback Logger 경계를 코드 파일로 분리했다.
- `06-architecture.md`의 “Rhino Plugin은 객체 추출과 결과 표시, Backend는 판단 로직” 구조를 유지했다.
- 사용자 승인 없는 Rhino 객체 자동 수정 금지 원칙을 `MaterialInsightObjectUpdater` 분리로 반영했다.

### 의도적으로 남긴 범위

- 실제 Rhino panel dock UI는 구현하지 않았다.
- Rhino 설치 환경에서 plugin 로딩 검증은 수행하지 않았다.
- `.rhp` packaging, installer, Yak 배포는 포함하지 않았다.
- 실제 사용자 버튼 이벤트와 `review-actions` 저장 UI는 skeleton 수준으로 남겼다.

## 4. 검증 결과

사용자 로컬 환경에서 `dotnet restore`와 `dotnet build`가 성공했다.

확인된 실행 결과:

```text
RhinoMaterialInsight -> plugin/RhinoMaterialInsight/bin/Debug/net7.0-windows/RhinoMaterialInsight.dll
Build succeeded.
Warnings: 2
Errors: 0
```

이후 nullable warning 2개는 `MaterialInsightObjectInspector.ReadUserAttributes`에서 null/blank key를 건너뛰도록 수정했다. 다시 빌드하면 warning이 해소되는지 확인한다.

빌드 산출물은 Rhino 로딩 편의를 위해 `.rhp`로도 복사되도록 project target을 추가했다.

```text
plugin/RhinoMaterialInsight/bin/Debug/net7.0-windows/RhinoMaterialInsight.rhp
```

사용자 Rhino 환경에서 plugin 로드 후 `MaterialInsightReview` 명령이 실행되었고, 객체 선택 후 backend에 다음 요청이 도달했다.

```text
POST /api/v1/review-object HTTP/1.1" 200 OK
```

초기 동기 HTTP 호출 구조에서는 API 통신 이후 Rhino가 먹통처럼 보이는 현상이 있었다. 이후 `MaterialInsightReviewCommand`를 background async 호출 구조로 수정해 Rhino UI thread 동기 대기를 제거했다.

변경 후 예상 command line 흐름:

```text
Material Insight object: ..., type=interior_wall, space=meeting_room, material=missing
Material Insight: sending review request to backend in background...
Material Insight: backend response received.
```

Rhino 설치 환경에서는 다음 명령으로 project restore/build를 확인한다.

```powershell
cd plugin/RhinoMaterialInsight
dotnet restore
dotnet build
```

Backend와 연동하려면 먼저 backend를 실행한다.

```powershell
cd backend
uvicorn app.main:app --reload
```

## 5. 산출물

- `plugin/RhinoMaterialInsight/RhinoMaterialInsight.csproj`
- `plugin/RhinoMaterialInsight/RhinoMaterialInsightPlugin.cs`
- `plugin/RhinoMaterialInsight/Commands/MaterialInsightReviewCommand.cs`
- `plugin/RhinoMaterialInsight/Models/MaterialInsightModels.cs`
- `plugin/RhinoMaterialInsight/Services/MaterialInsightObjectInspector.cs`
- `plugin/RhinoMaterialInsight/Services/MaterialInsightApiClient.cs`
- `plugin/RhinoMaterialInsight/Services/MaterialInsightObjectUpdater.cs`
- `plugin/RhinoMaterialInsight/Panels/MaterialInsightReviewPanel.cs`
- `plugin/RhinoMaterialInsight/README.md`
- `README.md`

## 6. 다음 단계

다음 phase는 `Phase 9B. Rhino Payload Contract Test`다.

Phase 9B에서는 plugin skeleton이 만드는 payload와 backend `ReviewObjectRequest` schema가 실제로 맞는지 샘플 payload와 contract test로 검증한다.
