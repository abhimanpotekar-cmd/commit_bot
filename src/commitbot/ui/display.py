from commitbot.config import load_settings
from commitbot.llm.generator import generate_commit_suggestions
from commitbot.schemas import CommitSuggestions
from rich.console import Console
from rich.table import Table
from dotenv import load_dotenv
from rich.text import Text
from commitbot.sources.history import get_recent_commit_messages
from commitbot.sources.local_git import get_staged_diff
from commitbot.ui.review import select_suggestion

load_dotenv()
import os

def display_suggestions(suggestions:CommitSuggestions)->None:
    console = Console()
    table =Table(title="Commit Suggestions")
    table.add_column("ID", justify="right", style="cyan", no_wrap=False)
    table.add_column("Title",style="magenta")
    table.add_column("Body",style="green")

    for i,suggestion in enumerate(suggestions.suggestions,start=1):
        table.add_row(str(i),
                      Text(suggestion.title),
                      Text(suggestion.body or ""))
    #                 used Text to wrap title and body so it stops it from interpreting them as markup


    console.print(table)

if __name__ == "__main__":
    path = os.getenv("PATHCALCULATOR")
    commit_suggestions= generate_commit_suggestions(get_staged_diff(path),get_recent_commit_messages(path),load_settings())
    display_suggestions(commit_suggestions)
    chosen_commit = select_suggestion(commit_suggestions)
    print(chosen_commit)