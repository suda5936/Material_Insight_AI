# P6 Schedule Recovery Copilot Backend

P6 Schedule Recovery Copilot의 FastAPI 백엔드다.

현재 노출된 기본 route:

```text
GET /health
```

## Run

```powershell
cd backend
python -m uvicorn app.main:app --reload
```

## Test

```powershell
python -m pytest app/tests/test_config.py app/tests/test_health.py app/tests/test_error_handler.py
```

## Next Backend Phase

다음 단계에서 추가할 CP 전용 모듈:

```text
backend/app/models/project.py
backend/app/models/schedule.py
backend/app/api/routes_projects.py
backend/app/api/routes_schedule_import.py
backend/app/services/schedule_importer.py
backend/app/services/schedule_validator.py
```
