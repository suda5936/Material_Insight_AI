from pathlib import Path
import sys

import yaml

BACKEND_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_ROOT.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.db.schema import DocumentMetadataRecord
from app.db.session import SessionLocal


def main() -> None:
    metadata_path = PROJECT_ROOT / "data" / "documents" / "document_metadata.yaml"
    raw = yaml.safe_load(metadata_path.read_text(encoding="utf-8")) or {}
    documents = raw.get("documents", [])

    with SessionLocal() as session:
        for item in documents:
            record = DocumentMetadataRecord(
                document_id=item["document_id"],
                title=item["title"],
                path=item["path"],
                document_type=item["document_type"],
                category=item.get("category"),
                space_type=item.get("space_type"),
                version=str(item.get("version")) if item.get("version") is not None else None,
                effective_date=str(item.get("effective_date"))
                if item.get("effective_date") is not None
                else None,
                status=item.get("status", "active"),
                source=item.get("source"),
                keywords=item.get("keywords", []),
            )
            session.merge(record)
        session.commit()

    print(f"document_metadata_seeded: {len(documents)}")


if __name__ == "__main__":
    main()
