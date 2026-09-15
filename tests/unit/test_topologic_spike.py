from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SPIKE_SCRIPT = PROJECT_ROOT / "tool-lab" / "topologic" / "spike.py"
ISOLATED_PYTHON = PROJECT_ROOT / ".venv-topologic" / "Scripts" / "python.exe"
RESULT_PATH = PROJECT_ROOT / "tool-lab" / "topologic" / "results" / "topologic-spike.json"


def test_topologic_spike_measures_space_and_persists_json_report() -> None:
    """The isolated TopologicPy executable must produce real geometry evidence."""

    assert ISOLATED_PYTHON.is_file(), "the TopologicPy environment is not provisioned"
    assert SPIKE_SCRIPT.is_file(), "the TopologicPy spike script is missing"

    environment = os.environ.copy()
    environment["PYTHONIOENCODING"] = "utf-8"
    completed = subprocess.run(
        [str(ISOLATED_PYTHON), str(SPIKE_SCRIPT)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        check=False,
        encoding="utf-8",
        env=environment,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    report = json.loads(completed.stdout)
    persisted = json.loads(RESULT_PATH.read_text(encoding="utf-8"))

    assert report == persisted
    assert report["status"] == "PASS"
    assert report["measurements"]["area_m2"] == pytest.approx(24.0)
    assert report["measurements"]["volume_m3"] == pytest.approx(72.0)
    assert report["topologicpy"]["imported"] is True
    assert report["exports"]["obj"]["status"] == "PASS"
    assert report["exports"]["obj"]["material_library"]["status"] == "PARTIAL"
    assert report["exports"]["obj"]["material_library"]["reference_exists"] is False
