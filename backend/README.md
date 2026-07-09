# Construction CP Recovery Backend

This backend is being pivoted to support critical path delay recovery workflows.

Currently exposed main routes:

```text
GET /health
POST /api/v1/rhino/objects
GET /api/v1/rhino/objects?project_id=...
POST /api/v1/rhino/selection
GET /api/v1/rhino/selection?project_id=...
```

The previous material-review routes are no longer registered in `app.main`.

Legacy material-review files may still exist temporarily while CP replacement models and services are introduced.

## Run

```powershell
cd backend
python -m uvicorn app.main:app --reload
```

## Rhino Sync Test

```powershell
python -m pytest app/tests/test_rhino_sync_api.py
```

## Next Backend Phase

Add CP-specific contracts:

```text
backend/app/models/cp_recovery.py
backend/app/api/routes_cp_recovery.py
backend/app/services/cp_impact_analyzer.py
backend/app/tests/test_cp_recovery_api.py
```
