"""Derive ``state/task-graph.yaml`` from the canonical phase plans.

The markdown plans are the single source of truth for task identity. This
module parses the ``### Task ... [Pnn-Tnn]`` headings out of
``docs/superpowers/plans/`` and writes the registry the scheduler consumes, so
a plan edit cannot silently desynchronise the graph.
"""

from __future__ import annotations

import re
from pathlib import Path

from .tasks import TaskRecord, TaskRegistry, load_registry

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

#: Fields a plan owns. Status and evidence belong to the task history, not to
#: the plan text, so a derivation must never fabricate them.
_PLAN_OWNED = ("phase", "plan_path", "title")


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
    """A fresh registry for the plans, with every task at PENDING."""
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


def regenerate(plans_dir: Path, target: Path) -> TaskRegistry:
    """Rewrite ``target`` from the plans while keeping recorded outcomes.

    Rebuilding from the plans alone would reset the whole registry to PENDING
    and drop the evidence of every finished task, which is exactly the kind of
    quiet progress loss this repository is meant to prevent. Dependencies and
    the plan-owned fields come from the plans; status and evidence are carried
    over per task id, and a task the plans no longer contain is reported rather
    than dropped silently.
    """
    target = Path(target)
    derived = build_registry(plans_dir, relative_to=target.parent.parent)
    if target.exists():
        existing = load_registry(target)
        for task_id, record in derived.tasks.items():
            kept = existing.tasks.get(task_id)
            if kept is None:
                continue
            record.status = kept.status
            record.evidence = list(kept.evidence)
        orphans = sorted(set(existing.tasks) - set(derived.tasks))
        if orphans:
            print("plans no longer define: " + " ".join(orphans))
    derived.validate()
    derived.save(target)
    return derived


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
#:
#: The master plan's phase graph (01 -> 07A -> 02; 01 -> 03 -> 04;
#: (02 + 04) -> 05 -> 06 -> 07B -> 08) is stated at *phase* level, so two of
#: its edges have no counterpart in the within-phase sequential default:
#: nothing in the reviewed plan makes P03-T01 follow P01-T13, nor P07-T01
#: either. They are pinned here, once, so the phase contract is not left to a
#: reader's inference. PHASE_00 is deliberately absent: it is the local
#: verification chain, not a predecessor of the normal route.
PHASE_BOUNDARY_DEPENDENCIES = {
    "P02-T01": ["P07-T13"],
    "P03-T01": ["P01-T13"],
    "P04-T01": ["P03-T15"],
    "P05-T01": ["P02-T20", "P04-T22"],
    "P06-T01": ["P05-T23"],
    "P07-T01": ["P01-T13"],
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
    target = root / "state" / "task-graph.yaml"
    registry = regenerate(root / "docs" / "superpowers" / "plans", target)
    print("wrote " + str(target) + " with " + str(len(registry.tasks)) + " tasks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
