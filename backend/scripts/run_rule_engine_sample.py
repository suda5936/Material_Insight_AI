import json
from pathlib import Path
import sys

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.models.object import DesignObjectInput
from app.services.rule_engine import load_default_rule_engine


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    sample_dir = project_root / "data" / "sample_objects"
    engine = load_default_rule_engine()

    for sample_path in sorted(sample_dir.glob("*.json")):
        payload = json.loads(sample_path.read_text(encoding="utf-8"))
        design_object = DesignObjectInput.model_validate(payload)
        results = engine.evaluate(design_object)
        issue_codes = [result.issue_code for result in results]
        print(f"{design_object.object_id}: {', '.join(issue_codes) if issue_codes else 'no_issues'}")


if __name__ == "__main__":
    main()
