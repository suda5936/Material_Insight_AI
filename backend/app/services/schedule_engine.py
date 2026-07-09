"""결정론적 일정 엔진 (CPM) — LLM이 아닌 "도구(Tool)".

[수업 정리] LLM은 계산을 못 믿는다 → 계산은 결정론적 Tool에 맡긴다.
------------------------------------------------------------------
LLM은 산술/그래프 계산에서 환각(잘못된 수치)을 낸다. 그래서 이 프로젝트의 철칙은
"일정 수치는 전부 이 엔진(Python + NetworkX)이 계산하고 LLM은 손대지 않는다"이다.

LangChain/LangGraph 관점에서 이 엔진은 에이전트가 호출하는 **Tool**에 해당한다.
    from langchain_core.tools import tool
    @tool
    def compute_cpm(...): ...   # LLM이 아니라 코드가 정확히 계산
차이점: 우리는 LLM이 이 Tool을 "자유롭게 호출"하게 두지 않고, 오케스트레이터가
정해진 순서로 직접 호출한다(신뢰성/재현성 우선). 그래서 같은 입력이면 항상 같은 결과.

구현: CPM(Critical Path Method)
    - Forward pass  : ES/EF (이른 시작/완료)
    - Backward pass : LS/LF (늦은 시작/완료)
    - Total Float = LS - ES, Critical = Float <= 0
    - Impact: START_BLOCK(시작 지연, 가산) / DURATION_INCREASE(기간 증가)
    - Recovery: REDUCE_START_BLOCK / REDUCE_ACTIVITY_DURATION 시뮬레이션
"""

from dataclasses import dataclass
from enum import Enum

import networkx as nx


class ScheduleEngineError(Exception):
    pass


@dataclass(frozen=True)
class ActivityInput:
    activity_id: str
    name: str
    remaining_duration: int
    is_milestone: bool = False
    is_completed: bool = False


@dataclass(frozen=True)
class RelationshipInput:
    predecessor_id: str
    successor_id: str
    lag: int = 0


@dataclass(frozen=True)
class ActivityCalc:
    activity_id: str
    es: int
    ef: int
    ls: int
    lf: int
    total_float: int
    is_critical: bool


@dataclass(frozen=True)
class CPMResult:
    project_duration: int
    activities: dict[str, ActivityCalc]
    critical_path: list[str]


@dataclass(frozen=True)
class ImpactResult:
    target_activity_id: str
    baseline_project_duration: int
    impact_project_duration: int
    project_delay_days: int
    baseline_total_float: int
    impact_total_float: int
    is_target_critical: bool
    critical_path: list[str]
    cpm: CPMResult


class ImpactMode(str, Enum):
    START_BLOCK = "START_BLOCK"
    DURATION_INCREASE = "DURATION_INCREASE"


class RecoveryAction(str, Enum):
    REDUCE_START_BLOCK = "REDUCE_START_BLOCK"
    REDUCE_ACTIVITY_DURATION = "REDUCE_ACTIVITY_DURATION"


@dataclass(frozen=True)
class ScenarioResult:
    action: RecoveryAction
    target_activity_id: str
    reduction_days: int
    adjusted_value_days: int
    impact_project_duration: int
    recovered_days: int
    cpm: CPMResult


class ScheduleGraph:
    def __init__(
        self,
        activities: list[ActivityInput],
        relationships: list[RelationshipInput],
        start_blocks: dict[str, int] | None = None,
    ) -> None:
        self._activities: dict[str, ActivityInput] = {a.activity_id: a for a in activities}
        if len(self._activities) != len(activities):
            raise ScheduleEngineError("Duplicate activity_id in schedule graph input.")

        self._relationships = list(relationships)
        self._start_blocks = dict(start_blocks) if start_blocks else {}

        graph: nx.DiGraph = nx.DiGraph()
        graph.add_nodes_from(self._activities.keys())
        for rel in self._relationships:
            if rel.predecessor_id not in self._activities:
                raise ScheduleEngineError(
                    f"Relationship references unknown predecessor '{rel.predecessor_id}'."
                )
            if rel.successor_id not in self._activities:
                raise ScheduleEngineError(
                    f"Relationship references unknown successor '{rel.successor_id}'."
                )
            if rel.lag < 0:
                raise ScheduleEngineError("Relationship lag must not be negative.")
            graph.add_edge(rel.predecessor_id, rel.successor_id, lag=rel.lag)

        if not nx.is_directed_acyclic_graph(graph):
            raise ScheduleEngineError("Schedule network must be a DAG to run the schedule engine.")

        self._graph = graph
        self._topo_order = list(nx.topological_sort(graph))

    def with_duration_override(self, activity_id: str, new_duration: int) -> "ScheduleGraph":
        activities = [
            ActivityInput(
                activity_id=a.activity_id,
                name=a.name,
                remaining_duration=new_duration if a.activity_id == activity_id else a.remaining_duration,
                is_milestone=a.is_milestone,
                is_completed=a.is_completed,
            )
            for a in self._activities.values()
        ]
        return ScheduleGraph(activities, self._relationships, self._start_blocks)

    def with_start_block(self, activity_id: str, block_days: int) -> "ScheduleGraph":
        start_blocks = dict(self._start_blocks)
        start_blocks[activity_id] = block_days
        return ScheduleGraph(list(self._activities.values()), self._relationships, start_blocks)

    def has_activity(self, activity_id: str) -> bool:
        return activity_id in self._activities

    def remaining_duration(self, activity_id: str) -> int:
        activity = self._activities[activity_id]
        return 0 if activity.is_completed else activity.remaining_duration

    def min_duration(self, activity_id: str) -> int:
        return 0 if self._activities[activity_id].is_milestone else 1

    def compute_cpm(self) -> CPMResult:
        es: dict[str, int] = {}
        ef: dict[str, int] = {}

        for activity_id in self._topo_order:
            preds = list(self._graph.predecessors(activity_id))
            # A start block models a delay that pushes the activity's start
            # LATER than it otherwise would begin (e.g. late material delivery),
            # so it is additive on top of the predecessor-driven early start.
            block = self._start_blocks.get(activity_id, 0)
            if preds:
                candidate = max(ef[p] + self._graph[p][activity_id]["lag"] for p in preds)
            else:
                candidate = 0
            node_es = candidate + block
            duration = self._effective_duration(activity_id)
            es[activity_id] = node_es
            ef[activity_id] = node_es + duration

        project_duration = max(ef.values()) if ef else 0

        lf: dict[str, int] = {}
        ls: dict[str, int] = {}
        for activity_id in reversed(self._topo_order):
            succs = list(self._graph.successors(activity_id))
            if succs:
                node_lf = min(ls[s] - self._graph[activity_id][s]["lag"] for s in succs)
            else:
                node_lf = project_duration
            duration = self._effective_duration(activity_id)
            lf[activity_id] = node_lf
            ls[activity_id] = node_lf - duration

        activities: dict[str, ActivityCalc] = {}
        critical_path: list[str] = []
        for activity_id in self._topo_order:
            total_float = ls[activity_id] - es[activity_id]
            is_critical = total_float <= 0
            activities[activity_id] = ActivityCalc(
                activity_id=activity_id,
                es=es[activity_id],
                ef=ef[activity_id],
                ls=ls[activity_id],
                lf=lf[activity_id],
                total_float=total_float,
                is_critical=is_critical,
            )
            if is_critical:
                critical_path.append(activity_id)

        return CPMResult(
            project_duration=project_duration,
            activities=activities,
            critical_path=critical_path,
        )

    def _effective_duration(self, activity_id: str) -> int:
        activity = self._activities[activity_id]
        if activity.is_completed:
            return 0
        return activity.remaining_duration


def compute_start_block_impact(
    graph: ScheduleGraph, baseline: CPMResult, target_activity_id: str, delay_days: int
) -> ImpactResult:
    if delay_days < 0:
        raise ScheduleEngineError("delay_days must not be negative.")
    if target_activity_id not in baseline.activities:
        raise ScheduleEngineError(f"Unknown target activity '{target_activity_id}'.")

    impacted_graph = graph.with_start_block(target_activity_id, delay_days)
    cpm = impacted_graph.compute_cpm()
    return _build_impact_result(target_activity_id, baseline, cpm)


def compute_duration_increase_impact(
    graph: ScheduleGraph, baseline: CPMResult, target_activity_id: str, delay_days: int
) -> ImpactResult:
    if delay_days < 0:
        raise ScheduleEngineError("delay_days must not be negative.")
    if target_activity_id not in baseline.activities:
        raise ScheduleEngineError(f"Unknown target activity '{target_activity_id}'.")

    current_duration = graph._activities[target_activity_id].remaining_duration
    impacted_graph = graph.with_duration_override(target_activity_id, current_duration + delay_days)
    cpm = impacted_graph.compute_cpm()
    return _build_impact_result(target_activity_id, baseline, cpm)


def _build_impact_result(target_activity_id: str, baseline: CPMResult, cpm: CPMResult) -> ImpactResult:
    baseline_calc = baseline.activities[target_activity_id]
    impact_calc = cpm.activities[target_activity_id]
    return ImpactResult(
        target_activity_id=target_activity_id,
        baseline_project_duration=baseline.project_duration,
        impact_project_duration=cpm.project_duration,
        project_delay_days=cpm.project_duration - baseline.project_duration,
        baseline_total_float=baseline_calc.total_float,
        impact_total_float=impact_calc.total_float,
        is_target_critical=impact_calc.is_critical,
        critical_path=cpm.critical_path,
        cpm=cpm,
    )


def simulate_reduce_start_block(
    graph: ScheduleGraph,
    target_activity_id: str,
    issue_delay_days: int,
    reduction_days: int,
) -> ScenarioResult:
    if reduction_days < 0:
        raise ScheduleEngineError("reduction_days must not be negative.")

    adjusted_block = max(0, issue_delay_days - reduction_days)
    full_impact_graph = graph.with_start_block(target_activity_id, issue_delay_days)
    full_impact_duration = full_impact_graph.compute_cpm().project_duration

    scenario_graph = graph.with_start_block(target_activity_id, adjusted_block)
    scenario_cpm = scenario_graph.compute_cpm()

    return ScenarioResult(
        action=RecoveryAction.REDUCE_START_BLOCK,
        target_activity_id=target_activity_id,
        reduction_days=reduction_days,
        adjusted_value_days=adjusted_block,
        impact_project_duration=scenario_cpm.project_duration,
        recovered_days=full_impact_duration - scenario_cpm.project_duration,
        cpm=scenario_cpm,
    )


def simulate_reduce_activity_duration(
    graph: ScheduleGraph,
    target_activity_id: str,
    current_duration: int,
    reduction_days: int,
    min_duration: int = 1,
) -> ScenarioResult:
    if reduction_days < 0:
        raise ScheduleEngineError("reduction_days must not be negative.")

    full_impact_graph = graph.with_duration_override(target_activity_id, current_duration)
    full_impact_duration = full_impact_graph.compute_cpm().project_duration

    adjusted_duration = max(min_duration, current_duration - reduction_days)
    scenario_graph = graph.with_duration_override(target_activity_id, adjusted_duration)
    scenario_cpm = scenario_graph.compute_cpm()

    return ScenarioResult(
        action=RecoveryAction.REDUCE_ACTIVITY_DURATION,
        target_activity_id=target_activity_id,
        reduction_days=reduction_days,
        adjusted_value_days=adjusted_duration,
        impact_project_duration=scenario_cpm.project_duration,
        recovered_days=full_impact_duration - scenario_cpm.project_duration,
        cpm=scenario_cpm,
    )


# --- Orchestration-level helpers (impact-mode aware) -----------------------------


@dataclass(frozen=True)
class ScenarioSimulation:
    action: RecoveryAction
    reduction_days: int
    adjusted_value_days: int
    scenario_project_duration: int
    recovered_days: int
    applicable: bool


def apply_issue_impact(
    baseline_graph: ScheduleGraph,
    impact_mode: ImpactMode,
    target_activity_id: str,
    delay_days: int,
) -> ScheduleGraph:
    """Return the graph with the reported issue applied to the target activity."""
    if delay_days < 0:
        raise ScheduleEngineError("delay_days must not be negative.")
    if impact_mode == ImpactMode.START_BLOCK:
        return baseline_graph.with_start_block(target_activity_id, delay_days)
    current = baseline_graph.remaining_duration(target_activity_id)
    return baseline_graph.with_duration_override(target_activity_id, current + delay_days)


def simulate_scenario(
    baseline_graph: ScheduleGraph,
    impacted_graph: ScheduleGraph,
    impacted_duration: int,
    impact_mode: ImpactMode,
    target_activity_id: str,
    delay_days: int,
    action: RecoveryAction,
    reduction_days: int,
) -> ScenarioSimulation:
    """Apply one recovery action on top of the impacted schedule and measure
    recovered days = impacted_duration - scenario_duration. The recovery is
    only meaningful when the action matches how the issue was applied; when it
    does not (e.g. REDUCE_START_BLOCK on a DURATION_INCREASE issue) the scenario
    is reported as not applicable with zero recovery."""
    if reduction_days < 0:
        raise ScheduleEngineError("reduction_days must not be negative.")

    min_dur = baseline_graph.min_duration(target_activity_id)

    if action == RecoveryAction.REDUCE_START_BLOCK and impact_mode == ImpactMode.START_BLOCK:
        adjusted = max(0, delay_days - reduction_days)
        scenario_graph = baseline_graph.with_start_block(target_activity_id, adjusted)
        applicable = True
    elif action == RecoveryAction.REDUCE_ACTIVITY_DURATION:
        current = impacted_graph.remaining_duration(target_activity_id)
        adjusted = max(min_dur, current - reduction_days)
        scenario_graph = impacted_graph.with_duration_override(target_activity_id, adjusted)
        applicable = True
    else:
        # Action does not match the impact mode; no recovery can be applied.
        adjusted = delay_days if action == RecoveryAction.REDUCE_START_BLOCK else (
            impacted_graph.remaining_duration(target_activity_id)
        )
        scenario_graph = impacted_graph
        applicable = False

    scenario_duration = scenario_graph.compute_cpm().project_duration
    return ScenarioSimulation(
        action=action,
        reduction_days=reduction_days,
        adjusted_value_days=adjusted,
        scenario_project_duration=scenario_duration,
        recovered_days=impacted_duration - scenario_duration,
        applicable=applicable,
    )
