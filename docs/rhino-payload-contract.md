# Rhino Payload Contract

This document fixes the boundary between the Rhino plugin and the FastAPI backend.

The payload is not Rhino's official object JSON. It is the Material Insight internal `review-object` API contract created from selected Rhino object metadata.

## Endpoint

```text
POST /api/v1/review-object
```

## Required Root Fields

- `project`
- `object`

## Required Project Fields

- `project.project_id`

Other project fields are optional:

- `project.project_type`
- `project.design_stage`
- `project.building_use`
- `project.region`
- `project.priority`

## Required Object Fields

- `object.object_id`

The following object fields are optional but recommended:

- `object.object_type`
- `object.layer`
- `object.name`
- `object.material`
- `object.thickness_mm`
- `object.space_type`
- `object.review_status`
- `object.geometry`
- `object.user_attributes`

## Geometry Fields

`object.geometry` may contain:

- `object_kind`
- `length_mm`
- `area_m2`
- `volume_m3`
- `bbox`

`bbox` can contain plugin-defined summary keys such as `min` and `max`. The backend treats it as a generic object.

## Type Notes

- `thickness_mm` is stored as a number in the canonical payload.
- The backend also accepts numeric strings such as `"75"` because Rhino UserStrings are string-based.
- Unknown fields are rejected by the backend schema.
- Rhino plugin DTOs use `JsonPropertyName` to emit snake_case fields that match the backend.

## Canonical Sample

The canonical plugin sample lives at:

```text
plugin/RhinoMaterialInsight/Samples/review_object_payload.json
```

The backend mirror sample lives at:

```text
backend/data/rhino_plugin_review_object_payload.json
```

Both samples are validated by backend contract tests.
