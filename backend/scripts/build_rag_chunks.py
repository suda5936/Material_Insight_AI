import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOCUMENT_METADATA_PATH = PROJECT_ROOT / "data" / "documents" / "document_metadata.yaml"
MATERIAL_CATALOG_PATH = PROJECT_ROOT / "data" / "materials" / "material_catalog.yaml"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "rag_chunks.jsonl"


def main() -> None:
    chunks = [
        *build_document_chunks(DOCUMENT_METADATA_PATH),
        *build_material_chunks(MATERIAL_CATALOG_PATH),
    ]
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        for chunk in chunks:
            file.write(json.dumps(chunk, ensure_ascii=False, sort_keys=True) + "\n")
    print(f"Wrote {len(chunks)} chunks to {OUTPUT_PATH}")


def build_document_chunks(metadata_path: Path) -> List[Dict[str, Any]]:
    raw = yaml.safe_load(metadata_path.read_text(encoding="utf-8")) or {}
    documents = raw.get("documents", [])
    chunks: List[Dict[str, Any]] = []
    for metadata in documents:
        text = (metadata_path.parent / metadata["path"]).read_text(encoding="utf-8")
        for index, section in enumerate(split_markdown_sections(text), start=1):
            category = metadata.get("category")
            space_type = metadata.get("space_type")
            chunks.append(
                {
                    "chunk_id": f"{metadata['document_id']}::section-{index:03d}",
                    "source_id": metadata["document_id"],
                    "source_type": metadata["document_type"],
                    "title": metadata["title"],
                    "section": section["section"],
                    "chunk_text": section["text"],
                    "object_types": [category] if category else [],
                    "space_types": [space_type] if space_type else [],
                    "performance_tags": metadata.get("keywords", []),
                    "keywords": metadata.get("keywords", []),
                    "version": str(metadata.get("version")) if metadata.get("version") else None,
                    "effective_date": str(metadata.get("effective_date"))
                    if metadata.get("effective_date")
                    else None,
                    "status": metadata.get("status", "active"),
                    "source": metadata.get("source"),
                }
            )
    return chunks


def build_material_chunks(catalog_path: Path) -> List[Dict[str, Any]]:
    raw = yaml.safe_load(catalog_path.read_text(encoding="utf-8")) or {}
    chunks: List[Dict[str, Any]] = []
    for material in raw.get("materials", []):
        caution_text = " ".join(material.get("caution_notes", []))
        chunk_text = (
            f"{material['name']} ({material.get('korean_name', '')}). "
            f"Recommended use: {material.get('recommended_use', '')} "
            f"Cautions: {caution_text}"
        ).strip()
        chunks.append(
            {
                "chunk_id": f"{material['material_id']}::material",
                "source_id": material["material_id"],
                "source_type": material.get("source_type", "material_catalog"),
                "title": material["name"],
                "section": "material_catalog",
                "chunk_text": chunk_text,
                "object_types": material.get("object_types", []),
                "space_types": material.get("space_types", []),
                "performance_tags": material.get("performance_tags", []),
                "keywords": [
                    material["name"],
                    material.get("korean_name", ""),
                    *material.get("object_types", []),
                    *material.get("space_types", []),
                    *material.get("performance_tags", []),
                ],
                "version": str(material.get("version")) if material.get("version") else None,
                "effective_date": str(material.get("effective_date"))
                if material.get("effective_date")
                else None,
                "status": material.get("status", "active"),
                "source": material.get("source"),
            }
        )
    return chunks


def split_markdown_sections(text: str) -> Iterable[Dict[str, str]]:
    current_section = "document"
    current_lines: List[str] = []
    for line in text.splitlines():
        if line.startswith("#"):
            if has_text(current_lines):
                yield {"section": current_section, "text": "\n".join(current_lines).strip()}
            current_section = line.strip("# ").strip() or "document"
            current_lines = []
        else:
            current_lines.append(line)
    if has_text(current_lines):
        yield {"section": current_section, "text": "\n".join(current_lines).strip()}


def has_text(lines: List[str]) -> bool:
    return any(line.strip() for line in lines)


if __name__ == "__main__":
    main()
