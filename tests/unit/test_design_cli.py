"""CLI contracts for canonical design runs and finalist comparison."""

import hashlib
import json
from pathlib import Path

import yaml
from typer.testing import CliRunner

from amanda_agent.cli import app

runner = CliRunner()


def write_canonical_state(root: Path) -> tuple[Path, Path]:
    source = root / "docs" / "source" / "brief.pdf"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"canonical source")
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()

    requirements = root / "project" / "requirements" / "program.json"
    requirements.parent.mkdir(parents=True)
    requirements.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "baseline": {
                    "source_id": "SRC-001",
                    "source_filename": "brief.pdf",
                    "source_sha256": source_hash,
                    "source_pages": [1],
                    "person_capacity": 20,
                    "adoption_status": "ACCEPTED",
                    "selection_authority": "AGENT_DELEGATED",
                    "selection_date": "2026-09-15",
                    "evidence": "test canonical source",
                },
                "totals": {
                    "internal_useful_m2": 20.0,
                    "external_programmed_m2": 0.0,
                },
                "reconciliation": {
                    "ok": True,
                    "mismatches": [],
                    "internal_useful_m2": 20.0,
                    "external_programmed_m2": 0.0,
                },
                "sectors": [
                    {
                        "logical_id": "SEC-01",
                        "name": "Acolhimento",
                        "area_kind": "INTERNAL",
                        "subtotal_m2": 20.0,
                        "spaces": [
                            {
                                "logical_id": "REQ-01-01",
                                "name": "Sala",
                                "quantity": 1,
                                "target_area_m2": 20.0,
                                "area_kind": "INTERNAL",
                                "source_page": 1,
                                "total_area_m2": 20.0,
                            }
                        ],
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    site = root / "project" / "site" / "site.json"
    site.parent.mkdir(parents=True)
    site.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "site_name": "Test site",
                "location": "Natal/RN",
                "site_version": 1,
                "boundary": {
                    "kind": "STUDY_PLACEHOLDER",
                    "coordinates": [[0, 0], [20, 0], [20, 20], [0, 20], [0, 0]],
                },
                "design_coordinate_origin": {
                    "x": 0,
                    "y": 0,
                    "z": 0,
                    "convention": "LOCAL_DESIGN_PLANE",
                },
                "topography": {
                    "source_state": "MISSING",
                    "representation": "PLANAR_PLACEHOLDER",
                    "elevation_points": [],
                },
                "provenance": [
                    {
                        "source_id": "SRC-001",
                        "locator": "page 1",
                        "sha256": source_hash,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = root / "project" / "provenance" / "source-manifest.yaml"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "documents": [
                    {
                        "source_id": "SRC-001",
                        "filename": "brief.pdf",
                        "sha256": source_hash,
                        "mime_type": "application/pdf",
                        "ingested_at": "2026-09-15T00:00:00Z",
                        "immutable_path": "docs/source/brief.pdf",
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return requirements, site


def test_design_creates_run_from_canonical_inputs_without_mutating_sources(
    tmp_path: Path, monkeypatch
):
    requirements, site = write_canonical_state(tmp_path)
    before = {
        requirements: hashlib.sha256(requirements.read_bytes()).hexdigest(),
        site: hashlib.sha256(site.read_bytes()).hexdigest(),
    }
    monkeypatch.setenv("AMANDA_PROJECT_ROOT", str(tmp_path))

    result = runner.invoke(app, ["design", "--run-id", "RUN-001"])

    assert result.exit_code == 0, result.output
    run_dir = tmp_path / "design-engine" / "runs" / "RUN-001"
    run = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    assert run["run_id"] == "RUN-001"
    assert run["requirements_path"] == "project/requirements/program.json"
    assert run["site_path"] == "project/site/site.json"
    assert run["finalists"] is not None
    assert all(
        hashlib.sha256(path.read_bytes()).hexdigest() == digest
        for path, digest in before.items()
    )


def test_design_rejects_mutable_source_state_without_creating_a_run(
    tmp_path: Path, monkeypatch
):
    requirements, _ = write_canonical_state(tmp_path)
    source = tmp_path / "docs" / "source" / "brief.pdf"
    source.write_bytes(b"changed source")
    monkeypatch.setenv("AMANDA_PROJECT_ROOT", str(tmp_path))

    result = runner.invoke(app, ["design", "--run-id", "RUN-INVALID"])

    assert result.exit_code != 0
    assert "source state" in result.output.lower()
    assert not (tmp_path / "design-engine" / "runs" / "RUN-INVALID").exists()
    assert requirements.is_file()


def test_compare_prints_and_saves_the_finalist_matrix(
    tmp_path: Path, monkeypatch
):
    write_canonical_state(tmp_path)
    run_dir = tmp_path / "design-engine" / "runs" / "RUN-001"
    run_dir.mkdir(parents=True)
    (run_dir / "run.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "run_id": "RUN-001",
                "finalists": [
                    {
                        "finalist_id": "RUN-001-F01",
                        "seed": 7,
                        "status": "FEASIBLE",
                        "geometry_hash": "abc123",
                        "metrics": {"program_compliance": 1.0},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("AMANDA_PROJECT_ROOT", str(tmp_path))

    result = runner.invoke(app, ["compare", "RUN-001"])

    assert result.exit_code == 0, result.output
    assert "finalist matrix" in result.stdout.lower()
    matrix = json.loads(
        (run_dir / "finalist-matrix.json").read_text(encoding="utf-8")
    )
    assert matrix["run_id"] == "RUN-001"
    assert matrix["finalists"][0]["finalist_id"] == "RUN-001-F01"
    assert matrix["finalists"][0]["metrics"]["program_compliance"] == 1.0
