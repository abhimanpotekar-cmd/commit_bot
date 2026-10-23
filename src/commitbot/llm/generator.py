import importlib.resources
from typing import List
import os
from dotenv import load_dotenv
from ollama import ResponseError
import httpx
from commitbot.llm.summarizer import summarize_large_diff
from commitbot.exceptions import ModelTimeoutError, ModelConnectionError, ModelResponseError
from commitbot.llm.validation import validate_suggestions

load_dotenv()
from langchain_core.messages import  HumanMessage ,SystemMessage
from commitbot.config import Settings, load_settings
from commitbot.llm.ollama_client import create_chat_model
from commitbot.processing.context import build_commit_context
from commitbot.schemas import CommitSuggestions
from commitbot.sources.history import get_recent_commit_messages
from commitbot.sources.local_git import get_staged_diff


def load_commit_prompt() -> str:
    """
    Load the commit message prompt from commitbot.prompts/commit_message.txt.
    Rejects empty or whitespace-only content.
    """
    # Locate the file inside the commitbot.prompts package
    prompt_path = importlib.resources.files("commitbot.prompts") / "commit_message.txt"


    with prompt_path.open("r", encoding="utf-8") as f:
        prompt_text = f.read()


    if not prompt_text.strip():
        raise ValueError("Commit prompt file is empty or whitespace-only.")

    return prompt_text

def generate_commit_suggestions(staged_diff:str,recent_messages:List[str],settings:Settings)->CommitSuggestions:



    if settings.max_diff_chars<len(staged_diff):

        summarized = summarize_large_diff(staged_diff,settings)
        context = build_commit_context(summarized,recent_messages,is_summary=True)
    else:
        context = build_commit_context(staged_diff, recent_messages)
    prompt=load_commit_prompt()
    try:
        llm = create_chat_model(settings)
        structured_suggesstions = llm.with_structured_output(CommitSuggestions,method="json_schema")
        output = structured_suggesstions.invoke([SystemMessage(prompt),HumanMessage(context)])

        try:
            finall_commits_suggestions = validate_suggestions(
                output,
            )
        except ValueError as e:
            retry_messages = [
                SystemMessage(content=prompt),
                HumanMessage(content=context),
                HumanMessage(content=f"Validation error: {e}. Please correct and return valid commit suggestions."),
            ]
            retry_output = structured_suggesstions.invoke(retry_messages)
            retry_commit=validate_suggestions(
                retry_output, )
            return retry_commit
    except httpx.TimeoutException as e:
        raise ModelTimeoutError(
            f"Model request timed out after {settings.request_timeout} seconds. "
            "Try increasing request_timeout in settings."
        ) from e
    except (ConnectionError, httpx.ConnectError) as e:
        raise ModelConnectionError(
            f"Failed to conect to Ollama at {settings.base_url}. Verify the service is running."
        ) from e
    except ResponseError as e:
        raise ModelResponseError(
            f"Ollama API error for model '{settings.model}': {e.error}"
        ) from e
    return finall_commits_suggestions

if __name__ == "__main__":
    path = os.getenv("PATHCALCULATOR")
    print(generate_commit_suggestions(get_staged_diff(path),get_recent_commit_messages(path),load_settings()))