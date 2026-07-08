import json
from pathlib import Path
import sys

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.models.object import ReviewObjectRequest


def main() -> None:
    sample_path = Path(__file__).resolve().parents[1] / "data" / "sample_review_object_request.json"
    payload = json.loads(sample_path.read_text(encoding="utf-8"))
    request = ReviewObjectRequest.model_validate(payload)
    print("sample_request_valid")
    print(request.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
