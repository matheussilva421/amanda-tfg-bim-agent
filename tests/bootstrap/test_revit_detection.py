"""Revit detection against a fake Autodesk root."""

from pathlib import Path

from amanda_agent.bootstrap.revit import RevitDetection, scan_roots


def make_install(root: Path, year: str, *, with_api: bool = True) -> Path:
    install = root / ("Revit " + year)
    install.mkdir(parents=True)
    (install / "Revit.exe").write_bytes(b"MZ")
    if with_api:
        (install / "RevitAPI.dll").write_bytes(b"MZ")
    return install


def test_missing_root_is_not_an_error(tmp_path: Path):
    detection = scan_roots([tmp_path / "absent"])

    assert detection.installations == []
    assert detection.selected is None
    assert detection.probe_status == "NOT_FOUND"


def test_installation_without_api_is_rejected(tmp_path: Path):
    make_install(tmp_path, "2027", with_api=False)

    detection = scan_roots([tmp_path])

    assert detection.installations == []
    assert any("incomplete installation" in note for note in detection.notes)


def test_selected_build_is_the_highest_year(tmp_path: Path):
    make_install(tmp_path, "2026")
    newest = make_install(tmp_path, "2027")

    detection = scan_roots([tmp_path])

    assert detection.is_ambiguous is True
    assert detection.selected is not None
    assert detection.selected.install_path == newest
    assert detection.selected.year == 2027
    assert detection.selected.api_path.name == "RevitAPI.dll"


def test_detection_serializes_to_json_ready_dict(tmp_path: Path):
    make_install(tmp_path, "2027")

    payload = scan_roots([tmp_path]).as_dict()

    assert payload["probe_status"] == "DETECTED"
    assert payload["installation_count"] == 1
    assert payload["selected"]["install_path"].endswith("Revit 2027")
    assert payload["ambiguous"] is False


def test_unrelated_directories_are_ignored(tmp_path: Path):
    (tmp_path / "AutoCAD 2027").mkdir()
    (tmp_path / "Revit 2027 Add-in Manager").mkdir()

    detection = scan_roots([tmp_path])

    assert detection.installations == []
