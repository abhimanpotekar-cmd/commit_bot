import pytest

from commitbot.processing.chunking import chunk_diff
from commitbot.processing.context import (
    build_commit_context,
    build_pull_request_context,
)
from commitbot.processing.diff_parser import split_diff_by_file
from commitbot.processing.filters import should_exclude_file


# --- 1. FILTERS TESTS ---
def test_should_exclude_file():
    patterns = [".env", ".env.*", "*.key", "uv.lock", "certs/*.pem"]

    assert should_exclude_file("backend/.env", patterns) is True
    assert should_exclude_file(r"backend\.env", patterns) is True
    assert should_exclude_file(".env.production", patterns) is True
    assert should_exclude_file("certs/server.pem", patterns) is True
    assert should_exclude_file("secrets/private.key", patterns) is True
    assert should_exclude_file("uv.lock", patterns) is True

    # Allowed files
    assert should_exclude_file("src/main.py", patterns) is False
    assert should_exclude_file("README.md", patterns) is False
    assert should_exclude_file("calculator.py", []) is False


# --- 2. DIFF PARSER TESTS ---
def test_split_diff_by_file():
    assert split_diff_by_file("") == []

    single_file = (
        "diff --git a/app.py b/app.py\n"
        "--- a/app.py\n"
        "+++ b/app.py\n"
        "@@ -1 +1 @@\n"
        "+print('hello')\n"
    )
    assert len(split_diff_by_file(single_file)) == 1

    two_files = (
        "diff --git a/a.py b/a.py\n"
        "--- a/a.py\n"
        "+++ b/a.py\n"
        "@@ -1 +1 @@\n"
        "+# a\n"
        "diff --git a/b.py b/b.py\n"
        "--- a/b.py\n"
        "+++ b/b.py\n"
        "@@ -1 +1 @@\n"
        "+# b\n"
    )
    sections = split_diff_by_file(two_files)
    assert len(sections) == 2
    assert "".join(sections) == two_files


# --- 3. CHUNKING TESTS ---
def test_chunk_diff():
    assert chunk_diff("", 1000) == []

    diff_content = (
        "diff --git a/math.py b/math.py\n"
        "--- a/math.py\n"
        "+++ b/math.py\n"
        "@@ -1,2 +1,2 @@\n"
        "-def add(a, b): return a\n"
        "+def add(a, b): return a + b\n"
    )
    # Small diff fits in one chunk
    chunks = chunk_diff(diff_content, 2000)
    assert len(chunks) == 1
    assert chunks[0] == diff_content

    with pytest.raises(ValueError, match="max_chars must be at least 1"):
        chunk_diff(diff_content, 0)


# --- 4. CONTEXT TESTS ---
def test_build_commit_context_local():
    diff = "diff --git a/app.py b/app.py\n+print('hello')"
    history = ["feat: initial commit", "fix: resolve bug"]

    context = build_commit_context(diff, history)
    assert "Recent commit titles -- style examples only :" in context
    assert "feat: initial commit" in context
    assert "Staged diff -- changes to describe :" in context
    assert diff in context


def test_build_commit_context_summary():
    summary_text = "Fragment 1 summary: updated print statement."
    history = ["feat: initial commit"]

    context = build_commit_context(summary_text, history, is_summary=True)
    assert "Summaries of staged changes -- derived from diff fragments;" in context


def test_build_pull_request_context():
    pr_diff = "diff --git a/app.py b/app.py\nGitHub change status: modified\n"
    history = ["feat: add user login"]

    context = build_pull_request_context(pr_diff, history)
    assert "Pull request diff -- changes to describe :" in context
    assert pr_diff in context


def test_build_context_empty_diff_raises():
    with pytest.raises(ValueError, match="No staged changes to describe."):
        build_commit_context("   ", ["feat: test"], source="staged")

    with pytest.raises(ValueError, match="No pull request changes to describe."):
        build_pull_request_context("   ", ["feat: test"])


def test_build_context_no_history():
    diff = "diff --git a/app.py b/app.py\n+x = 1"
    context = build_commit_context(diff, [])
    assert "No commit history available" in context