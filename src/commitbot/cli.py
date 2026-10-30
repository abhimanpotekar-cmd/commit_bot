from pathlib import Path
import typer
from rich.console import Console

from commitbot.config import load_settings
from commitbot.exceptions import CommitBotError
from commitbot.ui.display import display_suggestions
from commitbot.ui.review import select_suggestion, edit_suggestion
from commitbot.service import suggest_local_commits, suggest_pr_commits
from rich.prompt import Confirm
import subprocess
import sys


app = typer.Typer()


@app.callback()
def app_callback():
    """Generate commit using local AI model."""
    pass


def copy_to_clipboard(text: str) -> bool:
    """Copies text to system clipboard across Windows, macOS, and Linux without extra dependencies."""
    try:
        if sys.platform == "win32":
            subprocess.run(["clip.exe"], input=text.encode("utf-16le"), check=True)
            return True
        elif sys.platform == "darwin":
            subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=True)
            return True
        else:
            try:
                subprocess.run(["wl-copy"], input=text.encode("utf-8"), check=True)
                return True
            except FileNotFoundError:
                subprocess.run(
                    ["xclip", "-selection", "clipboard"],
                    input=text.encode("utf-8"),
                    check=True,
                )
                return True
    except Exception:
        return False


@app.command(name="bot")
@app.command(name="suggest")
def bot(
    repo: Path | None = typer.Option(
        None,
        "--repo",
        help="Path to the repository",
    ),
    config: Path | None = typer.Option(
        None,
        "--config",
        help="Path to the configuration file",
    ),
) -> None:
    """Suggest commit messages for staged changes."""
    try:
        settings = load_settings(config)
        suggested_commits = suggest_local_commits(settings=settings, repo=repo)
        while True:
            display_suggestions(suggested_commits)
            if Confirm.ask("Generate new suggestions?", default=False):
                suggested_commits = suggest_local_commits(settings=settings, repo=repo)
            else:
                break

    except (CommitBotError, ValueError, OSError) as e:
        Console(stderr=True).print(str(e), markup=False)
        raise typer.Exit(code=1) from e

    selected_commit = select_suggestion(suggested_commits)
    if Confirm.ask("Edit this message.", default=False):
        selected_commit = edit_suggestion(selected_commit)

    if selected_commit.body:
        final_message = f"{selected_commit.title}\n\n{selected_commit.body}"
    else:
        final_message = selected_commit.title

    print(final_message)

    if copy_to_clipboard(final_message):
        Console().print("\n[dim green]✔ Copied to clipboard! Paste it directly into git commit.[/dim green]")


@app.command(name="pr")
def pr(
    url: str = typer.Argument(
        ...,
        help="GitHub pull request URL (e.g. https://github.com/owner/repo/pull/12)",
    ),
    config: Path | None = typer.Option(
        None,
        "--config",
        help="Path to the configuration file",
    ),
) -> None:
    """Suggest commit messages for a GitHub pull request."""
    try:
        settings = load_settings(config)
        suggested_commits = suggest_pr_commits(pr_url=url, settings=settings)
        while True:
            display_suggestions(suggested_commits)
            if Confirm.ask("Generate new suggestions?", default=False):
                suggested_commits = suggest_pr_commits(pr_url=url, settings=settings)
            else:
                break

    except (CommitBotError, ValueError, OSError) as e:
        Console(stderr=True).print(str(e), markup=False)
        raise typer.Exit(code=1) from e

    selected_commit = select_suggestion(suggested_commits)
    if Confirm.ask("Edit this message.", default=False):
        selected_commit = edit_suggestion(selected_commit)

    if selected_commit.body:
        final_message = f"{selected_commit.title}\n\n{selected_commit.body}"
    else:
        final_message = selected_commit.title

    print(final_message)

    if copy_to_clipboard(final_message):
        Console().print("\n[dim green]✔ Copied to clipboard! Paste it directly into git commit.[/dim green]")


if __name__ == "__main__":
    app()