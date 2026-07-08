from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.schema import (
    Base,
    DocumentMetadataRecord,
    RecommendationRecord,
    ReviewActionRecord,
)
from app.db.session import create_db_engine


def test_db_schema_can_create_core_tables_and_insert_records() -> None:
    engine = create_db_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        document = DocumentMetadataRecord(
            document_id="SPEC-INT-024",
            title="회의실 구획벽 시방 기준",
            path="specs/spec_int_024_meeting_room_wall.md",
            document_type="project_specification",
            category="interior_wall",
            space_type="meeting_room",
            version="2.1",
            status="active",
            source="internal_project_spec",
            keywords=["interior_wall", "meeting_room"],
        )
        recommendation = RecommendationRecord(
            recommendation_id="REC-0001",
            object_id="W-012",
            project_id="PRJ-001",
            status="review_required",
            severity="medium",
            summary="재료 정보가 누락되어 있습니다.",
            detected_issues=["material_missing"],
            required_action="designer_review",
            confidence=0.8,
            payload={"sources": ["SPEC-INT-024"]},
        )
        action = ReviewActionRecord(
            review_action_id="ACT-0001",
            recommendation_id="REC-0001",
            object_id="W-012",
            user_id="designer-01",
            action="edit",
            edited_values={"thickness_mm": 125},
            reason="회의실 차음 검토 후 두께 보정",
            payload={"approved": True},
        )

        session.add_all([document, recommendation, action])
        session.commit()

        assert session.scalar(select(DocumentMetadataRecord.document_id)) == "SPEC-INT-024"
        assert session.scalar(select(RecommendationRecord.recommendation_id)) == "REC-0001"
        assert session.scalar(select(ReviewActionRecord.review_action_id)) == "ACT-0001"
