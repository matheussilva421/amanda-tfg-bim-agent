"""The JSONL log is append-only and redacts before persisting."""

import json
from pathlib import Path

from amanda_agent.logging import EventLog, read_events

SECRET = "sk-logsecretvalue1234567890"


def test_record_carries_timestamp_task_operation_provider_status(
    tmp_path: Path,
):
    log = EventLog(tmp_path / "events.jsonl", task="P01-T09")

    log.record(
        operation="probe",
        provider="revit",
        status="PASS",
        detail="inventory complete",
    )

    events = read_events(tmp_path / "events.jsonl")
    assert len(events) == 1
    event = events[0]
    assert event["task"] == "P01-T09"
    assert event["operation"] == "probe"
    assert event["provider"] == "revit"
    assert event["status"] == "PASS"
    assert event["timestamp_utc"].endswith("Z")


def test_log_is_append_only_and_survives_multiple_writers(tmp_path: Path):
    path = tmp_path / "events.jsonl"
    first = EventLog(path, task="P01-T09")
    second = EventLog(path, task="P01-T10")

    first.record(operation="a", provider="x", status="PASS")
    second.record(operation="b", provider="y", status="PASS")
    first.record(operation="c", provider="x", status="FAIL")

    events = read_events(path)
    assert [event["operation"] for event in events] == ["a", "b", "c"]


def test_secrets_are_redacted_before_persisting(tmp_path: Path):
    path = tmp_path / "events.jsonl"
    log = EventLog(path, task="P01-T09")

    log.record(
        operation="auth",
        provider="codex",
        status="FAIL",
        detail="Authorization: Bearer " + SECRET,
        data={"OPENAI_API_KEY": SECRET, "nested": {"api_key": SECRET}},
    )

    raw = path.read_text(encoding="utf-8")
    assert SECRET not in raw
    event = read_events(path)[0]
    assert event["data"]["OPENAI_API_KEY"] == "[REDACTED]"
    assert event["data"]["nested"]["api_key"] == "[REDACTED]"


def test_exception_payloads_are_redacted_too(tmp_path: Path):
    path = tmp_path / "events.jsonl"
    log = EventLog(path, task="P01-T09")

    try:
        raise RuntimeError("token=" + SECRET)
    except RuntimeError as error:
        log.record_exception(
            operation="connect", provider="revit", error=error
        )

    raw = path.read_text(encoding="utf-8")
    assert SECRET not in raw
    event = read_events(path)[0]
    assert event["status"] == "FAIL"
    assert event["error_type"] == "RuntimeError"


def test_malformed_lines_do_not_break_reading(tmp_path: Path):
    path = tmp_path / "events.jsonl"
    log = EventLog(path, task="P01-T09")
    log.record(operation="a", provider="x", status="PASS")
    with path.open("a", encoding="utf-8") as stream:
        stream.write("{not json}\n")
    log.record(operation="b", provider="x", status="PASS")

    events = read_events(path)

    assert [event["operation"] for event in events] == ["a", "b"]
    assert any(
        "unparsable" in note for note in read_events(path, include_problems=True).problems
    )


def test_event_order_is_monotonic(tmp_path: Path):
    path = tmp_path / "events.jsonl"
    log = EventLog(path, task="P01-T09")
    for index in range(3):
        log.record(operation="step" + str(index), provider="x", status="PASS")

    sequences = [event["sequence"] for event in read_events(path)]

    assert sequences == sorted(sequences)
    assert len(set(sequences)) == 3
