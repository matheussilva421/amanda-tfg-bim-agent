"""Typed blocker and task-graph models.

These live here, not in the autonomy phase, because the resume command must be
usable from the start. Plan 07A extends this module rather than growing a
second, competing implementation.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class Severity(StrEnum):
    BLOCKING = "BLOCKING"
    DEGRADING = "DEGRADING"
    INFORMATIONAL = "INFORMATIONAL"


class Blocker(BaseModel):
    """A typed obstacle.

    Severity is an explicit field. Inferring it from a string prefix would let
    an innocuous name look fatal and a fatal one look harmless.
    """

    id: str
    summary: str
    severity: Severity
    owner_phase: str | None = None
    affected_tasks: list[str] = Field(default_factory=list)
    evidence: str | None = None
    resolution: str | None = None
    requires_user_action: bool = False
    created_utc: str | None = None
    resolved_utc: str | None = None

    @property
    def is_open(self) -> bool:
        return self.resolved_utc is None


class TaskNode(BaseModel):
    id: str
    name: str
    phase_id: str
    depends_on: list[str] = Field(default_factory=list)


class TaskGraph(BaseModel):
    nodes: dict[str, TaskNode] = Field(default_factory=dict)

    def add(self, node: TaskNode) -> None:
        self.nodes[node.id] = node

    def validate_graph(self) -> None:
        """Reject unknown dependencies and cycles before any scheduling."""
        for node in self.nodes.values():
            for dependency in node.depends_on:
                if dependency not in self.nodes:
                    raise ValueError(
                        "task " + node.id + " depends on unknown task " + dependency
                    )
        self._reject_cycles()

    def _reject_cycles(self) -> None:
        white, grey, black = 0, 1, 2
        colour = {task_id: white for task_id in self.nodes}

        def visit(task_id: str, path: list) -> None:
            colour[task_id] = grey
            for dependency in self.nodes[task_id].depends_on:
                if colour[dependency] == grey:
                    raise ValueError(
                        "dependency cycle: "
                        + " -> ".join(path + [task_id, dependency])
                    )
                if colour[dependency] == white:
                    visit(dependency, path + [task_id])
            colour[task_id] = black

        for task_id in list(self.nodes):
            if colour[task_id] == white:
                visit(task_id, [])

    def blocked_tasks(self, blockers: list) -> set:
        """Tasks blocked by an open blocking blocker, transitively."""
        blocked = set()
        for blocker in blockers:
            if blocker.is_open and blocker.severity == Severity.BLOCKING:
                blocked.update(blocker.affected_tasks)
        changed = True
        while changed:
            changed = False
            for node in self.nodes.values():
                if node.id in blocked:
                    continue
                if any(dependency in blocked for dependency in node.depends_on):
                    blocked.add(node.id)
                    changed = True
        return blocked

    def runnable_tasks(self, blockers: list) -> list:
        blocked = self.blocked_tasks(blockers)
        return sorted(
            node.id for node in self.nodes.values() if node.id not in blocked
        )
