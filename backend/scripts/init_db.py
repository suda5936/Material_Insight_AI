from pathlib import Path
import sys

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import get_settings
from app.db.schema import Base
from app.db.session import engine


def main() -> None:
    Base.metadata.create_all(bind=engine)
    print(f"database_initialized: {get_settings().database_url}")


if __name__ == "__main__":
    main()
