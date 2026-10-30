import subprocess
from pathlib import Path
import pytest

from commitbot.exceptions import NotGitRepositoryError
from commitbot.sources.local_git import (
    find_repo_root,
    get_staged_diff,
    get_staged_files,
)


def test_find_repo_root_success(temp_git_repo: Path):
    assert find_repo_root(temp_git_repo).resolve() == temp_git_repo.resolve()


def test_find_repo_root_not_a_repo(tmp_path: Path):
    non_repo = tmp_path / "not_a_repo"
    non_repo.mkdir()
    with pytest.raises(NotGitRepositoryError):
        find_repo_root(non_repo)


def test_find_repo_root_nonexistent(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        find_repo_root(tmp_path / "does_not_exist")


def test_get_staged_files_and_diff(temp_git_repo: Path):

    assert get_staged_files(temp_git_repo) == []
    assert get_staged_diff(temp_git_repo) == ""


    test_file = temp_git_repo / "calculator.py"
    test_file.write_text("def add(a, b): return a + b\n")
    subprocess.run(["git", "add", "calculator.py"], cwd=temp_git_repo, check=True)


    staged = get_staged_files(temp_git_repo)
    assert staged == ["calculator.py"]


    diff = get_staged_diff(temp_git_repo)
    assert "diff --git" in diff
    assert "+def add(a, b): return a + b" in diff


    assert get_staged_diff(temp_git_repo, files=[]) == ""