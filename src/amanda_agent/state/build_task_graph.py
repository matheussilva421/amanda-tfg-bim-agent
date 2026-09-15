"""Derive ``state/task-graph.yaml`` from the canonical phase plans.

The markdown plans are the single source of truth for task identity. This
module parses the ``### Task ... [Pnn-Tnn]`` headings out of
``docs/superpowers/plans/`` and writes the registry the scheduler consumes, so
a plan edit cannot silently desynchronise the graph.
"""

from __future__ import annotations

import re
from pathlib import Path

from .tasks import TaskRecord, TaskRegistry

HEADING = re.compile(
    r"^###\s+Task\s+[^\[]*?\[(?P<id>P\d{2}-T\d{2}|P0[07]-T\d{2})\]",
    re.MULTILINE,
)

PHASE_FOR_PREFIX = {
    "P00": "PHASE_00",
    "P01": "PHASE_01",
    "P02": "PHASE_02",
    "P03": "PHASE_03",
    "P04": "PHASE_04",
    "P05": "PHASE_05",
    "P06": "PHASE_06",
    "P07": "PHASE_07A",
    "P08": "PHASE_08",
    "P09": "PHASE_09",
}

#: Tasks from section 07 that belong to the later 07B integration subset.
SEVEN_B_TASKS = {"P07-T07", "P07-T08", "P07-T09", "P07-T14", "P07-T15",
                 "P07-T17", "P07-T18", "P07-T19"}


def _phase_for(task_id: str) -> str:
    if task_id in SEVEN_B_TASKS:
        return "PHASE_07B"
    return PHASE_FOR_PREFIX[task_id[:3]]


def parse_plan_file(path: Path) -> list:
    """Task records for one plan file, in document order."""
    text = path.read_text(encoding="utf-8")
    records = []
    for match in HEADING.finditer(text):
        task_id = match.group("id")
        line = text[match.start(): text.find("\n", match.start())]
        title = re.sub(r"^###\s+Task\s+[^:]*:\s*", "", line).strip()
        title = re.sub(r"\s*\[[^\]]*\]\s*$", "", title).strip()
        records.append(
            TaskRecord(
                id=task_id,
                phase=_phase_for(task_id),
                plan_path=str(path).replace("\\", "/"),
                title=title,
            )
        )
    return records


def build_registry(plans_dir: Path, *, relative_to: Path | None = None) -> TaskRegistry:
    registry = TaskRegistry()
    plans_dir = Path(plans_dir)
    for plan_file in sorted(plans_dir.glob("*.md")):
        for record in parse_plan_file(plan_file):
            if relative_to is not None:
                record.plan_path = (
                    plan_file.relative_to(relative_to).as_posix()
                )
            if record.id in registry.tasks:
                raise ValueError(
                    "duplicate task id " + record.id + " in " + plan_file.name
                )
            registry.add(record)
    _wire_sequential_dependencies(registry)
    registry.validate()
    return registry


#: Within-phase overrides named explicitly by the master plan. A task listed
#: here keeps only these dependencies instead of the sequential default.
EXPLICIT_DEPENDENCIES = {
    # P06-T15 reviews R14 before promotion, so it hangs off T13, not T14.
    "P06-T15": ["P06-T13"],
    # P06-T14 promotion depends on the P06-T15 visual review.
    "P06-T14": ["P06-T15"],
    # P08-T19 preparation depends on P08-T17 exports; P08-T18 seals after it.
    "P08-T19": ["P08-T17"],
    "P08-T18": ["P08-T19"],
}

#: Cross-phase edges: successor -> extra predecessors.
PHASE_BOUNDARY_DEPENDENCIES = {
    "P02-T01": ["P07-T13"],
    "P04-T01": ["P03-T15"],
    "P05-T01": ["P02-T20", "P04-T22"],
    "P06-T01": ["P05-T23"],
    "P07-T07": ["P06-T15"],
    "P08-T01": ["P06-T15", "P07-T19"],
    "P09-T01": ["P08-T19"],
}


def _wire_sequential_dependencies(registry: TaskRegistry) -> None:
    """Within a phase, a task hard-depends on the previous one in the plan.

    The master plan states numeric order is reading order rather than an
    implicit dependency, and names explicit exceptions. Those exceptions are
    recorded here, once, instead of being re-derived from prose.
    """
    by_phase: dict = {}
    for record in registry.tasks.values():
        by_phase.setdefault(record.phase, []).append(record.id)

    for phase, task_ids in by_phase.items():
        ordered = sorted(task_ids)
        for previous, current in zip(ordered, ordered[1:]):
            if current in EXPLICIT_DEPENDENCIES:
                continue
            registry.tasks[current].depends_on = [previous]

    for task_id, dependencies in EXPLICIT_DEPENDENCIES.items():
        if task_id in registry.tasks:
            registry.tasks[task_id].depends_on = list(dependencies)

    for successor, predecessors in PHASE_BOUNDARY_DEPENDENCIES.items():
        if successor not in registry.tasks:
            continue
        for predecessor in predecessors:
            if predecessor in registry.tasks:
                registry.tasks[successor].depends_on.append(predecessor)


def main() -> int:
    root = Path(__file__).resolve().parents[3]
    registry = build_registry(
        root / "docs" / "superpowers" / "plans", relative_to=root
    )
    target = root / "state" / "task-graph.yaml"
    registry.save(target)
    print("wrote " + str(target) + " with " + str(len(registry.tasks)) + " tasks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
