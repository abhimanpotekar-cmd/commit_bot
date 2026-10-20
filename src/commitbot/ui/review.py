
from commitbot.schemas import CommitSuggestions,CommitSuggestion
from rich.prompt import Prompt

def select_suggestion(suggestions:CommitSuggestions)->CommitSuggestion:
    choice:str=Prompt.ask(
        "Select the commit message.",
        choices=[str(i) for i in range(1,len(suggestions.suggestions)+1)],
        default="1"
    )
    return suggestions.suggestions[int(choice)-1]

