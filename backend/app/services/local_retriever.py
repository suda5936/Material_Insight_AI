from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

import yaml

from app.models.document import RetrievedDocument
from app.models.object import DesignObjectInput
from app.models.rule import RuleResult


TOKEN_PATTERN = re.compile(r"[A-Za-z0-9가-힣_]+")
DEFAULT_MIN_RELEVANCE_SCORE = 5.0


class LocalRetrieverError(RuntimeError):
    pass


@dataclass(frozen=True)
class DocumentRecord:
    metadata: Dict[str, Any]
    text: str


@dataclass(frozen=True)
class DocumentChunk:
    metadata: Dict[str, Any]
    section: str
    text: str
    tokens: set[str]


@dataclass(frozen=True)
class LocalRetriever:
    chunks: List[DocumentChunk]

    @classmethod
    def from_metadata_file(cls, metadata_path: Path) -> "LocalRetriever":
        raw = yaml.safe_load(metadata_path.read_text(encoding="utf-8")) or {}
        documents = raw.get("documents")
        if not isinstance(documents, list):
            raise LocalRetrieverError("Metadata file must contain a 'documents' list.")

        document_root = metadata_path.parent
        chunks: List[DocumentChunk] = []
        for metadata in documents:
            document_path = document_root / metadata["path"]
            text = document_path.read_text(encoding="utf-8")
            record = DocumentRecord(metadata=metadata, text=text)
            chunks.extend(_chunk_document(record))
        return cls(chunks=chunks)

    def search(
        self,
        design_object: DesignObjectInput,
        rule_results: Sequence[RuleResult],
        limit: int = 5,
    ) -> List[RetrievedDocument]:
        query_terms = build_query_terms(design_object, rule_results)
        scored = []
        for chunk in self.chunks:
            if chunk.metadata.get("status") != "active":
                continue
            score = _score_chunk(chunk, query_terms, design_object, rule_results)
            if score <= 0:
                continue
            scored.append((score, chunk))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            _to_retrieved_document(score=score, chunk=chunk)
            for score, chunk in scored[:limit]
        ]

    def search_relevant(
        self,
        design_object: DesignObjectInput,
        rule_results: Sequence[RuleResult],
        limit: int = 5,
        min_score: float = DEFAULT_MIN_RELEVANCE_SCORE,
    ) -> List[RetrievedDocument]:
        candidates = self.search(design_object, rule_results, limit=limit)
        return [document for document in candidates if document.score >= min_score]


def load_default_retriever() -> LocalRetriever:
    return LocalRetriever.from_metadata_file(default_metadata_path())


def default_metadata_path() -> Path:
    return Path(__file__).resolve().parents[3] / "data" / "documents" / "document_metadata.yaml"


def build_query_terms(
    design_object: DesignObjectInput,
    rule_results: Sequence[RuleResult],
) -> set[str]:
    values: List[Any] = [
        design_object.object_id,
        design_object.object_type,
        design_object.layer,
        design_object.name,
        design_object.material,
        design_object.space_type,
        design_object.review_status,
    ]
    values.extend(result.issue_code for result in rule_results)
    values.extend(result.field for result in rule_results)
    values.extend(_flatten_values(design_object.user_attributes))
    return _tokenize(" ".join(str(value) for value in values if value is not None))


def _chunk_document(record: DocumentRecord) -> List[DocumentChunk]:
    chunks: List[DocumentChunk] = []
    current_section = "document"
    current_lines: List[str] = []

    for line in record.text.splitlines():
        if line.startswith("#"):
            if _has_text(current_lines):
                chunks.append(_make_chunk(record.metadata, current_section, current_lines))
            current_lines = []
            current_section = line.strip("# ").strip() or "document"
        else:
            current_lines.append(line)

    if _has_text(current_lines):
        chunks.append(_make_chunk(record.metadata, current_section, current_lines))

    return chunks


def _make_chunk(
    metadata: Dict[str, Any],
    section: str,
    lines: Sequence[str],
) -> DocumentChunk:
    text = "\n".join(line for line in lines).strip()
    keyword_text = " ".join(str(keyword) for keyword in metadata.get("keywords", []))
    tokens = _tokenize(f"{metadata.get('title', '')} {section} {keyword_text} {text}")
    return DocumentChunk(metadata=metadata, section=section, text=text, tokens=tokens)


def _has_text(lines: Sequence[str]) -> bool:
    return any(line.strip() for line in lines)


def _score_chunk(
    chunk: DocumentChunk,
    query_terms: set[str],
    design_object: DesignObjectInput,
    rule_results: Sequence[RuleResult],
) -> float:
    overlap = len(query_terms & chunk.tokens)
    score = float(overlap)

    if design_object.object_type and chunk.metadata.get("category") == design_object.object_type:
        score += 4.0
    if design_object.space_type and chunk.metadata.get("space_type") == design_object.space_type:
        score += 4.0

    issue_codes = {result.issue_code for result in rule_results}
    keywords = {str(keyword).lower() for keyword in chunk.metadata.get("keywords", [])}
    score += len({issue.lower() for issue in issue_codes} & keywords) * 3.0

    if score <= 0:
        return 0.0

    if chunk.metadata.get("document_type") == "project_specification":
        score += 1.0
    if chunk.metadata.get("document_type") == "approved_case":
        score += 0.5

    return score


def _to_retrieved_document(score: float, chunk: DocumentChunk) -> RetrievedDocument:
    metadata = chunk.metadata
    return RetrievedDocument(
        document_id=metadata["document_id"],
        title=metadata["title"],
        section=chunk.section,
        chunk_text=chunk.text,
        document_type=metadata["document_type"],
        version=str(metadata.get("version")) if metadata.get("version") is not None else None,
        effective_date=str(metadata.get("effective_date"))
        if metadata.get("effective_date") is not None
        else None,
        status=metadata.get("status", "active"),
        source=metadata.get("source"),
        score=round(score, 3),
    )


def _tokenize(text: str) -> set[str]:
    return {token.lower() for token in TOKEN_PATTERN.findall(text)}


def _flatten_values(value: Any) -> Iterable[Any]:
    if isinstance(value, dict):
        for item in value.values():
            yield from _flatten_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from _flatten_values(item)
    else:
        yield value
