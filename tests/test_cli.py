from typer.testing import CliRunner

from mic.cli import app

runner = CliRunner()


def test_hello() -> None:
    result = runner.invoke(app, ["hello", "World"])
    assert result.exit_code == 0
    assert "Hello, World!" in result.output
