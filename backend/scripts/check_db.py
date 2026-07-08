from pathlib import Path
import sys

from sqlalchemy import text

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import get_settings
from app.db.session import SessionLocal


def main() -> None:
    with SessionLocal() as session:
        value = session.execute(text("select 1")).scalar_one()
    print(f"database_ok: {value} ({get_settings().database_url})")


if __name__ == "__main__":
    main()
