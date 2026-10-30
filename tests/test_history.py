import subprocess
from pathlib import Path
import pytest

from commitbot.sources.history import get_recent_commit_messages


def test_recent_commit_messages_empty_repo(temp_git_repo: Path):
    # A fresh repo with 0 commits returns empty list instead of crashing
    assert get_recent_commit_messages(temp_git_repo) == []


def test_recent_commit_messages_with_commits(temp_git_repo: Path):
    # Create 3 commits
    for i in range(1, 4):
        file = temp_git_repo / f"file_{i}.txt"
        file.write_text(f"content {i}")
        subprocess.run(["git", "add", "."], cwd=temp_git_repo, check=True)
        subprocess.run(
            ["git", "commit", "-m", f"feat: commit number {i}"],
            cwd=temp_git_repo,
            check=True,)


    messages = get_recent_commit_messages(temp_git_repo, limit=2)
    assert len(messages) == 2
    assert messages[0] == "feat: commit number 3"
    assert messages[1] == "feat: commit number 2"


def test_recent_commit_messages_invalid_limit(temp_git_repo: Path):
    with pytest.raises(ValueError, match="limit must be at least 1"):
        get_recent_commit_messages(temp_git_repo, limit=0)