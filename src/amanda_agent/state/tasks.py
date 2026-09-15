"""Task-level dependency graph.

Phase ids in the program graph are coarse. This module carries the individual
``Pnn-Tnn`` tasks: which plan file defines them, what they hard-depend on and
where they stand. A task becomes READY only after every hard dependency
reached PASS or PASS_WITH_WARNINGS. A dependency that lost its input
(``BLOCKED_BY_INPUT``) propagates to its own dependents only, so an unrelated
branch keeps moving.

This is the module Plan 01 promised and Plan 07A extends; there is no second
competing implementation.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from ..models.state import TaskStatus

SCHEMA_VERSION = 1

#: Statuses that satisfy a hard dependency.
SATISFIED: frozenset = frozenset(
    {TaskStatus.PASS, TaskStatus.PASS_WITH_WARNINGS}
)

#: Statuses that stop downstream work for the same reason.
UNSATISFIABLE: frozenset = frozenset(
    {
        TaskStatus.BLOCKED_BY_INPUT,
        TaskStatus.BLOCKED_BY_TOOL,
        TaskStatus.CRITICAL_FAILURE,
    }
)


class TaskRecord(BaseModel):
    """One schedulable unit of work."""

    id: str
    phase: str
    plan_path: str
    title: str = ""
    depends_on: list[str] = Field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    evidence: list[str] = Field(default_factory=list)


class TaskRegistry(BaseModel):
    schema_version: int = SCHEMA_VERSION
    tasks: dict[str, TaskRecord] = Field(default_factory=dict)

    # -- building ------------------------------------------------------
    def add(self, record: TaskRecord) -> None:
        self.tasks[record.id] = record

    def set_status(self, task_id: str, status: TaskStatus) -> TaskRecord:
        if task_id not in self.tasks:
            raise KeyError("unknown task " + task_id)
        # Coerce so a plain "PASS" from a caller or a YAML round-trip keeps the
        # field a real enum instead of a bare string that serialises oddly.
        self.tasks[task_id].status = TaskStatus(status)
        return self.tasks[task_id]

    def add_evidence(self, task_id: str, reference: str) -> None:
        if task_id not in self.tasks:
            raise KeyError("unknown task " + task_id)
        self.tasks[task_id].evidence.append(reference)

    def unready_dependencies(self, task_id: str) -> list:
        """Hard dependencies of ``task_id`` that have not reached a pass yet.

        Read-only: the caller decides whether the unfinished predecessor is a
        reason to stop or a limitation to record. Keeping the check here means
        the graph and the writer cannot disagree about what "dependency" means.
        """
        if task_id not in self.tasks:
            raise KeyError("unknown task " + task_id)
        return sorted(
            dependency
            for dependency in self.tasks[task_id].depends_on
            if self.tasks[dependency].status not in SATISFIED
        )

    # -- validation ----------------------------------------------------
    def validate(self) -> None:
        for record in self.tasks.values():
            for dependency in record.depends_on:
                if dependency not in self.tasks:
                    raise ValueError(
                        "task "
                        + record.id
                        + " depends on unknown task "
                        + dependency
                    )
        self._reject_cycles()

    def _reject_cycles(self) -> None:
        colour = {task_id: 0 for task_id in self.tasks}

        def visit(task_id: str, path: list) -> None:
            colour[task_id] = 1
            for dependency in self.tasks[task_id].depends_on:
                if colour[dependency] == 1:
                    raise ValueError(
                        "dependency cycle: "
                        + " -> ".join(path + [task_id, dependency])
                    )
                if colour[dependency] == 0:
                    visit(dependency, path + [task_id])
            colour[task_id] = 2

        for task_id in list(self.tasks):
            if colour[task_id] == 0:
                visit(task_id, [])

    # -- scheduling ----------------------------------------------------
    def ready_tasks(self) -> list:
        """Pending tasks whose hard dependencies are all satisfied."""
        ready = []
        for record in self.tasks.values():
            if record.status != TaskStatus.PENDING:
                continue
            if all(
                self.tasks[dependency].status in SATISFIED
                for dependency in record.depends_on
            ):
                ready.append(record.id)
        return sorted(ready)

    def parallel_ready_tasks(self) -> list:
        return self.ready_tasks()

    def parallel_batches(self) -> list:
        """Ready tasks grouped into batches of tasks with no relation.

        Only tasks that are not ancestors/descendants of each other can run at
        once; the first batch is therefore maximal but never self-conflicting.
        """
        ready = self.ready_tasks()
        batches: list = []
        remaining = list(ready)
        while remaining:
            batch: list = []
            for candidate in remaining:
                if all(
                    not self._related(candidate, chosen)
                    for chosen in batch
                ):
                    batch.append(candidate)
            batches.append(sorted(batch))
            remaining = [task_id for task_id in remaining if task_id not in batch]
        return batches

    def _ancestors(self, task_id: str, seen: set) -> set:
        for dependency in self.tasks[task_id].depends_on:
            if dependency not in seen:
                seen.add(dependency)
                self._ancestors(dependency, seen)
        return seen

    def _related(self, left: str, right: str) -> bool:
        return right in self._ancestors(left, set()) or left in self._ancestors(
            right, set()
        )

    def propagate(self) -> None:
        """Carry an unsatisfiable dependency forward to its dependents."""
        changed = True
        while changed:
            changed = False
            for record in self.tasks.values():
                if record.status not in {TaskStatus.PENDING, TaskStatus.READY}:
                    continue
                for dependency in record.depends_on:
                    upstream = self.tasks[dependency].status
                    if upstream in UNSATISFIABLE:
                        record.status = upstream
                        changed = True
                        break

    # -- persistence ---------------------------------------------------
    def save(self, path: Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = yaml.safe_dump(
            self.model_dump(mode="json"), sort_keys=False, allow_unicode=True
        )
        path.write_text(payload, encoding="utf-8")


def load_registry(path: Path) -> TaskRegistry:
    """Load the registry. A missing file is an error, never a fresh graph."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError("task registry not found: " + str(path))
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return TaskRegistry(**raw)
