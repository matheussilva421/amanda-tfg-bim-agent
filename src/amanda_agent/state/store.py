"""Atomic, revision-checked YAML persistence for project state.

Design rules encoded here:

* a failed save never destroys the previous valid state;
* an invalid file is preserved for inspection instead of being replaced by defaults;
* concurrent writers are detected through a compare-and-swap on state_revision.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import yaml

from ..models.state import ProjectState


class StateStoreError(Exception):
    """Base class for state persistence failures."""


class StateRevisionConflict(StateStoreError):
    """Another writer advanced the state revision first."""


class StateStore:
    def __init__(self, path: Path):
        self.path = Path(path)

    # -- reading ---------------------------------------------------------
    def load(self) -> ProjectState:
        if not self.path.exists():
            return ProjectState()
        raw = yaml.safe_load(self.path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise StateStoreError("state file is not a mapping: " + str(self.path))
        return ProjectState(**raw)

    def current_revision(self) -> int:
        return self.load().state_revision

    # -- writing ---------------------------------------------------------
    def save(
        self,
        state: ProjectState,
        *,
        expected_revision: int | None = None,
    ) -> ProjectState:
        """Persist state atomically, bumping state_revision.

        When expected_revision is provided the current on-disk revision must
        match it, otherwise a concurrent writer already changed the state.
        """
        on_disk_exists = self.path.exists()
        current = self.load()

        if on_disk_exists and current.schema_version != state.schema_version:
            raise StateStoreError(
                "schema version mismatch: on-disk "
                + str(current.schema_version)
                + " vs incoming "
                + str(state.schema_version)
            )

        if expected_revision is not None and current.state_revision != expected_revision:
            raise StateRevisionConflict(
                "expected revision "
                + str(expected_revision)
                + ", found "
                + str(current.state_revision)
            )

        next_state = state.model_copy(
            update={"state_revision": current.state_revision + 1}
        )
        payload = yaml.safe_dump(
            next_state.model_dump(mode="json"), sort_keys=True, allow_unicode=True
        )

        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle, tmp_name = tempfile.mkstemp(
            prefix="." + self.path.name + ".", suffix=".tmp", dir=str(self.path.parent)
        )
        tmp_path = Path(tmp_name)
        try:
            with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(tmp_path, self.path)
        except BaseException:
            tmp_path.unlink(missing_ok=True)
            raise
        return next_state
