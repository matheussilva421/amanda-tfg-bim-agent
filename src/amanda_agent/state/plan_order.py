"""Read-only diagnostics for the reviewed cross-phase task order.

The task registry contains individual task dependencies, while the reviewed
plan also has a small phase-level contract.  This module checks that contract
without writing to the registry and evaluates the two pre-production branches
independently.  A Revit/tool blocker therefore cannot become a blocker for
source reconciliation or synthetic solver work merely through aggregation.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

from ..models.state import TaskStatus
from .tasks import TaskRegistry, load_registry

# Each tuple is (predecessor phase, successor phase).  The optional rendering
# phase is checked only when it is present in the task registry.
REQUIRED_PHASE_DEPENDENCIES: tuple[tuple[str, str], ...] = (
    ("PHASE_01", "PHASE_07A"),
    ("PHASE_07A", "PHASE_02"),
    ("PHASE_01", "PHASE_03"),
    ("PHASE_03", "PHASE_04"),
    ("PHASE_02", "PHASE_05"),
    ("PHASE_04", "PHASE_05"),
    ("PHASE_05", "PHASE_06"),
    ("PHASE_06", "PHASE_07B"),
    ("PHASE_07B", "PHASE_08"),
)
OPTIONAL_PHASE_DEPENDENCIES: tuple[tuple[str, str], ...] = (
    ("PHASE_08", "PHASE_09"),
)

# PHASE_00 is a local verification chain.  It is allowed to feed the normal
# route if a future registry records that relationship, but it is not part of
# the reviewed Phase 01--09 contract and is not required here.
ALLOWED_AUXILIARY_DEPENDENCIES: tuple[tuple[str, str], ...] = (
    ("PHASE_00", "PHASE_01"),
)

BRANCH_PHASES: Mapping[str, tuple[str, ...]] = {
    "revit": ("PHASE_01", "PHASE_07A", "PHASE_02"),
    "solver": ("PHASE_01", "PHASE_03", "PHASE_04"),
    "production": (
        "PHASE_01",
        "PHASE_07A",
        "PHASE_02",
        "PHASE_03",
        "PHASE_04",
        "PHASE_05",
        "PHASE_06",
        "PHASE_07B",
        "PHASE_08",
    ),
}

PASS_STATUSES = frozenset(
    {TaskStatus.PASS, TaskStatus.PASS_WITH_WARNINGS}
)
BLOCKING_STATUSES = frozenset(
    {
        TaskStatus.BLOCKED_BY_INPUT,
        TaskStatus.BLOCKED_BY_TOOL,
        TaskStatus.CRITICAL_FAILURE,
    }
)


@dataclass(frozen=True)
class PlanOrderIssue:
    """One deterministic topology or registry diagnostic."""

    code: str
    message: str
    predecessor_phase: str | None = None
    successor_phase: str | None = None
    task_id: str | None = None

    def as_dict(self) -> dict[str, str | None]:
        return {
            "code": self.code,
            "message": self.message,
            "predecessor_phase": self.predecessor_phase,
            "successor_phase": self.successor_phase,
            "task_id": self.task_id,
        }


@dataclass(frozen=True)
class BranchDiagnostic:
    """Status of one intended deliverable branch."""

    name: str
    phases: tuple[str, ...]
    status: str
    blocking_phases: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "phases": list(self.phases),
            "status": self.status,
            "blocking_phases": list(self.blocking_phases),
        }


@dataclass(frozen=True)
class PlanOrderDiagnostic:
    """Read-only result of :func:`diagnose_plan_order`."""

    phase_edges: tuple[tuple[str, str], ...]
    issues: tuple[PlanOrderIssue, ...]
    branches: Mapping[str, BranchDiagnostic]

    @property
    def passed(self) -> bool:
        """Whether the registry topology satisfies the phase contract."""
        return not self.issues

    def as_dict(self) -> dict[str, object]:
        """Return a stable JSON/YAML-friendly representation."""
        return {
            "passed": self.passed,
            "phase_edges": [list(edge) for edge in self.phase_edges],
            "issues": [issue.as_dict() for issue in self.issues],
            "branches": {
                name: self.branches[name].as_dict()
                for name in sorted(self.branches)
            },
        }


def _registry_from(source: Path | str | TaskRegistry | Mapping) -> TaskRegistry:
    if isinstance(source, TaskRegistry):
        return source
    if isinstance(source, (str, Path)):
        return load_registry(Path(source))
    if isinstance(source, Mapping):
        return TaskRegistry.model_validate(source)
    raise TypeError(
        "plan order source must be a task registry, mapping or YAML path"
    )


def _phase_edges(registry: TaskRegistry) -> tuple[tuple[str, str], ...]:
    edges: set[tuple[str, str]] = set()
    for task_id in sorted(registry.tasks):
        task = registry.tasks[task_id]
        for dependency_id in sorted(set(task.depends_on)):
            dependency = registry.tasks[dependency_id]
            if dependency.phase != task.phase:
                edges.add((dependency.phase, task.phase))
    return tuple(sorted(edges))


def _required_edges(phases: set[str]) -> tuple[tuple[str, str], ...]:
    required = [
        edge
        for edge in REQUIRED_PHASE_DEPENDENCIES
        if edge[0] in phases and edge[1] in phases
    ]
    if "PHASE_09" in phases:
        required.extend(
            edge
            for edge in OPTIONAL_PHASE_DEPENDENCIES
            if edge[0] in phases and edge[1] in phases
        )
    return tuple(sorted(required))


def _contract_reaches(predecessor: str, successor: str) -> bool:
    """Return whether an edge preserves the reviewed phase ordering.

    A direct edge that is already implied by the contract is redundant but
    safe.  For example, the production preflight may retain a direct
    ``PHASE_06 -> PHASE_08`` dependency in addition to the explicit
    ``PHASE_06 -> PHASE_07B -> PHASE_08`` route.
    """
    adjacency: dict[str, set[str]] = {}
    for left, right in REQUIRED_PHASE_DEPENDENCIES + OPTIONAL_PHASE_DEPENDENCIES:
        adjacency.setdefault(left, set()).add(right)

    pending = [predecessor]
    visited: set[str] = set()
    while pending:
        current = pending.pop()
        if current in visited:
            continue
        visited.add(current)
        for following in adjacency.get(current, set()):
            if following == successor:
                return True
            pending.append(following)
    return False


def _phase_statuses(
    registry: TaskRegistry, explicit_blocked: set[str]
) -> dict[str, str]:
    phases = sorted({task.phase for task in registry.tasks.values()})
    statuses: dict[str, str] = {}
    for phase in phases:
        records = [
            registry.tasks[task_id]
            for task_id in sorted(registry.tasks)
            if registry.tasks[task_id].phase == phase
        ]
        task_statuses = {record.status for record in records}
        if phase in explicit_blocked or task_statuses & BLOCKING_STATUSES:
            statuses[phase] = "BLOCKED"
        elif records and task_statuses and task_statuses <= PASS_STATUSES:
            statuses[phase] = "PASS"
        else:
            statuses[phase] = "PENDING"
    return statuses


def _branches(
    registry: TaskRegistry, explicit_blocked: set[str]
) -> Mapping[str, BranchDiagnostic]:
    phase_statuses = _phase_statuses(registry, explicit_blocked)
    result: dict[str, BranchDiagnostic] = {}
    for name, phases in BRANCH_PHASES.items():
        blocking = tuple(
            phase for phase in phases if phase_statuses.get(phase) == "BLOCKED"
        )
        if blocking:
            status = "BLOCKED"
        elif all(phase_statuses.get(phase) == "PASS" for phase in phases):
            status = "PASS"
        else:
            status = "PENDING"
        result[name] = BranchDiagnostic(
            name=name,
            phases=phases,
            status=status,
            blocking_phases=blocking,
        )
    return MappingProxyType(result)


def _registry_issues(registry: TaskRegistry) -> tuple[PlanOrderIssue, ...]:
    try:
        registry.validate()
    except ValueError as exc:
        return (
            PlanOrderIssue(
                code="INVALID_TASK_GRAPH",
                message=str(exc),
            ),
        )
    return ()


def diagnose_plan_order(
    source: Path | str | TaskRegistry | Mapping,
    *,
    blocked_phases: Iterable[str] = (),
) -> PlanOrderDiagnostic:
    """Diagnose phase ordering and branch isolation without mutating ``source``.

    ``source`` may be the repository's ``state/task-graph.yaml`` path, an
    existing :class:`TaskRegistry`, or a registry-shaped mapping.  The
    optional ``blocked_phases`` parameter represents an external gate such as
    an unavailable provider; it affects branch reporting only and never edits
    task statuses.
    """
    registry = _registry_from(source)
    graph_issues = _registry_issues(registry)
    explicit_blocked = set(blocked_phases)
    if graph_issues:
        return PlanOrderDiagnostic(
            phase_edges=(),
            issues=graph_issues,
            branches=_branches(registry, explicit_blocked),
        )

    edges = _phase_edges(registry)
    edge_set = set(edges)
    phases = {task.phase for task in registry.tasks.values()}
    issues: list[PlanOrderIssue] = []

    expected_phases = {
        phase
        for edge in REQUIRED_PHASE_DEPENDENCIES
        for phase in edge
    }
    for phase in sorted(expected_phases - phases):
        issues.append(
            PlanOrderIssue(
                code="MISSING_PHASE",
                message="required phase is absent from the task graph: " + phase,
                successor_phase=phase,
            )
        )

    for predecessor, successor in _required_edges(phases):
        if (predecessor, successor) not in edge_set:
            issues.append(
                PlanOrderIssue(
                    code="MISSING_PHASE_DEPENDENCY",
                    message=(
                        "phase "
                        + successor
                        + " has no task dependency on phase "
                        + predecessor
                    ),
                    predecessor_phase=predecessor,
                    successor_phase=successor,
                )
            )

    for predecessor, successor in edges:
        if (predecessor, successor) not in set(ALLOWED_AUXILIARY_DEPENDENCIES) and not _contract_reaches(
            predecessor, successor
        ):
            issues.append(
                PlanOrderIssue(
                    code="UNEXPECTED_PHASE_DEPENDENCY",
                    message=(
                        "phase "
                        + successor
                        + " depends on phase "
                        + predecessor
                        + " outside the reviewed contract"
                    ),
                    predecessor_phase=predecessor,
                    successor_phase=successor,
                )
            )

    ordered_issues = tuple(
        sorted(
            issues,
            key=lambda issue: (
                issue.code,
                issue.predecessor_phase or "",
                issue.successor_phase or "",
                issue.task_id or "",
                issue.message,
            ),
        )
    )
    return PlanOrderDiagnostic(
        phase_edges=edges,
        issues=ordered_issues,
        branches=_branches(registry, explicit_blocked),
    )


def verify_plan_order(
    source: Path | str | TaskRegistry | Mapping,
    *,
    blocked_phases: Iterable[str] = (),
) -> PlanOrderDiagnostic:
    """Compatibility spelling for callers that expect a verification verb."""
    return diagnose_plan_order(source, blocked_phases=blocked_phases)
