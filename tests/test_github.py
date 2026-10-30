from unittest.mock import MagicMock
import httpx
import pytest

from commitbot.exceptions import GitHubAPIError
from commitbot.sources.authentication import get_github_token
from commitbot.sources.github import (
    build_pull_request_diff,
    create_github_client,
    filter_pull_request_files,
    get_pull_request,
    get_pull_request_files,
    get_recent_repository_messages,
    parse_pull_request_url,
)


# --- 1. URL PARSER TESTS ---
def test_parse_pull_request_url_valid():
    owner, repo, pr_num = parse_pull_request_url(
        "https://github.com/torvalds/linux/pull/123"
    )
    assert owner == "torvalds"
    assert repo == "linux"
    assert pr_num == 123


def test_parse_pull_request_url_trailing_slash():
    owner, repo, pr_num = parse_pull_request_url(
        "https://github.com/fastapi/fastapi/pull/42/"
    )
    assert owner == "fastapi"
    assert repo == "fastapi"
    assert pr_num == 42


@pytest.mark.parametrize(
    "invalid_url",
    [
        "http://github.com/owner/repo/pull/1",  # HTTP not HTTPS
        "https://gitlab.com/owner/repo/pull/1",  # Not github.com
        "https://github.com/owner/repo/issues/1",  # Issues, not pull
        "https://github.com/owner/repo/pull/0",  # PR <= 0
        "https://github.com/owner/repo/pull/abc",  # Non-digit
        "https://user:pass@github.com/owner/repo/pull/1",  # Credentials
    ],
)
def test_parse_pull_request_url_invalid(invalid_url):
    with pytest.raises(ValueError):
        parse_pull_request_url(invalid_url)


# --- 2. CLIENT & AUTHENTICATION TESTS ---
def test_create_github_client_without_token():
    with create_github_client() as client:
        assert "Authorization" not in client.headers
        assert client.headers["Accept"] == "application/vnd.github+json"
        assert client.headers["User-Agent"] == "commitbot"


def test_create_github_client_with_token():
    with create_github_client("test_token_123") as client:
        assert client.headers["Authorization"] == "Bearer test_token_123"


def test_get_github_token(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_mocktoken123")
    assert get_github_token() == "ghp_mocktoken123"

    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    assert get_github_token() is None


# --- 3. FILE FILTERING TESTS ---
def test_filter_pull_request_files():
    sample_files = [
        {"filename": "src/main.py", "status": "modified"},
        {"filename": "backend/.env", "status": "added"},
        {"filename": "secrets.key", "status": "added"},
        {
            "filename": "clean.txt",
            "previous_filename": "secret.key",
            "status": "renamed",
        },
    ]
    patterns = [".env", "*.key"]
    filtered = filter_pull_request_files(sample_files, patterns)

    assert len(filtered) == 1
    assert filtered[0]["filename"] == "src/main.py"


# --- 4. DIFF RECONSTRUCTION TESTS ---
def test_build_pull_request_diff():
    assert build_pull_request_diff([]) == ""

    sample_files = [
        {
            "filename": "calculator.py",
            "status": "modified",
            "patch": "@@ -1 +1 @@\n-a\n+b",
        },
        {
            "filename": "new_name.py",
            "previous_filename": "old_name.py",
            "status": "renamed",
            "patch": "",
        },
    ]
    diff = build_pull_request_diff(sample_files)

    assert 'diff --git "a/calculator.py" "b/calculator.py"' in diff
    assert "GitHub change status: modified" in diff
    assert "@@ -1 +1 @@" in diff
    assert 'Previous filename: "old_name.py"' in diff
    assert "Patch unavailable; only file metadata is known." in diff


# --- 5. MOCKED GITHUB API CALLS ---
def test_get_pull_request_success():
    mock_client = MagicMock(spec=httpx.Client)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.json.return_value = {
        "number": 12,
        "title": "Add feature",
        "base": {"sha": "abc123sha"},
    }
    mock_response.raise_for_status.return_value = None
    mock_client.get.return_value = mock_response

    result = get_pull_request(mock_client, repo="repo", pr_num=12, owner="owner")
    assert result["number"] == 12
    assert result["base"]["sha"] == "abc123sha"


def test_get_recent_repository_messages_success():
    mock_client = MagicMock(spec=httpx.Client)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.json.return_value = [
        {"commit": {"message": "feat: first line\n\nbody details"}},
        {"commit": {"message": "fix: bugfix"}},
    ]
    mock_response.raise_for_status.return_value = None
    mock_client.get.return_value = mock_response

    titles = get_recent_repository_messages(
        mock_client, owner="owner", repo="repo", ref="sha", limit=2
    )
    assert titles == ["feat: first line", "fix: bugfix"]