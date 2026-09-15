"""TDD contract for the ordered cold-persistence gate."""

from __future__ import annotations

import importlib

import pytest


def _persistence():
    try:
        return importlib.import_module("amanda_agent.qa.persistence")
    except ModuleNotFoundError as exc:
        pytest.fail(f"persistence coordinator is not implemented yet: {exc}")


def _complete_record():
    module = _persistence()
    record = module.PersistenceRecord(release_id="RC01")
    for step in module.PersistenceStep:
        record.record_step(
            step,
            status=module.PersistenceStatus.PASS,
            evidence={"observed": step.value},
        )
    return module, record


def test_promotion_refuses_an_incomplete_persistence_sequence():
    module = _persistence()
    record = module.PersistenceRecord(release_id="RC01")
    record.record_step(
        module.PersistenceStep.SAVE_RC,
        status=module.PersistenceStatus.PASS,
        evidence={"path": "RC01.rvt"},
    )

    assert record.is_complete is False
    with pytest.raises(module.PersistenceIncompleteError):
        record.require_complete()


def test_complete_typed_sequence_is_accepted_for_promotion():
    module, record = _complete_record()

    assert record.is_complete is True
    assert record.promotion_ready is True
    assert [step.step for step in record.steps] == list(module.PersistenceStep)


def test_save_without_wait_for_completion_is_rejected():
    module = _persistence()
    record = module.PersistenceRecord(release_id="RC01")
    record.record_step(
        module.PersistenceStep.SAVE_RC,
        status=module.PersistenceStatus.PASS,
        evidence={"path": "RC01.rvt"},
    )
    record.record_step(
        module.PersistenceStep.CLOSE_AND_HASH,
        status=module.PersistenceStatus.PASS,
        evidence={"sha256": "a" * 64},
    )

    assert record.is_complete is False
    assert any(
        "wait" in reason.lower() or "completion" in reason.lower()
        for reason in record.incomplete_reasons
    )


def test_cold_reopen_steps_are_mandatory_even_when_save_passed():
    module = _persistence()
    record = module.PersistenceRecord(release_id="RC01")
    for step in (
        module.PersistenceStep.SAVE_RC,
        module.PersistenceStep.WAIT_SAVE_COMPLETION,
        module.PersistenceStep.CLOSE_AND_HASH,
        module.PersistenceStep.PROCESS_EXIT,
    ):
        record.record_step(
            step,
            status=module.PersistenceStatus.PASS,
            evidence={"observed": step.value},
        )

    assert record.is_complete is False
    missing = set(record.missing_steps)
    assert {
        module.PersistenceStep.START_REVIT_2027,
        module.PersistenceStep.OPEN_RC,
        module.PersistenceStep.RECONNECT_PROVIDER,
        module.PersistenceStep.PROVIDER_HEALTH,
        module.PersistenceStep.CRITICAL_QA,
        module.PersistenceStep.SEMANTIC_STATE,
    } <= missing
