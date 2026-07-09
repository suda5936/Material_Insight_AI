import csv
import io

import networkx as nx

from app.core.errors import APIError

ACTIVITY_COLUMNS = {
    "activity_id",
    "name",
    "original_duration",
    "remaining_duration",
    "is_milestone",
    "is_completed",
}
RELATIONSHIP_COLUMNS = {"predecessor_id", "successor_id", "type", "lag"}

ALLOWED_RELATIONSHIP_TYPES = {"FS"}
TRUE_VALUES = {"1", "true", "True", "TRUE", "yes", "y"}


class ParsedActivity:
    def __init__(
        self,
        activity_id: str,
        name: str,
        original_duration: int,
        remaining_duration: int,
        is_milestone: bool,
        is_completed: bool,
    ) -> None:
        self.activity_id = activity_id
        self.name = name
        self.original_duration = original_duration
        self.remaining_duration = remaining_duration
        self.is_milestone = is_milestone
        self.is_completed = is_completed


class ParsedRelationship:
    def __init__(self, predecessor_id: str, successor_id: str, type_: str, lag: int) -> None:
        self.predecessor_id = predecessor_id
        self.successor_id = successor_id
        self.type = type_
        self.lag = lag


def _invalid(message: str, details: dict[str, object] | None = None) -> APIError:
    return APIError(
        status_code=422,
        error_code="invalid_schedule_input",
        message=message,
        details=details,
    )


def _read_csv_rows(raw_csv: str, required_columns: set[str], source: str) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(raw_csv))
    if reader.fieldnames is None:
        raise _invalid(f"{source} CSV has no header row.")

    missing = required_columns - set(reader.fieldnames)
    if missing:
        raise _invalid(
            f"{source} CSV is missing required columns.",
            details={"missing_columns": sorted(missing)},
        )

    rows = [row for row in reader]
    if not rows:
        raise _invalid(f"{source} CSV has no data rows.")
    return rows


def _parse_int(value: str, field: str, row_index: int) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        raise _invalid(
            f"Field '{field}' must be an integer.",
            details={"row": row_index, "value": value},
        ) from None


def _parse_bool(value: str) -> bool:
    return str(value).strip() in TRUE_VALUES


def parse_activities_csv(raw_csv: str) -> list[ParsedActivity]:
    rows = _read_csv_rows(raw_csv, ACTIVITY_COLUMNS, "Activity")

    activities: list[ParsedActivity] = []
    seen_ids: set[str] = set()
    for index, row in enumerate(rows, start=2):
        activity_id = row["activity_id"].strip()
        if not activity_id:
            raise _invalid("Activity row is missing activity_id.", details={"row": index})
        if activity_id in seen_ids:
            raise _invalid(
                "Duplicate activity_id found in Activity CSV.",
                details={"activity_id": activity_id},
            )
        seen_ids.add(activity_id)

        name = row["name"].strip()
        if not name:
            raise _invalid("Activity row is missing name.", details={"row": index, "activity_id": activity_id})

        is_milestone = _parse_bool(row["is_milestone"])
        is_completed = _parse_bool(row["is_completed"])
        original_duration = _parse_int(row["original_duration"], "original_duration", index)
        remaining_duration = _parse_int(row["remaining_duration"], "remaining_duration", index)

        if original_duration < 0 or remaining_duration < 0:
            raise _invalid(
                "Activity durations must not be negative.",
                details={"row": index, "activity_id": activity_id},
            )
        if is_milestone and (original_duration != 0 or remaining_duration != 0):
            raise _invalid(
                "Milestone activity duration must be 0.",
                details={"row": index, "activity_id": activity_id},
            )
        if not is_milestone and original_duration < 1:
            raise _invalid(
                "Non-milestone activity original_duration must be at least 1.",
                details={"row": index, "activity_id": activity_id},
            )
        if is_completed and remaining_duration != 0:
            raise _invalid(
                "Completed activity remaining_duration must be 0.",
                details={"row": index, "activity_id": activity_id},
            )

        activities.append(
            ParsedActivity(
                activity_id=activity_id,
                name=name,
                original_duration=original_duration,
                remaining_duration=remaining_duration,
                is_milestone=is_milestone,
                is_completed=is_completed,
            )
        )

    return activities


def parse_relationships_csv(raw_csv: str) -> list[ParsedRelationship]:
    rows = _read_csv_rows(raw_csv, RELATIONSHIP_COLUMNS, "Relationship")

    relationships: list[ParsedRelationship] = []
    for index, row in enumerate(rows, start=2):
        predecessor_id = row["predecessor_id"].strip()
        successor_id = row["successor_id"].strip()
        rel_type = row["type"].strip().upper()

        if not predecessor_id or not successor_id:
            raise _invalid(
                "Relationship row is missing predecessor_id or successor_id.",
                details={"row": index},
            )
        if rel_type not in ALLOWED_RELATIONSHIP_TYPES:
            raise _invalid(
                "Only FS relationships are supported in the MVP.",
                details={"row": index, "type": rel_type},
            )

        lag = _parse_int(row["lag"], "lag", index)
        if lag < 0:
            raise _invalid(
                "Relationship lag must not be negative.",
                details={"row": index, "predecessor_id": predecessor_id, "successor_id": successor_id},
            )

        relationships.append(
            ParsedRelationship(
                predecessor_id=predecessor_id,
                successor_id=successor_id,
                type_=rel_type,
                lag=lag,
            )
        )

    return relationships


def validate_relationship_references(
    activities: list[ParsedActivity], relationships: list[ParsedRelationship]
) -> None:
    activity_ids = {activity.activity_id for activity in activities}
    for relationship in relationships:
        if relationship.predecessor_id not in activity_ids:
            raise _invalid(
                "Relationship references unknown predecessor activity_id.",
                details={"activity_id": relationship.predecessor_id},
            )
        if relationship.successor_id not in activity_ids:
            raise _invalid(
                "Relationship references unknown successor activity_id.",
                details={"activity_id": relationship.successor_id},
            )
        if relationship.predecessor_id == relationship.successor_id:
            raise _invalid(
                "Relationship cannot connect an activity to itself.",
                details={"activity_id": relationship.predecessor_id},
            )


def detect_cycle(
    activities: list[ParsedActivity], relationships: list[ParsedRelationship]
) -> tuple[bool, list[str]]:
    graph: nx.DiGraph = nx.DiGraph()
    graph.add_nodes_from(activity.activity_id for activity in activities)
    graph.add_edges_from(
        (relationship.predecessor_id, relationship.successor_id) for relationship in relationships
    )

    is_dag = nx.is_directed_acyclic_graph(graph)
    if is_dag:
        return True, []

    cycle_ids: set[str] = set()
    for cycle in nx.simple_cycles(graph):
        cycle_ids.update(cycle)
    return False, sorted(cycle_ids)
