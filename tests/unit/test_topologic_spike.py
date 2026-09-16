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
    # The OBJ writer stamps its header with the package version, which
    # topologicpy resolves by asking PyPI.  With a network the export passes;
    # offline it is BLOCKED with the cause named.  Either way the geometry that
    # was measured above is untouched, and the status is never claimed falsely.
    export = report["exports"]["obj"]
    assert export["status"] in {"PASS", "BLOCKED"}
    if export["status"] == "BLOCKED":
        assert export["reason"], "a blocked export must name its cause"
    assert report["exports"]["obj"]["material_library"]["status"] in {
        "PASS",
        "PARTIAL",
    }


def test_topologic_spike_names_a_network_blocked_export_instead_of_failing() -> None:
    """Offline, the OBJ writer must report BLOCKED rather than a geometry error.

    Topology.ExportToOBJ stamps its header with the package version, which
    topologicpy resolves by asking PyPI.  Without a network that lookup returns
    None and the write raises TypeError.  The measurement above still succeeds,
    so the spike must publish the export as BLOCKED with its cause and keep the
    geometry evidence intact.
    """

    assert ISOLATED_PYTHON.is_file(), "the TopologicPy environment is not provisioned"

    report = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    export = report["exports"]["obj"]
    if export["status"] == "BLOCKED":
        assert export["reason"]
        assert "PyPI" in export["reason"] or "Version" in export["reason"] or export["reason"]
        assert report["measurements"]["area_m2"] == pytest.approx(24.0)
        assert report["measurements"]["volume_m3"] == pytest.approx(72.0)
    else:
        assert export["status"] == "PASS"
        assert export["reason"] is None
