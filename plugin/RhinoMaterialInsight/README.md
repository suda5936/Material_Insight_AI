# Rhino Object Sync Plugin

This Rhino plugin is preserved as a support module for the Construction CP Recovery Agent.

It does not perform material recommendation.

Its role is:

```text
scan Rhino objects
send object summaries to backend
apply frontend-selected object id back in Rhino
```

## Commands

### `MaterialInsightSyncObjects`

Scans visible Rhino document objects and sends object summaries to:

```text
POST /api/v1/rhino/objects
```

### `MaterialInsightApplySelection`

Reads the selected object id from:

```text
GET /api/v1/rhino/selection?project_id=...
```

Then selects and zooms to the matching object in Rhino.

## Build

```powershell
cd plugin/RhinoMaterialInsight
dotnet restore
dotnet build
```

Generated plugin:

```text
plugin/RhinoMaterialInsight/bin/Debug/net7.0-windows/RhinoMaterialInsight.rhp
```

## Demo Flow

1. Start backend.
2. Open Rhino model.
3. Run `MaterialInsightSyncObjects`.
4. Open frontend.
5. Load synced Rhino object list.
6. Select one object card.
7. Send selected object id to backend.
8. Run `MaterialInsightApplySelection` in Rhino.

The selected Rhino object becomes optional model/location context for a CP delay issue.

## Preserved Contract

Do not break these behaviors during CP recovery development:

```text
Rhino can upload object summaries.
Frontend can list uploaded Rhino objects.
Frontend can store selected object_id.
Rhino can apply frontend-selected object_id.
```
