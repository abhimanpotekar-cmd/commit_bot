from pathlib import Path

from commitbot.config import Settings
from commitbot.llm.generator import generate_commit_suggestions
from commitbot.schemas import CommitSuggestions
from commitbot.sources.history import get_recent_commit_messages
from commitbot.sources.local_git import get_staged_diff


def suggest_local_commits(
    settings: Settings,
    repo: str | Path | None = None,
) -> CommitSuggestions:
    staged_diff = get_staged_diff(repo)

    if not staged_diff.strip():
        raise ValueError("No staged changes to describe.")

    recent_messages = get_recent_commit_messages(
        repo,
        limit=settings.history_limit,
    )

    return generate_commit_suggestions(
        staged_diff,
        recent_messages,
        settings,
    )