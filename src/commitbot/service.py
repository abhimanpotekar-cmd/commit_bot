from pathlib import Path

from commitbot.config import Settings
from commitbot.llm.generator import generate_commit_suggestions
from commitbot.processing.filters import should_exclude_file
from commitbot.schemas import CommitSuggestions
from commitbot.sources.history import get_recent_commit_messages
from commitbot.sources.local_git import get_staged_diff, get_staged_files


def suggest_local_commits(
    settings: Settings,
    repo: str | Path | None = None,
) -> CommitSuggestions:

    staged_files = get_staged_files(repo)
    if not staged_files:
        raise ValueError("No staged changes to describe.")

    # 2. Filter out excluded files based on configuration
    allowed_files = [
        path
        for path in staged_files
        if not should_exclude_file(path, settings.exclude_patterns)
    ]
    if not allowed_files:
        raise ValueError("All staged files are excluded by configuration.")

    staged_diff = get_staged_diff(repo,files=allowed_files)
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