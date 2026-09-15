"""Environment probes are unit tested against injected command output."""

from amanda_agent.bootstrap.environment import (
    CommandResult,
    parse_dotnet_sdks,
    probe_tools,
)


SAMPLE_DOTNET = """8.0.422 [C:\\Program Files\\dotnet\\sdk]
8.0.100-preview.7.23376.3 [C:\\Program Files\\dotnet\\sdk]

"""


def test_dotnet_sdk_parser_reads_version_and_location():
    sdks = parse_dotnet_sdks(SAMPLE_DOTNET)

    assert [sdk.version for sdk in sdks] == [
        "8.0.422",
        "8.0.100-preview.7.23376.3",
    ]
    assert sdks[0].base_path.endswith("sdk")


def test_dotnet_sdk_parser_tolerates_garbage_lines():
    sdks = parse_dotnet_sdks("no dotnet sdks were found\n\n")

    assert sdks == []


def test_missing_codex_is_a_critical_failure():
    def runner(argv):
        if argv[:2] == ["git", "--version"]:
            return CommandResult(0, "git version 2.51.0.windows.1", "")
        return CommandResult(1, "", "not found")

    probes = probe_tools(runner=runner, which=lambda name: None)

    by_name = {probe.name: probe for probe in probes}
    assert by_name["git"].status == "AVAILABLE"
    assert by_name["codex"].status == "MISSING"
    assert by_name["codex"].critical is True
    assert by_name["dotnet"].critical is False


def test_python_probe_only_accepts_the_312_series():
    def runner(argv):
        if argv[:1] == ["py"] and "-3.12" in argv:
            return CommandResult(1, "", "Requested Python version (3.12) not installed")
        if argv[:1] == ["py"]:
            return CommandResult(0, "Python 3.14.4", "")
        return CommandResult(1, "", "nope")

    probes = probe_tools(runner=runner, which=lambda name: None)

    python = {probe.name: probe for probe in probes}["python312"]
    assert python.status == "MISSING"
    assert "3.14" not in (python.version or "")


def test_dotnet_probe_reports_inventory_without_installing():
    issued = []

    def runner(argv):
        issued.append(list(argv))
        if argv[:3] == ["dotnet", "--list-sdks"]:
            return CommandResult(0, SAMPLE_DOTNET, "")
        return CommandResult(1, "", "nope")

    probes = probe_tools(runner=runner, which=lambda name: None)

    dotnet = {probe.name: probe for probe in probes}["dotnet"]
    assert dotnet.status == "AVAILABLE"
    assert dotnet.sdks[0].version == "8.0.422"
    mutating = {"install", "add", "update", "upgrade", "remove"}
    assert not any(mutating & set(argv) for argv in issued), issued
