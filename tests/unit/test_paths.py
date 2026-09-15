from pathlib import Path

from amanda_agent.paths import ProjectPaths


def test_project_paths_derive_from_root(tmp_path: Path):
    root = tmp_path / "project amanda"
    root.mkdir()

    paths = ProjectPaths.from_root(root)

    assert paths.root == root.resolve()
    assert paths.state == root.resolve() / "state"
    assert paths.logs == root.resolve() / "logs"
    assert paths.bim == root.resolve() / "bim"
    assert paths.project_state == root.resolve() / "PROJECT_STATE.yaml"
    assert paths.snapshots == root.resolve() / "state" / "snapshots"


def test_project_state_never_escapes_root(tmp_path: Path):
    paths = ProjectPaths.from_root(tmp_path)
    for candidate in (paths.state, paths.logs, paths.bim, paths.project_state, paths.snapshots):
        assert paths.root in candidate.parents or candidate.parent == paths.root
