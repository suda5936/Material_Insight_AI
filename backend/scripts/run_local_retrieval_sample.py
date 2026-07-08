import json
from pathlib import Path
import sys

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.models.object import DesignObjectInput
from app.services.local_retriever import load_default_retriever
from app.services.rule_engine import load_default_rule_engine


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    sample_path = project_root / "data" / "sample_objects" / "wall_meeting_room_missing_material.json"

    payload = json.loads(sample_path.read_text(encoding="utf-8"))
    design_object = DesignObjectInput.model_validate(payload)

    rule_engine = load_default_rule_engine()
    rule_results = rule_engine.evaluate(design_object)

    retriever = load_default_retriever()
    documents = retriever.search_relevant(design_object, rule_results, limit=5)

    for document in documents:
        print(
            f"{document.document_id} | {document.section} | "
            f"v{document.version} | {document.source} | score={document.score}"
        )


if __name__ == "__main__":
    main()
