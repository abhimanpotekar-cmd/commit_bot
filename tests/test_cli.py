from unittest.mock import patch
from pathlib import Path
from typer.testing import CliRunner

from commitbot.cli import app
from commitbot.schemas import CommitSuggestion, CommitSuggestions

runner = CliRunner()



def test_cli_main_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "bot" in result.stdout
    assert "suggest" in result.stdout
    assert "pr" in result.stdout


def test_cli_bot_help():
    result = runner.invoke(app, ["bot", "--help"])
    assert result.exit_code == 0
    assert "--repo" in result.stdout
    assert "--config" in result.stdout


def test_cli_pr_help():
    result = runner.invoke(app, ["pr", "--help"])
    assert result.exit_code == 0
    assert "URL" in result.stdout



def test_cli_bot_not_git_repo(tmp_path: Path):
    non_repo = tmp_path / "empty_dir"
    non_repo.mkdir()
    result = runner.invoke(app, ["bot", "--repo", str(non_repo)])
    assert result.exit_code == 1


def test_cli_pr_invalid_url():
    result = runner.invoke(app, ["pr", "https://gitlab.com/wrong/repo/pull/1"])
    assert result.exit_code == 1



@patch("commitbot.cli.suggest_local_commits")
def test_cli_bot_flow_success(mock_suggest):
    mock_suggest.return_value = CommitSuggestions(
        suggestions=[
            CommitSuggestion(title="feat: add CLI runner tests", body="Covers Typer workflows."),
            CommitSuggestion(title="test: add CLI tests", body=None),
            CommitSuggestion(title="cli: support bot command", body=None),
        ]
    )

    # Simulated user inputs:
    # 1. "Generate new suggestions?" -> "n"
    # 2. "Select the commit message." -> "1"
    # 3. "Edit this message." -> "n"
    user_inputs = "n\n1\nn\n"
    result = runner.invoke(app, ["bot"], input=user_inputs)

    assert result.exit_code == 0
    assert "feat: add CLI runner tests" in result.stdout


@patch("commitbot.cli.suggest_pr_commits")
def test_cli_pr_flow_success(mock_suggest_pr):
    mock_suggest_pr.return_value = CommitSuggestions(
        suggestions=[
            CommitSuggestion(title="feat: add pull request support", body="Adds GitHub integration."),
            CommitSuggestion(title="pr: support remote diffs", body=None),
            CommitSuggestion(title="github: parse PR commits", body=None),
        ]
    )


    user_inputs = "n\n1\nn\n"
    result = runner.invoke(app, ["pr", "https://github.com/owner/repo/pull/42"], input=user_inputs)

    assert result.exit_code == 0
    assert "feat: add pull request support" in result.stdout