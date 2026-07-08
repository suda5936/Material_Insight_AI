# Review Object Payload Contract

이 문서는 Rhino Plugin, Mock Plugin UI, FastAPI Backend가 공유하는 `review-object` 입력 JSON 계약이다.

주의: 이 JSON은 Rhino 공식 native JSON 형식이 아니다. RhinoCommon에는 Rhino 객체와 geometry 자체를 직렬화하는 `ToJSON`/`FromJSON` 계열 API가 있지만, Material Insight AI는 전체 Rhino 객체를 그대로 전송하지 않고 업무 검토에 필요한 메타데이터만 추출해 이 계약으로 보낸다.

## 목적

Rhino Plugin이 실제 객체를 선택해 데이터를 추출할 때, 백엔드가 기대하는 형식과 다르면 검토 API가 실패한다. 따라서 MVP에서는 아래 payload 형식을 표준 계약으로 고정한다.

## Endpoint

```text
POST /api/v1/review-object
```

Phase 3A 기준으로 endpoint 구현은 아직 없지만, 입력 schema는 `ReviewObjectRequest`로 이미 고정되어 있다.

## Standard Payload

```json
{
  "project": {
    "project_id": "PRJ-001",
    "project_type": "interior",
    "design_stage": "basic_design",
    "building_use": "office",
    "region": "KR",
    "priority": "performance"
  },
  "object": {
    "object_id": "W-012",
    "object_type": "interior_wall",
    "layer": "A-WALL",
    "name": "MeetingRoom_Wall_012",
    "space_type": "meeting_room",
    "material": null,
    "thickness_mm": 75,
    "review_status": "pending",
    "geometry": {
      "object_kind": "Brep",
      "length_mm": null,
      "area_m2": 12.4,
      "volume_m3": null,
      "bbox": {}
    },
    "user_attributes": {
      "fire_rating": null,
      "acoustic_required": true
    }
  }
}
```

## Backend Schema Mapping

| Payload path | Backend model | Required | Note |
|---|---|---:|---|
| `project.project_id` | `ProjectContext.project_id` | yes | 프로젝트 식별자 |
| `project.project_type` | `ProjectContext.project_type` | no | 예: `interior` |
| `project.design_stage` | `ProjectContext.design_stage` | no | 예: `basic_design` |
| `project.building_use` | `ProjectContext.building_use` | no | 예: `office` |
| `project.region` | `ProjectContext.region` | no | 예: `KR` |
| `project.priority` | `ProjectContext.priority` | no | 예: `performance` |
| `object.object_id` | `DesignObjectInput.object_id` | yes | Rhino GUID 또는 업무용 ID |
| `object.object_type` | `DesignObjectInput.object_type` | no | UserString/UserDictionary 우선 |
| `object.layer` | `DesignObjectInput.layer` | no | Rhino layer full path |
| `object.name` | `DesignObjectInput.name` | no | Rhino object name |
| `object.material` | `DesignObjectInput.material` | no | 객체 또는 레이어 재료명 |
| `object.thickness_mm` | `DesignObjectInput.thickness_mm` | no | 숫자 권장. Rhino에서 문자열로 와도 Pydantic이 숫자로 변환 가능 |
| `object.space_type` | `DesignObjectInput.space_type` | no | 예: `meeting_room` |
| `object.review_status` | `DesignObjectInput.review_status` | no | 예: `pending`, `reviewed` |
| `object.geometry.object_kind` | `GeometrySummary.object_kind` | no | 예: `Brep`, `Curve`, `Mesh` |
| `object.geometry.length_mm` | `GeometrySummary.length_mm` | no | 길이 |
| `object.geometry.area_m2` | `GeometrySummary.area_m2` | no | 면적 |
| `object.geometry.volume_m3` | `GeometrySummary.volume_m3` | no | 체적 |
| `object.geometry.bbox` | `GeometrySummary.bbox` | no | Rhino bounding box summary |
| `object.user_attributes` | `DesignObjectInput.user_attributes` | no | 기타 업무 속성 |

## Rhino Plugin Extraction Rule

Rhino Plugin은 다음 우선순위로 값을 채운다.

1. `UserString` 또는 `UserDictionary`
2. Rhino 기본 속성: object id, name, layer, material
3. Geometry summary
4. 레이어명/객체명 기반 추정값
5. 추정 불가 시 `null`

## Important Constraints

- Backend는 현재 `extra="forbid"` 정책을 사용한다. 계약에 없는 top-level field나 object field를 보내면 validation error가 난다.
- Rhino Plugin에서 추가 정보가 필요하면 `object.user_attributes` 안에 넣는다.
- `thickness_mm`는 가능하면 숫자로 보낸다.
- 객체 타입이나 공간 용도가 불명확하면 추정값을 임의 확정하지 말고 `null`로 보낸다.
- AI 추천값은 사용자 승인 전에는 Rhino 객체에 자동 반영하지 않는다.

## Contract Test

계약 fixture:

```text
backend/data/rhino_plugin_review_object_payload.json
```

검증 테스트:

```text
backend/app/tests/test_review_object_contract.py
```

실행:

```powershell
cd backend
pytest app/tests/test_review_object_contract.py
```
