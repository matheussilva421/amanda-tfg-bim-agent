from pathlib import Path


SOURCE = Path(__file__).with_name("CreateLabWall.cs")
HOST_SOURCE = SOURCE.parent / "host" / "LabHostApp.cs"
RUNNER_SOURCE = SOURCE.parents[2] / ".tmp-t16-run.ps1"


def test_create_lab_wall_contains_the_fail_closed_revit_wall_contract() -> None:
    assert SOURCE.is_file(), "CreateLabWall.cs must be delivered before the command can be built"

    source = SOURCE.read_text(encoding="utf-8")

    required_fragments = (
        "IExternalCommand",
        '"Level 1"',
        "UnitUtils.ConvertToInternalUnits",
        "UnitTypeId.Meters",
        "Wall.Create",
        "new Transaction",
        "5.0",
        "3.0",
        "ElementId.Value",
        "get_BoundingBox(null)",
        "throw new InvalidOperationException",
    )

    for fragment in required_fragments:
        assert fragment in source, f"missing required Revit API contract: {fragment}"


def test_host_uses_per_launch_job_and_fail_closed_ownership_gates() -> None:
    assert HOST_SOURCE.is_file(), "LabHostApp.cs must be delivered with the host"

    host = HOST_SOURCE.read_text(encoding="utf-8")

    required_fragments = (
        'Environment.GetEnvironmentVariable("AMANDA_LAB_HOST_JOB")',
        'Path.Combine(BaseDirectory, "host-job.json")',
        'GetString("env_token", string.Empty)',
        'Environment.GetEnvironmentVariable("AMANDA_LAB_HOST_TOKEN")',
        'string.IsNullOrWhiteSpace(activePath)',
        'StandbyRvt',
        'OpenAndActivateDocument(job.StandbyRvt)',
        'var closedDocumentTitle = document.Title',
        'document.Close(false)',
        'ExitRevit',
    )

    for fragment in required_fragments:
        assert fragment in host, f"missing host safety contract: {fragment}"


def test_runner_exports_job_path_and_launch_token_before_start() -> None:
    assert RUNNER_SOURCE.is_file(), ".tmp-t16-run.ps1 must be available for the runtime gate"

    runner = RUNNER_SOURCE.read_text(encoding="utf-8")

    required_fragments = (
        "$env:AMANDA_LAB_HOST_TOKEN = $token",
        "$env:AMANDA_LAB_HOST_JOB = $HostJobPath",
        "Save-LaunchJob $started.Id",
        "expected_pid = $expectedPid",
        "env_token = $token",
        "$owned.StartTime -eq $startedStartTime",
    )

    for fragment in required_fragments:
        assert fragment in runner, f"missing runner safety contract: {fragment}"
