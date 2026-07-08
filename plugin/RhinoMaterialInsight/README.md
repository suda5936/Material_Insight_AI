# Rhino Material Insight Plugin Skeleton

이 폴더는 Material Insight AI의 Rhino Plugin skeleton이다.

Phase 9의 목표는 Rhino 설치 없이도 plugin 책임 경계를 코드로 제시하는 것이다. 실제 Rhino에서 로드하고 UI panel을 완성하려면 Rhino 8과 RhinoCommon 개발 환경이 필요하다.

## 책임 범위

Rhino plugin은 AI 판단을 직접 수행하지 않는다.

Plugin이 담당하는 일:

- Rhino 객체 선택
- RhinoObject/ObjectAttributes/GeometryBase에서 메타데이터 추출
- Material Insight 내부 `review-object` payload 생성
- FastAPI backend 호출
- 추천 결과 표시
- 사용자 승인 이후에만 Rhino 객체 UserString 업데이트

Backend가 담당하는 일:

- schema validation
- Rule Engine
- Retrieval/RAG
- LLM recommendation
- Review Action logging

## 주요 파일

- `RhinoMaterialInsight.csproj`: RhinoCommon 기반 C# project skeleton
- `RhinoMaterialInsightPlugin.cs`: Rhino plugin entry
- `Commands/MaterialInsightReviewCommand.cs`: 객체 선택 후 review API 호출 명령
- `Services/MaterialInsightObjectInspector.cs`: Rhino 객체를 Material Insight payload로 변환
- `Services/MaterialInsightApiClient.cs`: backend API client
- `Services/MaterialInsightObjectUpdater.cs`: 사용자 승인 이후 객체 속성 업데이트
- `Panels/MaterialInsightReviewPanel.cs`: Rhino command line 기반 결과 표시 placeholder
- `Models/MaterialInsightModels.cs`: backend API DTO

## Rhino에서 읽는 값

| Payload 필드 | RhinoCommon 접근 |
|---|---|
| `object.object_id` | `rhinoObject.Id`, `attributes.Name`, `material_insight_object_id` |
| `object.name` | `attributes.Name` |
| `object.layer` | `doc.Layers[attributes.LayerIndex].FullPath` |
| `object.material` | `attributes.GetUserString("material")`, `rhinoObject.GetMaterial(true)` |
| `object.object_type` | `attributes.GetUserString("object_type")` |
| `object.space_type` | `attributes.GetUserString("space_type")` |
| `object.thickness_mm` | `attributes.GetUserString("thickness_mm")` |
| `object.review_status` | `attributes.GetUserString("review_status")` |
| `object.geometry.object_kind` | `geometry.ObjectType` |
| `object.geometry.bbox` | `geometry.GetBoundingBox(true)` |
| `object.user_attributes` | `attributes.GetUserStrings()` |

이 payload는 Rhino 공식 JSON이 아니라 Material Insight backend가 받는 내부 API 계약이다.

계약 문서와 canonical sample은 다음 파일에 있다.

```text
docs/rhino-payload-contract.md
plugin/RhinoMaterialInsight/Samples/review_object_payload.json
backend/data/rhino_plugin_review_object_payload.json
```

## 실행 전 준비

Backend:

```powershell
cd backend
uvicorn app.main:app --reload
```

Rhino plugin 개발:

```powershell
cd plugin/RhinoMaterialInsight
dotnet restore
dotnet build
```

빌드가 끝나면 다음 파일을 Rhino에서 로드한다.

```text
plugin/RhinoMaterialInsight/bin/Debug/net7.0-windows/RhinoMaterialInsight.rhp
```

Rhino에서 `PlugInManager`를 열고 Install 버튼으로 `.rhp` 파일을 선택하거나, Rhino 창에 `.rhp` 파일을 끌어다 놓는다. 로드 후 명령창에서 다음 명령을 실행한다.

```text
MaterialInsightReview
```

명령 실행 후 backend 통신은 백그라운드에서 수행된다. Rhino command line에 `sending review request to backend in background...`가 표시되면 Rhino UI를 계속 조작할 수 있어야 한다.

Plugin API client는 8초 timeout을 사용하므로, backend가 꺼져 있으면 잠시 후 command line에 오류가 표시된다.

## Rhino 사용자 속성 예시

선택 객체에 다음 UserString을 넣으면 backend 검토 품질이 좋아진다.

```text
object_type=interior_wall
space_type=meeting_room
thickness_mm=75
review_status=pending
acoustic_required=true
fire_rating=
```

## Human-in-the-loop 원칙

AI 추천은 자동으로 Rhino 객체에 반영하지 않는다.

`MaterialInsightObjectUpdater`는 사용자가 수용 또는 수정 저장을 명시한 이후에만 다음 UserString을 업데이트하도록 분리되어 있다.

```text
material
thickness_mm
review_status
last_review_id
last_review_summary
```
