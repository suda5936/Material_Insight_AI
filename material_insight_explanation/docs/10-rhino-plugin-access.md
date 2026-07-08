# 10. Rhino Plugin 접근 가능성 및 데이터 처리 방식

## 10.1 Rhino를 직접 설치해서 실행해야 하는가?

결론부터 말하면, **실제 Rhino Plugin까지 시연하려면 Rhino를 설치하고 실행해야 한다.**  
하지만 MVP 개발 전체가 Rhino 설치에 의존할 필요는 없다.

본 프로젝트는 다음 두 단계로 나누어 진행하는 것이 가장 현실적이다.

| 구분 | Rhino 필요 여부 | 설명 |
|---|---|---|
| Agent 백엔드 개발 | 불필요 | FastAPI, Rule Engine, RAG, LLM 추천, 로그 저장은 Rhino 없이 구현 가능 |
| Mock Plugin UI 데모 | 불필요 | Rhino에서 추출될 객체 JSON을 웹 UI 또는 샘플 파일로 입력해 시연 가능 |
| Rhino Plugin skeleton 작성 | 부분 필요 | 코드 구조는 작성 가능하지만 실제 로딩·객체 선택 테스트는 Rhino 필요 |
| 실제 Rhino 객체 선택 시연 | 필요 | Rhino 설치 후 플러그인을 로드해 객체 선택, 속성 추출, 결과 표시를 확인해야 함 |

따라서 과제 MVP에서는 다음 전략을 권장한다.

1. **우선 Rhino 없이 백엔드와 Mock Plugin UI를 완성한다.**
2. 객체 입력은 `sample_objects/*.json`으로 구성한다.
3. API 구조는 실제 Rhino Plugin이 호출할 수 있도록 설계한다.
4. 시간이 가능하면 마지막에 Rhino Plugin을 연결해 실제 객체 선택 시연을 추가한다.

이 방식은 구현 리스크를 줄이면서도 보고서의 설계와 구현 흐름을 일치시킬 수 있다.

---

## 10.2 Rhino Plugin 접근 가능성

Rhino는 RhinoCommon SDK를 통해 C# 기반 플러그인을 만들 수 있다. 플러그인은 Rhino 내부에 명령을 추가하고, 사용자가 선택한 객체의 속성과 geometry 정보를 읽을 수 있다.

Material Insight AI에서 필요한 다음 정보는 RhinoCommon으로 접근 가능한 범위에 포함된다.

- 객체 고유 ID
- 객체 이름
- 레이어 정보
- 객체 타입
- 재료 인덱스와 재료 출처
- 그룹 또는 블록 관련 정보
- Bounding Box
- Curve, Surface, Brep, Mesh 등 geometry 타입
- 사용자 정의 문자열
- UserDictionary 또는 UserData 기반 사용자 정의 속성

즉, 본 프로젝트의 핵심 입력인 `object_id`, `layer`, `name`, `material`, `object_type`, `space_type`, `thickness_mm`, `review_status`를 Rhino Plugin에서 수집해 백엔드로 전달하는 구조는 구현 가능하다.

---

## 10.3 Rhino에서 가져올 데이터

Rhino 객체에서 가져올 데이터는 크게 네 종류로 나눈다.

### 1. 기본 객체 속성

Rhino 객체가 기본적으로 가지고 있는 속성이다.

| 필드 | 설명 | 예시 |
|---|---|---|
| object_id | Rhino 객체 고유 ID | `W-012` 또는 GUID |
| name | 객체 이름 | `MeetingRoom_Wall_012` |
| layer | 객체가 속한 레이어 | `A-WALL` |
| object_kind | Rhino geometry 타입 | `Brep`, `Curve`, `Mesh` |
| material | 객체 또는 레이어에 지정된 재료 | `Gypsum Board` |

### 2. 사용자 정의 업무 속성

Rhino는 BIM처럼 건축 객체 의미를 기본적으로 보장하지 않는다. 따라서 Material Insight AI가 필요한 업무 속성은 UserString 또는 UserDictionary로 저장하는 것이 좋다.

| 필드 | 설명 | 예시 |
|---|---|---|
| object_type | 업무상 객체 유형 | `interior_wall` |
| space_type | 공간 용도 | `meeting_room` |
| thickness_mm | 부재 두께 | `75` |
| review_status | 검토 상태 | `pending` |
| fire_rating | 내화 관련 입력 | `null` |
| acoustic_required | 차음 검토 필요 여부 | `true` |

### 3. Geometry 기반 보조 정보

객체의 형태에서 계산 가능한 값이다.

| 필드 | 설명 |
|---|---|
| bbox | 경계 상자 |
| area_m2 | 면적 |
| volume_m3 | 체적 |
| length_mm | 길이 |
| estimated_thickness_mm | geometry 기반 추정 두께 |

단, Rhino 자유형 모델에서 두께 자동 계산은 항상 정확하지 않다. MVP에서는 `thickness_mm`를 사용자 정의 속성에서 읽고, geometry 기반 두께 추정은 보조 정보로만 사용한다.

### 4. 프로젝트 컨텍스트

프로젝트 단위로 입력하거나 별도 설정 파일에서 가져온다.

| 필드 | 설명 | 예시 |
|---|---|---|
| project_id | 프로젝트 ID | `PRJ-001` |
| project_type | 프로젝트 유형 | `interior` |
| design_stage | 설계 단계 | `basic_design` |
| building_use | 건물 용도 | `office` |
| region | 지역 | `KR` |

---

## 10.4 Material Insight API용 Rhino 객체 Payload

중요한 점은 아래 JSON이 **Rhino 공식 표준 JSON 형식이 아니라는 것**이다. RhinoCommon에는 `RhinoObject.ToJSON()`, `GeometryBase.ToJSON()`, `ObjectAttributes.FromJSON()` 같은 Rhino 객체 직렬화 API가 존재하지만, 그 형식은 Rhino 객체/geometry 자체를 직렬화하기 위한 것이다.

Material Insight AI는 전체 Rhino geometry를 그대로 백엔드에 보내는 시스템이 아니다. 선택 객체에서 필요한 업무 메타데이터만 추출해 FastAPI 백엔드가 이해할 수 있는 **프로젝트 전용 review-object payload**로 변환한다.

따라서 Rhino Plugin은 선택 객체를 다음 JSON 구조로 변환해 백엔드 API로 보낸다.

```json
{
  "project": {
    "project_id": "PRJ-001",
    "project_type": "interior",
    "design_stage": "basic_design",
    "building_use": "office",
    "region": "KR"
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

이 JSON 구조는 Rhino 공식 포맷이 아니라, Rhino Plugin, Mock Plugin UI, 테스트 fixture가 공유하는 **Material Insight 내부 API 계약**이다. 이렇게 하면 Rhino 연결이 늦어져도 백엔드와 Agent 로직은 먼저 완성할 수 있다.

실제 Rhino Plugin 구현 시에는 다음 RhinoCommon 속성과 메서드에서 값을 추출해 위 payload에 매핑한다.

| Payload 필드 | RhinoCommon 접근 예시 | 비고 |
|---|---|---|
| `object.object_id` | `rhinoObject.Id` 또는 `attributes.ObjectId` | Rhino 객체 GUID |
| `object.name` | `attributes.Name` | 객체 이름 |
| `object.layer` | `doc.Layers[attributes.LayerIndex].FullPath` | LayerIndex 기반 |
| `object.material` | `attributes.MaterialIndex`, `attributes.MaterialSource`, `rhinoObject.GetMaterial(...)` | 객체/레이어 재료 해석 필요 |
| `object.geometry.object_kind` | `rhinoObject.Geometry.ObjectType` 또는 geometry class name | Brep, Curve, Mesh 등 |
| `object.geometry.bbox` | `geometry.GetBoundingBox(...)` | geometry summary |
| `object.object_type` | `attributes.GetUserString("object_type")` | 업무용 사용자 정의 속성 |
| `object.space_type` | `attributes.GetUserString("space_type")` | 업무용 사용자 정의 속성 |
| `object.thickness_mm` | `attributes.GetUserString("thickness_mm")` | 문자열로 읽힌 뒤 백엔드에서 숫자 변환 가능 |
| `object.user_attributes` | `attributes.GetUserStrings()` 또는 `UserDictionary` | 추가 업무 속성 |

---

## 10.5 데이터 추출 우선순위

객체 정보는 다음 우선순위로 해석한다.

1. **UserString/UserDictionary에 명시된 값**
2. **객체 이름과 레이어명 기반 매핑**
3. **재료 인덱스와 레이어 재료 정보**
4. **Geometry 계산값**
5. **추정 불가 시 사용자 입력 요청**

예를 들어 객체의 `object_type`이 UserDictionary에 없지만 레이어명이 `A-WALL`이면 `interior_wall`로 추정할 수 있다. 하지만 이 경우 결과에는 반드시 추정값임을 표시하고, 사용자가 확인할 수 있어야 한다.

---

## 10.6 백엔드 처리 방식

Rhino Plugin에서 보낸 JSON은 FastAPI 백엔드에서 다음 순서로 처리한다.

1. 요청 JSON 검증
2. 객체 속성 정규화
3. Rule Engine 실행
4. RAG 검색 항상 실행
5. relevance score threshold로 sources 채택 여부 판단
6. threshold 미통과 시 “근거 없음”으로 처리
7. LLM 추천 생성
8. 결과 JSON 반환
9. 사용자 액션 저장

### Rule Engine 처리 예시

```yaml
입력:
  object_type: interior_wall
  space_type: meeting_room
  material: null
  thickness_mm: 75

탐지 결과:
  - material_missing
  - thickness_review_required
```

### RAG 검색 질의 예시

```text
객체 유형: 비내력 내벽
공간 용도: 회의실
현재 재료: 미지정
현재 두께: 75mm
탐지 이슈: 재료 누락, 두께 검토 필요
검색 목적: 회의실 구획벽 재료 후보, 차음 검토, 일반 두께 참고 범위
```

### LLM 출력 예시

```json
{
  "status": "review_required",
  "severity": "medium",
  "summary": "재료 정보가 누락되어 있고 회의실 구획벽의 두께와 차음 성능 검토가 필요합니다.",
  "detected_issues": [
    "material_missing",
    "thickness_review_required"
  ],
  "material_candidates": [
    "경량철골 + 석고보드",
    "차음 보드 조합"
  ],
  "performance_notes": [
    "회의실은 차음 요구사항을 확인해야 합니다."
  ],
  "required_action": "designer_review",
  "confidence": 0.78
}
```

---

## 10.7 Rhino 결과 출력 방식

Rhino 안에서 결과는 세 가지 방식으로 출력한다.

### 1. 사이드 패널

가장 중요한 출력 방식이다.

패널에는 다음 내용을 표시한다.

- 선택 객체 요약
- 탐지된 문제
- 위험 수준
- 추천 재료
- 두께 검토 안내
- 성능상 주의사항
- 관련 문서 출처
- 추천 신뢰도
- 사용자 행동 버튼

사용자 행동 버튼은 다음과 같다.

- 수용
- 수정
- 보류
- 무시
- 전문가 검토 요청

### 2. 객체 속성 업데이트

사용자가 승인하거나 수정 후 수용한 경우에만 Rhino 객체 속성을 업데이트한다.

예시:

```yaml
material: 경량철골 + 석고보드
thickness_mm: 125
review_status: completed
last_review_id: REC-0001
last_review_summary: 회의실 구획벽 재료와 두께 검토 완료
```

주의할 점은 AI 추천을 자동으로 반영하지 않는다는 것이다. 반드시 사용자 승인 이후에만 객체 속성을 바꾼다.

### 3. 화면 표시 또는 마커

검토 상태를 Rhino 화면에 시각적으로 표시할 수 있다.

| 상태 | 표시 방식 예시 |
|---|---|
| 재료 누락 | 노란색 경고 마커 |
| 두께 검토 필요 | 주황색 표시 |
| 전문가 검토 필요 | 빨간색 표시 |
| 검토 완료 | 초록색 상태 표시 |

이 표시는 설계값 확정이 아니라 검토 상태를 알려주는 보조 UI다.

---

## 10.8 Rhino Plugin 의사코드

아래 코드는 실제 구현 방향을 보여주는 의사코드다.

```csharp
protected override Result RunCommand(RhinoDoc doc, RunMode mode)
{
    ObjRef objRef;
    var result = RhinoGet.GetOneObject(
        "검토할 객체를 선택하세요",
        false,
        ObjectType.AnyObject,
        out objRef
    );

    if (result != Result.Success)
        return result;

    var rhinoObject = objRef.Object();
    var attributes = rhinoObject.Attributes;
    var geometry = rhinoObject.Geometry;

    var payload = new
    {
        project = GetProjectContext(),
        @object = new
        {
            object_id = rhinoObject.Id.ToString(),
            object_type = attributes.GetUserString("object_type"),
            layer = doc.Layers[attributes.LayerIndex].FullPath,
            name = attributes.Name,
            material = ResolveMaterialName(doc, attributes),
            thickness_mm = attributes.GetUserString("thickness_mm"),
            space_type = attributes.GetUserString("space_type"),
            review_status = attributes.GetUserString("review_status"),
            geometry = BuildGeometrySummary(geometry),
            user_attributes = ReadMaterialInsightAttributes(attributes)
        }
    };

    var recommendation = PostReviewObject(payload);
    ShowReviewPanel(recommendation);

    return Result.Success;
}
```

승인 이후에는 다음과 같은 방식으로 Rhino 객체의 사용자 정의 속성을 수정한다.

```csharp
attributes.SetUserString("material", approvedMaterial);
attributes.SetUserString("thickness_mm", approvedThickness.ToString());
attributes.SetUserString("review_status", "completed");
attributes.SetUserString("last_review_id", recommendationId);

doc.Objects.ModifyAttributes(rhinoObject, attributes, true);
doc.Views.Redraw();
```

---

## 10.9 구현 시 주의할 점

### 1. Rhino는 BIM이 아니다

Rhino 객체는 기본적으로 `벽`, `바닥`, `천장` 같은 건축 의미를 보장하지 않는다. 따라서 레이어 규칙과 사용자 정의 속성 체계를 함께 설계해야 한다.

### 2. 두께 자동 계산은 MVP 핵심으로 두지 않는다

Brep 또는 Mesh에서 두께를 자동 추정할 수는 있지만 모델링 방식에 따라 오차가 크다. MVP에서는 명시적으로 입력된 `thickness_mm`를 기준으로 검토한다.

### 3. AI 자동 반영 금지

AI가 추천한 재료나 두께를 사용자 승인 없이 Rhino 객체에 바로 쓰면 안 된다. 본 프로젝트의 Human-in-the-loop 원칙과 맞지 않기 때문이다.

### 4. 구조·법규 항목은 전문가 검토로 전환

구조 안전성, 내화, 법규 적합성은 Agent가 확정하지 않는다. 관련 가능성이 감지되면 `expert_review`로 분류하고 검토 요청을 생성한다.

### 5. Rhino 없이도 백엔드 개발 가능하게 유지

플러그인 개발 환경 문제가 생길 수 있으므로, 항상 동일한 JSON 입력을 사용하는 Mock Plugin UI와 샘플 객체 파일을 유지한다.

---

## 10.10 MVP 결론

Rhino Plugin 접근은 가능하다.  
다만 안정적인 MVP를 위해서는 Rhino Plugin을 모든 판단 로직의 중심으로 두지 않고, **객체 데이터 추출과 결과 표시 계층**으로 제한하는 것이 좋다.

최종 구조는 다음과 같다.

```text
Rhino Plugin
  → 객체 선택과 메타데이터 추출
  → 백엔드 API 호출
  → 결과 패널 표시
  → 사용자 승인 후 객체 속성 업데이트

FastAPI Backend
  → Rule Engine
  → RAG 검색
  → LLM 추천
  → Review Log 저장
```

이 구조는 설계 문서의 핵심인 **객체 중심성, 근거 기반 추천, Human-in-the-loop, 위험 통제, 로그 저장**을 구현과 직접 연결한다.
