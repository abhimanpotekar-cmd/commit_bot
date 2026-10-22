from pathlib import Path
import typer
from rich.console import Console

from commitbot.config import load_settings
from commitbot.exceptions import CommitBotError
from commitbot.ui.display import display_suggestions
from commitbot.ui.review import select_suggestion,edit_suggestion
from commitbot.service import suggest_local_commits
from rich.prompt import Confirm

app = typer.Typer()

@app.callback()

def app_callback():
    """Generate commit using local AI model."""
    pass

@app.command()
def suggest(  repo: Path|None = typer.Option(
        None,
        "--repo",
        help="Path to the repository"
    ),
    config: Path|None = typer.Option(
        None,
        "--config",
        help="Path to the configuration file"
    ),
) -> None:

    """Suggest commit messages for staged changes."""
    try:
        settings=load_settings(config)
        suggested_commits = suggest_local_commits(settings=settings, repo=repo)
        while True:
            display_suggestions(suggested_commits)
            if Confirm.ask("Generate new suggestions?", default=False):
                suggested_commits = suggest_local_commits(settings=settings, repo=repo)
            else:
                break

    except (CommitBotError,ValueError,OSError) as e:
        Console(stderr=True).print(str(e),markup=False)
        raise typer.Exit(code=1) from e




    selected_commit=select_suggestion(suggested_commits)
    if Confirm.ask("Edit this message.",default=False):
        selected_commit=edit_suggestion(selected_commit)

    if selected_commit.body:
        print(f"{selected_commit.title}\n\n{selected_commit.body}")
    else:
        print(selected_commit.title)


