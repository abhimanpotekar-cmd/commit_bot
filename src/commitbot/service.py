from pathlib import Path

from commitbot.config import Settings
from commitbot.llm.generator import generate_commit_suggestions
from commitbot.processing.filters import should_exclude_file
from commitbot.schemas import CommitSuggestions
from commitbot.sources.history import get_recent_commit_messages
from commitbot.sources.local_git import get_staged_diff, get_staged_files

from commitbot.sources.authentication import get_github_token
from commitbot.sources.github import parse_pull_request_url,create_github_client,get_pull_request,get_pull_request_files,filter_pull_request_files,build_pull_request_diff,get_recent_repository_messages

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

def suggest_pr_commits(
    pr_url: str,
    settings: Settings,
    token: str | None = None,
) -> CommitSuggestions:
    owner, repo, pr_num = parse_pull_request_url(pr_url)
    auth_token = token or get_github_token()

    with create_github_client(token=auth_token) as client:
        pull_request = get_pull_request(
            client=client, repo=repo, pr_num=pr_num, owner=owner
        )
        files = get_pull_request_files(
            client=client, owner=owner, repo=repo, pr_num=pr_num
        )
        if not files:
            raise ValueError("No files found in pull request.")

        allowed_files = filter_pull_request_files(files, settings.exclude_patterns)
        if not allowed_files:
            raise ValueError("All pull request files are excluded by configuration.")

        pr_diff = build_pull_request_diff(allowed_files)
        if not pr_diff.strip():
            raise ValueError("No pull request changes to describe.")

        base_ref = pull_request.get("base", {}).get("sha")
        recent_messages = []
        if base_ref:
            recent_messages = get_recent_repository_messages(
                client=client,
                owner=owner,
                repo=repo,
                ref=base_ref,
                limit=settings.history_limit,
            )

    return generate_commit_suggestions(
        staged_diff=pr_diff,
        recent_messages=recent_messages,
        settings=settings,
        source="pull_request",
    )


if __name__ == "__main__":
    from commitbot.config import load_settings
    settings = load_settings()
    print("Testing service module...")
    # 1. Local staged test
    try:
        local_sugg = suggest_local_commits(settings)
        print("Local suggestions generated:", len(local_sugg.suggestions))
    except Exception as e:
        print("Local check:", e)

