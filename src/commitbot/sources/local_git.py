from dotenv import load_dotenv
load_dotenv()
import os
import subprocess
from pathlib import Path
from commitbot.exceptions import NotGitRepositoryError, GitNotInstalledError ,GitCommandError

def find_repo_root(repo: str | Path | None = None) -> Path:
    if repo is None:
        repo = Path.cwd()
    else:
        repo = Path(repo)
    if not repo.exists():
        raise FileNotFoundError(f"Path {repo} does not exist")
    if not repo.is_dir():
        raise NotADirectoryError(f"Path {repo} is not a directory")

    try:
        #subprocess used to run git commands
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=repo,#current working directory
            capture_output=True,
            check=True,
            text=True #if text = true stdout gives a string
        )
        return Path(result.stdout.strip()) #.stdout contains the captured output; text=True handles decoding. .strip() removes surrounding whitespace.
    except FileNotFoundError as e:
        raise GitNotInstalledError("Git executable not found. Install Git.") from e
    except subprocess.CalledProcessError as e:
        raise NotGitRepositoryError("Not a valid Git repository or Git command failed.") from e

def get_staged_diff(repo: str | Path | None = None) -> str:

    repository = find_repo_root(repo)
    try:
        result = subprocess.run(
            ["git","diff","--cached","--no-ext-diff","--no-textconv"],
            cwd = repository,
            capture_output=True,
            check=True,
            text=True
        )

    except subprocess.CalledProcessError as e:
        raise GitCommandError("Failed to read staged changes.") from e

    return result.stdout

if __name__ == "__main__":
    path = os.getenv("PATHCALCULATOR")
    res_find_repo_root = find_repo_root(path)
    res_staged=get_staged_diff(path)
    print(res_find_repo_root)
    print(res_staged)
