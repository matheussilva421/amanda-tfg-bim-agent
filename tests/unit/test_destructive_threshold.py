

def _destructive_operations(count: int):
    from amanda_agent.bim.diff import DiffAction, DiffOperation

    return [
        DiffOperation(logical_id=f"ROOM-{index:03d}", action=DiffAction.DELETE)
        for index in range(count)
    ]


def test_eleven_destructive_operations_per_one_hundred_managed_is_high_risk():
    from amanda_agent.bim.diff import assess_destructive_threshold

    assessment = assess_destructive_threshold(
        _destructive_operations(11), managed_count=100, pre_operation_checkpoint=True
    )

    assert assessment.status == "HIGH_RISK_PLAN"
    assert assessment.blocked is True
    assert assessment.destructive_count == 11


def test_five_destructive_operations_require_a_pre_operation_checkpoint():
    from amanda_agent.bim.diff import assess_destructive_threshold

    without_checkpoint = assess_destructive_threshold(
        _destructive_operations(5), managed_count=100
    )
    with_checkpoint = assess_destructive_threshold(
        _destructive_operations(5),
        managed_count=100,
        pre_operation_checkpoint=True,
    )

    assert without_checkpoint.status == "CHECKPOINT_REQUIRED"
    assert without_checkpoint.blocked is True
    assert with_checkpoint.allowed is True


def test_unknown_cascade_blocks_even_when_direct_diff_is_small():
    from amanda_agent.bim.diff import (
        DiffAction,
        DiffOperation,
        assess_destructive_threshold,
    )

    operation = DiffOperation(
        logical_id="WALL-001",
        action=DiffAction.REPLACE,
        cascade_unknown=True,
    )

    assessment = assess_destructive_threshold(
        [operation], managed_count=100, pre_operation_checkpoint=True
    )

    assert assessment.status == "UNKNOWN_CASCADE"
    assert assessment.blocked is True


def test_zero_managed_baseline_is_blocked_for_any_destructive_change():
    from amanda_agent.bim.diff import assess_destructive_threshold

    assessment = assess_destructive_threshold(
        _destructive_operations(1), managed_count=0, pre_operation_checkpoint=True
    )

    assert assessment.status == "NO_MANAGED_BASELINE"
    assert assessment.blocked is True


def test_high_risk_release_needs_checkpoint_and_reviewed_plan():
    from amanda_agent.bim.diff import assess_destructive_threshold

    assessment = assess_destructive_threshold(
        _destructive_operations(11),
        managed_count=100,
        pre_operation_checkpoint=True,
        reviewed_plan=True,
        release_high_risk=True,
    )

    assert assessment.status == "HIGH_RISK_PLAN"
    assert assessment.allowed is True


def test_threshold_config_loads_from_versioned_yaml(tmp_path):
    from amanda_agent.bim.diff import load_destructive_threshold

    config_path = tmp_path / "destructive-threshold.yaml"
    config_path.write_text(
        "schema_version: 2\nmanaged_ratio: 0.25\nabsolute_maximum: 50\n",
        encoding="utf-8",
    )

    config = load_destructive_threshold(config_path)

    assert config.schema_version == 2
    assert config.managed_ratio == 0.25
    assert config.absolute_maximum == 50


def test_default_threshold_config_is_versioned():
    from amanda_agent.bim.diff import load_destructive_threshold

    config = load_destructive_threshold()

    assert config.schema_version == 1
    assert config.managed_ratio == 0.10
