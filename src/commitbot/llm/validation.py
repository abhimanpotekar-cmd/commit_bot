from commitbot.schemas import CommitSuggestions

def validate_suggestions(suggestions: CommitSuggestions) -> CommitSuggestions:
    """
    Validate commit suggestions:
    - Reject duplicate titles (case-insensitive, trimmed).
    - Reject titles containing newline characters.
    """
    seen_titles = set()

    for suggestion in suggestions.suggestions:
        normalized = suggestion.title.strip().casefold()

        # Reject newline or carriage return in titles
        if "\n" in suggestion.title or "\r" in suggestion.title:
            raise ValueError("Commit titles must not contain newline characters")


        if normalized in seen_titles:
            raise ValueError("Model returned duplicate commit titles")

        seen_titles.add(normalized)

    return suggestions
