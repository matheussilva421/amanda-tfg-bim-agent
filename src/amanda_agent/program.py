"""The reviewed phase graph, encoded once.

The graph mirrors the canonical COMBINED plan: 01 -> 07A -> 02, 01 -> 03 -> 04,
and (02 + 04) -> 05 -> 06 -> 07B -> 08, with 09 optional. Encoding it in code
lets resume reason about what a blocker actually stops instead of guessing from
prose.
"""

from __future__ import annotations

from .models.tasks import TaskGraph, TaskNode

PHASE_SEQUENCE = [
    ("PHASE_01", "foundation-environment-state", []),
    ("PHASE_07A", "autonomy-recovery-security", ["PHASE_01"]),
    ("PHASE_02", "revit-tool-lab-providers", ["PHASE_01", "PHASE_07A"]),
    ("PHASE_03", "project-intelligence", ["PHASE_01"]),
    ("PHASE_04", "design-engine", ["PHASE_03"]),
    ("PHASE_05", "bim-compiler", ["PHASE_02", "PHASE_04"]),
    ("PHASE_06", "qa-release-exports", ["PHASE_05"]),
    ("PHASE_07B", "production-hardening", ["PHASE_06"]),
    ("PHASE_08", "amanda-production-run", ["PHASE_07B"]),
    ("PHASE_09", "optional-render-cloud", ["PHASE_08"]),
]

PHASE_02_TASK = "P02-T01"


def phase_graph() -> TaskGraph:
    """Phase-level graph plus the Revit entry task used by BIM blockers."""
    graph = TaskGraph()
    for phase_id, name, depends_on in PHASE_SEQUENCE:
        graph.add(
            TaskNode(id=phase_id, name=name, phase_id=phase_id, depends_on=depends_on)
        )
    graph.add(
        TaskNode(
            id=PHASE_02_TASK,
            name="Prove the Revit provider in the Tool Lab",
            phase_id="PHASE_02",
            depends_on=["PHASE_02"],
        )
    )
    graph.validate_graph()
    return graph


def blocking_phases_for(blocker) -> set:
    """Which phases an open blocker stops, including downstream phases."""
    graph = phase_graph()
    blocked = graph.blocked_tasks([blocker])
    return blocked
