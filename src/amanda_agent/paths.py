"""Canonical filesystem layout for the project."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectPaths:
    root: Path
    state: Path
    logs: Path
    bim: Path
    project_state: Path
    snapshots: Path

    @classmethod
    def from_root(cls, root: Path) -> "ProjectPaths":
        root = Path(root).resolve()
        return cls(
            root=root,
            state=root / "state",
            logs=root / "logs",
            bim=root / "bim",
            project_state=root / "PROJECT_STATE.yaml",
            snapshots=root / "state" / "snapshots",
        )

    def ensure_directories(self) -> None:
        """Create the durable directories this layout owns."""
        for directory in (self.state, self.logs, self.bim, self.snapshots):
            directory.mkdir(parents=True, exist_ok=True)
