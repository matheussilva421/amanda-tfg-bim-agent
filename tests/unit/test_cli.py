from typer.testing import CliRunner

from amanda_agent.cli import app

runner = CliRunner()


def test_help_lists_core_commands():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for command in ("doctor", "status", "resume", "rollback"):
        assert command in result.stdout


def test_unimplemented_commands_never_report_success():
    for command in ("doctor", "status", "resume", "rollback"):
        result = runner.invoke(app, [command])
        assert result.exit_code == 2, command
        assert "not implemented" in result.output
