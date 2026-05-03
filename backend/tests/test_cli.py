"""CLI tests."""

from __future__ import annotations

from typer.testing import CliRunner

from rss_news_reader.cli import app


def test_cli_init_command(configured_env) -> None:
    """Init command should succeed."""

    runner = CliRunner()
    result = runner.invoke(app, ["init"])

    assert result.exit_code == 0
    assert "Initialized" in result.stdout


def test_cli_test_source_command(configured_env) -> None:
    """test-source should return diagnostics for sample-local."""

    runner = CliRunner()
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["test-source", "sample-local"])

    assert result.exit_code == 0
    assert "sample-local" in result.stdout
