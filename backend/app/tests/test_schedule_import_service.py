import pytest

from app.core.errors import APIError
from app.services.schedule_import import (
    detect_cycle,
    parse_activities_csv,
    parse_relationships_csv,
    validate_relationship_references,
)

ACTIVITIES_CSV = """activity_id,name,original_duration,remaining_duration,is_milestone,is_completed
A100,Foundation,10,10,false,false
A200,Structure,20,20,false,false
A300,Handover,0,0,true,false
"""

RELATIONSHIPS_CSV = """predecessor_id,successor_id,type,lag
A100,A200,FS,0
A200,A300,FS,2
"""


def test_parse_activities_csv_happy_path() -> None:
    activities = parse_activities_csv(ACTIVITIES_CSV)

    assert len(activities) == 3
    assert activities[0].activity_id == "A100"
    assert activities[2].is_milestone is True


def test_parse_activities_csv_rejects_duplicate_id() -> None:
    csv_text = ACTIVITIES_CSV + "A100,Duplicate,5,5,false,false\n"

    with pytest.raises(APIError) as excinfo:
        parse_activities_csv(csv_text)

    assert excinfo.value.error_code == "invalid_schedule_input"


def test_parse_activities_csv_rejects_completed_with_remaining_duration() -> None:
    csv_text = (
        "activity_id,name,original_duration,remaining_duration,is_milestone,is_completed\n"
        "A100,Foundation,10,5,false,true\n"
    )

    with pytest.raises(APIError):
        parse_activities_csv(csv_text)


def test_parse_activities_csv_rejects_milestone_with_nonzero_duration() -> None:
    csv_text = (
        "activity_id,name,original_duration,remaining_duration,is_milestone,is_completed\n"
        "A300,Handover,1,1,true,false\n"
    )

    with pytest.raises(APIError):
        parse_activities_csv(csv_text)


def test_parse_relationships_csv_rejects_non_fs_type() -> None:
    csv_text = "predecessor_id,successor_id,type,lag\nA100,A200,SS,0\n"

    with pytest.raises(APIError):
        parse_relationships_csv(csv_text)


def test_parse_relationships_csv_rejects_negative_lag() -> None:
    csv_text = "predecessor_id,successor_id,type,lag\nA100,A200,FS,-1\n"

    with pytest.raises(APIError):
        parse_relationships_csv(csv_text)


def test_validate_relationship_references_rejects_unknown_activity() -> None:
    activities = parse_activities_csv(ACTIVITIES_CSV)
    relationships = parse_relationships_csv(
        "predecessor_id,successor_id,type,lag\nA100,A999,FS,0\n"
    )

    with pytest.raises(APIError):
        validate_relationship_references(activities, relationships)


def test_detect_cycle_returns_true_for_dag() -> None:
    activities = parse_activities_csv(ACTIVITIES_CSV)
    relationships = parse_relationships_csv(RELATIONSHIPS_CSV)

    is_dag, cycle_ids = detect_cycle(activities, relationships)

    assert is_dag is True
    assert cycle_ids == []


def test_detect_cycle_returns_false_for_cyclic_graph() -> None:
    activities = parse_activities_csv(ACTIVITIES_CSV)
    relationships = parse_relationships_csv(
        "predecessor_id,successor_id,type,lag\n"
        "A100,A200,FS,0\n"
        "A200,A300,FS,0\n"
        "A300,A100,FS,0\n"
    )

    is_dag, cycle_ids = detect_cycle(activities, relationships)

    assert is_dag is False
    assert set(cycle_ids) == {"A100", "A200", "A300"}
