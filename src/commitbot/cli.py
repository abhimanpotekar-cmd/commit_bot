from pathlib import Path
import typer

from commitbot.config import load_settings
from commitbot.ui.display import display_suggestions
from commitbot.ui.review import select_suggestion
from commitbot.service import suggest_local_commits
app = typer.Typer()

@app.callback()

def app_callback():
    """Empty application callback."""
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
    settings=load_settings(config)
    suggested_commits=suggest_local_commits(settings=settings,repo=repo)
    display_suggestions(suggested_commits)
    selected_commit=select_suggestion(suggested_commits)
    if selected_commit.body:
        print(selected_commit.title,"\n",selected_commit.body)
    else:
        print( selected_commit.title)

