import pytest

from app.services.schedule_engine import (
    ActivityInput,
    RelationshipInput,
    ScheduleEngineError,
    ScheduleGraph,
    compute_duration_increase_impact,
    compute_start_block_impact,
    simulate_reduce_activity_duration,
    simulate_reduce_start_block,
)


def _linear_chain_graph() -> ScheduleGraph:
    activities = [
        ActivityInput("A", "Foundation", 5),
        ActivityInput("B", "Structure", 3),
        ActivityInput("C", "Finishes", 2),
    ]
    relationships = [
        RelationshipInput("A", "B", lag=0),
        RelationshipInput("B", "C", lag=0),
    ]
    return ScheduleGraph(activities, relationships)


def test_linear_chain_forward_backward_pass() -> None:
    graph = _linear_chain_graph()
    cpm = graph.compute_cpm()

    assert cpm.project_duration == 10
    assert cpm.activities["A"].es == 0
    assert cpm.activities["A"].ef == 5
    assert cpm.activities["B"].es == 5
    assert cpm.activities["B"].ef == 8
    assert cpm.activities["C"].es == 8
    assert cpm.activities["C"].ef == 10
    for activity_id in ("A", "B", "C"):
        assert cpm.activities[activity_id].total_float == 0
        assert cpm.activities[activity_id].is_critical is True
    assert cpm.critical_path == ["A", "B", "C"]


def test_lag_delays_successor_start() -> None:
    activities = [ActivityInput("A", "A", 5), ActivityInput("B", "B", 3)]
    relationships = [RelationshipInput("A", "B", lag=4)]
    graph = ScheduleGraph(activities, relationships)

    cpm = graph.compute_cpm()

    assert cpm.activities["B"].es == 9
    assert cpm.project_duration == 12


def test_branch_and_parallel_paths_produce_near_critical_float() -> None:
    activities = [
        ActivityInput("A", "Start", 2),
        ActivityInput("B", "Short branch", 3),
        ActivityInput("C", "Long branch", 8),
        ActivityInput("D", "Join", 1),
    ]
    relationships = [
        RelationshipInput("A", "B", lag=0),
        RelationshipInput("A", "C", lag=0),
        RelationshipInput("B", "D", lag=0),
        RelationshipInput("C", "D", lag=0),
    ]
    graph = ScheduleGraph(activities, relationships)

    cpm = graph.compute_cpm()

    assert cpm.project_duration == 11
    assert cpm.activities["C"].is_critical is True
    assert cpm.activities["B"].is_critical is False
    assert cpm.activities["B"].total_float == 5
    assert cpm.critical_path == ["A", "C", "D"]


def test_milestone_has_zero_duration() -> None:
    activities = [
        ActivityInput("A", "Work", 5),
        ActivityInput("M", "Milestone", 0, is_milestone=True),
    ]
    relationships = [RelationshipInput("A", "M", lag=0)]
    graph = ScheduleGraph(activities, relationships)

    cpm = graph.compute_cpm()

    assert cpm.activities["M"].es == 5
    assert cpm.activities["M"].ef == 5
    assert cpm.project_duration == 5


def test_completed_activity_has_zero_remaining_duration_regardless_of_field() -> None:
    activities = [
        ActivityInput("A", "Done", 5, is_completed=True),
        ActivityInput("B", "Next", 3),
    ]
    relationships = [RelationshipInput("A", "B", lag=0)]
    graph = ScheduleGraph(activities, relationships)

    cpm = graph.compute_cpm()

    assert cpm.activities["A"].ef == 0
    assert cpm.activities["B"].es == 0
    assert cpm.project_duration == 3


def test_cycle_raises_schedule_engine_error() -> None:
    activities = [ActivityInput("A", "A", 1), ActivityInput("B", "B", 1)]
    relationships = [
        RelationshipInput("A", "B", lag=0),
        RelationshipInput("B", "A", lag=0),
    ]

    with pytest.raises(ScheduleEngineError):
        ScheduleGraph(activities, relationships)


def test_unknown_relationship_reference_raises() -> None:
    activities = [ActivityInput("A", "A", 1)]
    relationships = [RelationshipInput("A", "Z", lag=0)]

    with pytest.raises(ScheduleEngineError):
        ScheduleGraph(activities, relationships)


def test_start_block_impact_delays_project_and_downstream() -> None:
    graph = _linear_chain_graph()
    baseline = graph.compute_cpm()

    impact = compute_start_block_impact(graph, baseline, target_activity_id="B", delay_days=10)

    assert impact.baseline_project_duration == 10
    # B's natural ES from predecessor A is 5; a 10-day start block is additive,
    # pushing B's ES to 15 and growing the project by the full 10 days.
    assert impact.impact_project_duration == 20
    assert impact.project_delay_days == 10
    assert impact.is_target_critical is True


def test_duration_increase_impact_extends_project() -> None:
    graph = _linear_chain_graph()
    baseline = graph.compute_cpm()

    impact = compute_duration_increase_impact(graph, baseline, target_activity_id="B", delay_days=4)

    assert impact.baseline_project_duration == 10
    assert impact.impact_project_duration == 14
    assert impact.project_delay_days == 4


def test_simulate_reduce_start_block_recovers_days() -> None:
    graph = _linear_chain_graph()

    # Full impact (block=10) pushes project duration to 20. Reducing the block
    # to 7 (additive) makes B start at 5+7=12, giving project 17 and recovering 3.
    scenario = simulate_reduce_start_block(
        graph, target_activity_id="B", issue_delay_days=10, reduction_days=3
    )

    assert scenario.adjusted_value_days == 7
    assert scenario.impact_project_duration == 17
    assert scenario.recovered_days == 3


def test_simulate_reduce_start_block_reduction_cannot_go_below_zero() -> None:
    graph = _linear_chain_graph()

    scenario = simulate_reduce_start_block(
        graph, target_activity_id="B", issue_delay_days=5, reduction_days=20
    )

    assert scenario.adjusted_value_days == 0
    assert scenario.impact_project_duration == 10


def test_simulate_reduce_activity_duration_recovers_days_with_min_duration_floor() -> None:
    graph = _linear_chain_graph()

    scenario = simulate_reduce_activity_duration(
        graph,
        target_activity_id="B",
        current_duration=11,
        reduction_days=8,
        min_duration=2,
    )

    assert scenario.adjusted_value_days == 3
    assert scenario.impact_project_duration == 5 + 3 + 2
    full_impact = graph.with_duration_override("B", 11).compute_cpm().project_duration
    assert scenario.recovered_days == full_impact - scenario.impact_project_duration
