from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.schema import Base, ReviewActionRecord
from app.db.session import create_db_engine
from app.models.review_action import ReviewActionRequest
from app.services.review_logger import save_review_action


def test_save_review_action_persists_record() -> None:
    engine = create_db_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        response = save_review_action(
            session,
            ReviewActionRequest(
                recommendation_id="REC-0001",
                object_id="W-012",
                user_id="designer-01",
                action="accept",
                reason="Reviewed and accepted.",
            ),
        )

        record = session.scalar(
            select(ReviewActionRecord).where(
                ReviewActionRecord.review_action_id == response.review_action_id
            )
        )

    assert response.status == "saved"
    assert record is not None
    assert record.recommendation_id == "REC-0001"
    assert record.object_id == "W-012"
    assert record.action == "accept"
