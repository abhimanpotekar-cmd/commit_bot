from unittest.mock import MagicMock, patch
import pytest

from commitbot.config import Settings
from commitbot.llm.generator import generate_commit_suggestions, load_commit_prompt
from commitbot.llm.summarizer import load_summary_prompt
from commitbot.llm.validation import validate_suggestions
from commitbot.schemas import CommitSuggestion, CommitSuggestions


# --- 1. PROMPT LOADING TESTS ---
def test_load_commit_prompt():
    prompt = load_commit_prompt()
    assert isinstance(prompt, str)
    assert len(prompt.strip()) > 50
    assert "Git commit message generator" in prompt


def test_load_summary_prompt():
    prompt = load_summary_prompt()
    assert isinstance(prompt, str)
    assert len(prompt.strip()) > 50


# --- 2. VALIDATION TESTS ---
def test_validate_suggestions_valid():
    valid = CommitSuggestions(
        suggestions=[
            CommitSuggestion(title="feat: add user login", body="details"),
            CommitSuggestion(title="fix: resolve login bug", body=None),
            CommitSuggestion(title="docs: update auth guide", body=None),
        ]
    )
    result = validate_suggestions(valid)
    assert len(result.suggestions) == 3


def test_validate_suggestions_duplicate_rejected():
    duplicates = CommitSuggestions(
        suggestions=[
            CommitSuggestion(title="feat: add user login", body="details"),
            CommitSuggestion(title="FEAT: ADD USER LOGIN", body=None),  # Duplicate
            CommitSuggestion(title="docs: update auth guide", body=None),
        ]
    )
    with pytest.raises(ValueError, match="Model returned duplicate commit titles"):
        validate_suggestions(duplicates)


def test_validate_suggestions_newline_in_title_rejected():
    newline_title = CommitSuggestions(
        suggestions=[
            CommitSuggestion(title="feat: first line\nsecond line", body=None),
            CommitSuggestion(title="fix: something else", body=None),
            CommitSuggestion(title="docs: update readme", body=None),
        ]
    )
    with pytest.raises(ValueError, match="must not contain newline characters"):
        validate_suggestions(newline_title)


# --- 3. MOCKED GENERATION TESTS ---
@patch("commitbot.llm.generator.create_chat_model")
def test_generate_commit_suggestions_mocked(mock_create_model):
    expected = CommitSuggestions(
        suggestions=[
            CommitSuggestion(title="feat: add addition function", body="New math helper."),
            CommitSuggestion(title="refactor: improve calculator math", body=None),
            CommitSuggestion(title="math: support adding numbers", body=None),
        ]
    )

    mock_llm = MagicMock()
    mock_structured = MagicMock()
    mock_structured.invoke.return_value = expected
    mock_llm.with_structured_output.return_value = mock_structured
    mock_create_model.return_value = mock_llm

    settings = Settings()
    diff = "diff --git a/calc.py b/calc.py\n+def add(a, b): return a + b"
    history = ["feat: init calculator"]

    result = generate_commit_suggestions(diff, history, settings)

    assert len(result.suggestions) == 3
    assert result.suggestions[0].title == "feat: add addition function"
    mock_structured.invoke.assert_called_once()