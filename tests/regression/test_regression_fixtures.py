"""P04-T19 core regression fixtures.

The fixtures are executed against the real design engine; each expectation is
loaded from the fixture data rather than hard-coded here, so the recorded
invariants stay the single source of truth.
"""

from __future__ import annotations

import json
from typing import Any

import pytest
import regression_support as support


def _compare(expected: Any, actual: Any, path: str) -> None:
    if isinstance(expected, dict):
        assert isinstance(actual, dict), f"{path}: expected an object"
        missing = sorted(set(expected) - set(actual))
        assert not missing, f"{path}: missing keys {missing}"
        for key, value in expected.items():
            _compare(value, actual[key], f"{path}.{key}")
        return
    if isinstance(expected, list):
        assert isinstance(actual, list), f"{path}: expected a list"
        assert len(expected) == len(actual), (
            f"{path}: expected {len(expected)} items, got {len(actual)}"
        )
        for index, value in enumerate(expected):
            _compare(value, actual[index], f"{path}[{index}]")
        return
    if isinstance(expected, bool) or isinstance(actual, bool):
        assert expected is actual, f"{path}: expected {expected!r}, got {actual!r}"
        return
    if isinstance(expected, float) or isinstance(actual, float):
        assert actual == pytest.approx(expected, rel=1e-9, abs=1e-9), (
            f"{path}: expected {expected!r}, got {actual!r}"
        )
        return
    assert expected == actual, f"{path}: expected {expected!r}, got {actual!r}"


@pytest.mark.parametrize("name", support.FIXTURE_NAMES)
def test_fixture_directory_declares_every_required_artifact(name: str) -> None:
    directory = support.fixture_dir(name)
    assert directory.is_dir(), f"missing fixture directory {name}"
    for filename in support.FIXTURE_FILES:
        path = directory / filename
        assert path.is_file(), f"{name}/{filename} is missing"
        assert json.loads(path.read_text(encoding="utf-8")) not in (None, {}, []), (
            f"{name}/{filename} must not be empty"
        )
    seed = support.load_seed(name)
    assert set(seed) & {"seeds", "archetype_seed"}, (
        f"{name}/seed.json must declare seeds or archetype_seed"
    )
    assert support.load_invariants(name), f"{name} declares no invariants"


@pytest.mark.parametrize("name", support.FIXTURE_NAMES)
def test_fixture_matches_its_expected_invariants(name: str) -> None:
    result = support.evaluate_fixture(name)
    invariants = support.load_invariants(name)
    for key, expected in invariants.items():
        assert key in result["observed"], f"{name}: observed values lack {key}"
        _compare(expected, result["observed"][key], f"{name}.{key}")


@pytest.mark.parametrize("name", support.FIXTURE_NAMES)
def test_fixture_is_deterministic_for_the_same_seed(name: str) -> None:
    first = support.evaluate_fixture(name)
    second = support.evaluate_fixture(name)
    assert first["canonical_hash"] == second["canonical_hash"], (
        f"{name}: canonical hash changed between identical runs"
    )
    assert first["observed"] == second["observed"], (
        f"{name}: observed values changed between identical runs"
    )


@pytest.mark.parametrize("name", support.FIXTURE_NAMES)
def test_canonical_hash_is_reproducible_or_documented(name: str) -> None:
    expected = support.load_expected_hash(name)
    assert expected.get("algorithm") == "sha256", f"{name}: hash algorithm is not pinned"
    status = expected.get("status")
    assert status in {"STABLE", "UNSTABLE"}, f"{name}: unknown hash status {status!r}"
    if status != "STABLE":
        assert expected.get("reason"), (
            f"{name}: a non-stable canonical hash must document the reason"
        )
        pytest.skip(f"{name}: canonical hash is recorded as {status}")
    recorded = expected["canonical_hash"]
    assert isinstance(recorded, str) and len(recorded) == 64, (
        f"{name}: recorded hash is not a sha256 digest"
    )
    result = support.evaluate_fixture(name)
    assert result["canonical_hash"] == recorded, (
        f"{name}: canonical hash drifted from the recorded fixture hash"
    )


def test_regression_set_exercises_the_whole_core_engine() -> None:
    declared: set[str] = set()
    for name in support.FIXTURE_NAMES:
        declared.update(str(item) for item in support.load_input(name)["exercises"])

    missing = sorted(support.REQUIRED_ENGINE_AREAS - declared)
    assert not missing, f"no fixture declares these engine areas: {missing}"


@pytest.mark.parametrize("name", support.FIXTURE_NAMES)
def test_each_fixture_records_runtime_evidence_for_declared_areas(name: str) -> None:
    result = support.evaluate_fixture(name)
    evidence = result["observed"]["engine_evidence"]
    assert result["exercises"], f"{name}: no engine areas declared"
    for area in result["exercises"]:
        entry = evidence.get(area)
        assert isinstance(entry, dict) and entry, (
            f"{name}: declared {area} without recording runtime evidence"
        )


def _recorded_expectations(value: Any) -> int:
    if isinstance(value, dict):
        return sum(_recorded_expectations(item) for item in value.values())
    if isinstance(value, list):
        return sum(_recorded_expectations(item) for item in value)
    return 1


@pytest.mark.parametrize("name", support.FIXTURE_NAMES)
def test_fixture_invariants_are_substantive(name: str) -> None:
    invariants = support.load_invariants(name)
    recorded = _recorded_expectations(invariants)
    assert recorded >= 20, (
        f"{name}: only {recorded} recorded expectations; too thin to protect the engine"
    )
    assert any(
        isinstance(value, (list, dict)) and value for value in invariants.values()
    ), f"{name}: invariants contain no structured expectations"
