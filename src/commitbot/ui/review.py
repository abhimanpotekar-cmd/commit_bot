from rich.console import Console

from commitbot.schemas import CommitSuggestions,CommitSuggestion
from rich.prompt import Prompt

def select_suggestion(suggestions:CommitSuggestions)->CommitSuggestion:
    choice:str=Prompt.ask(
        "Select the commit message.",
        choices=[str(i) for i in range(1,len(suggestions.suggestions)+1)],
        default="1"
    )
    return suggestions.suggestions[int(choice)-1]



def edit_suggestion(suggestion: CommitSuggestion) -> CommitSuggestion:
    console = Console(stderr=True)

    while True:
        title = Prompt.ask(
            "Suggest a new title",
            default=suggestion.title,
        )
        raw_body = Prompt.ask(
            "Suggest a new Body or enter `-` to remove the body.",
            default=suggestion.body or "",
        )

        stripped_body = raw_body.strip()
        body = None if stripped_body in ("", "-") else raw_body

        try:
            if "\n" in title or "\r" in title:
                raise ValueError("Title must not contain newline characters.")

            return CommitSuggestion(
                title=title,
                body=body,
            )
        except ValueError as e:
            console.print(str(e), markup=False)

