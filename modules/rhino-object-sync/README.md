# Rhino Object Sync Preserved Module

## Status

Preserved support module.

This module should remain functional while the main application pivots to the Construction CP Recovery Agent.

## New Role

Rhino object sync is no longer the input layer for material recommendation.

Its new role is:

```text
visual issue-location selector for construction delay events
```

The module helps attach model context to a CP delay issue:

```text
rhino object id
object name
layer
geometry kind
bounding box
visibility / locked state
optional user attributes
```

Schedule analysis must still be driven by schedule data:

```text
activity id
duration
calendar
dependency logic
float
baseline
actual progress
resources
cost categories
```

## Preserved Backend Files

```text
backend/app/api/routes_rhino_sync.py
backend/app/models/rhino_sync.py
backend/app/tests/test_rhino_sync_api.py
backend/app/main.py
```

Relevant endpoints:

```text
POST /api/v1/rhino/objects
GET  /api/v1/rhino/objects?project_id=...
POST /api/v1/rhino/selection
GET  /api/v1/rhino/selection?project_id=...
```

## Preserved Plugin Files

```text
plugin/RhinoMaterialInsight/Commands/MaterialInsightSyncObjectsCommand.cs
plugin/RhinoMaterialInsight/Commands/MaterialInsightApplySelectionCommand.cs
plugin/RhinoMaterialInsight/Models/MaterialInsightModels.cs
plugin/RhinoMaterialInsight/Services/MaterialInsightApiClient.cs
plugin/RhinoMaterialInsight/Services/MaterialInsightObjectInspector.cs
plugin/RhinoMaterialInsight/README.md
```

Rhino commands:

```text
MaterialInsightSyncObjects
MaterialInsightApplySelection
```

## Preserved Frontend Behavior

The current browser UI can:

```text
load synced Rhino objects
display object cards
select an object
send the selected object id back to backend
```

During the CP pivot, this UI should be reused as the left-side "issue location / model context" panel.

## Do Not Break

During future CP refactoring, avoid breaking these contracts:

```text
Rhino plugin can upload object summaries.
Frontend can list uploaded Rhino objects.
Frontend can store selected object_id.
Rhino plugin can apply frontend-selected object_id.
```

## Safe To Change Later

These names still contain the old Material Insight wording and may be renamed later after the CP backend is stable:

```text
plugin/RhinoMaterialInsight/
frontend/mock-plugin-ui/
MaterialInsightSyncObjects
MaterialInsightApplySelection
```

Rename only after confirming the compiled Rhino plugin still loads and the backend routes still pass tests.

## Manual Verification

```powershell
cd backend
python -m pytest app/tests/test_rhino_sync_api.py
```

```powershell
cd plugin/RhinoMaterialInsight
dotnet build
```

```powershell
node --check frontend/mock-plugin-ui/app.js
```
