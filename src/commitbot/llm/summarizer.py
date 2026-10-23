import os
from dotenv import load_dotenv

from commitbot.processing.chunking import chunk_diff
from commitbot.sources.local_git import get_staged_diff

load_dotenv()
import importlib.resources
from ollama import ResponseError
from commitbot.config import Settings
import httpx
from commitbot.llm.ollama_client import create_chat_model
from langchain_core.messages import SystemMessage,HumanMessage
from langchain_core.output_parsers import StrOutputParser
from commitbot.exceptions import ModelTimeoutError, ModelConnectionError, ModelResponseError
def load_summary_prompt()->str:
    prompt_path=importlib.resources.files('commitbot.prompts') / 'summarize_diff.txt'
    with prompt_path.open("r",encoding="utf-8") as f:
        prompt=f.read()
    if prompt.strip()=="":
        raise ValueError("No prompt provided for summarizing diff")
    return prompt

def summarize_diff_chunk(chunk:str,settings:Settings)->str:
    if(chunk.strip()==""):
        raise ValueError("No chunk provided for summarizing diff")
    try :
        prompt = load_summary_prompt()

        llm = create_chat_model(settings)
        chain = llm | StrOutputParser()
        output = chain.invoke([SystemMessage(prompt),HumanMessage(chunk)])
        output=output.strip()
        if output=="":
            raise ModelResponseError("Empty summary output")
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

    return output


def summarize_large_diff(diff_str:str,settings:Settings)->str:
    if diff_str.strip()=="":
        raise ValueError("No diff provided for summarizing.")
    list_diff=chunk_diff(diff_str,settings.max_diff_chars)
    summarized_diff_list=[]
    i=1
    for chunk in list_diff:
        summarized_diff=f"Fragment {i} summary\n{summarize_diff_chunk(chunk,settings)}"
        summarized_diff_list.append(summarized_diff)
        i=i+1
    summary_str = "\n\n".join(summarized_diff_list)
    if(len(summary_str)>settings.max_diff_chars):
        raise ValueError("The summary of diff exceeds the maximum character limit.")
    return summary_str



if __name__ == "__main__":

    path = os.getenv("PATHCALCULATOR")
    if not path:
        raise ValueError("Set PATHCALCULATOR in .env")

    diff = get_staged_diff(path)
    print(summarize_diff_chunk(diff, Settings()))
    print(summarize_large_diff(diff, Settings()))