# CP Recovery Mock UI

This UI is now a pivot workspace for the Construction CP Recovery Agent.

Current supported behavior:

```text
load Rhino synced objects
select a Rhino object as optional CP issue context
send selected object id back to Rhino
```

Removed from the UI:

```text
material recommendation
old AI material review result panel
old model QA panel
review action buttons
old latest result bridge
```

## Run

```powershell
cd frontend/mock-plugin-ui
python -m http.server 8001
```

Open:

```text
http://localhost:8001
```

## Demo Use

1. Start backend.
2. Run `MaterialInsightSyncObjects` in Rhino.
3. Click `객체 목록 불러오기`.
4. Select a Rhino object.
5. Click `선택을 Rhino로 보내기`.
6. Run `MaterialInsightApplySelection` in Rhino.

The selected object is intended to become optional location/model context for a CP delay issue in the next implementation phase.
