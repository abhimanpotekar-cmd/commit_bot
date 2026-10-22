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

def get_staged_diff(repo: str | Path | None = None,files:list[str]|None=None) -> str:

    repository = find_repo_root(repo)
    if(files == []):
        return ""
    commands=["git","--literal-pathspecs","diff","--cached","--no-ext-diff","--no-textconv","--no-renames"]
    if files is not None:
        commands.append("--")
        commands.extend(files)
    try:
        result = subprocess.run(
            commands,
            cwd = repository,
            capture_output=True,
            check=True,
            text=True
        )

    except subprocess.CalledProcessError as e:
        raise GitCommandError("Failed to read staged changes.") from e

    return result.stdout

def get_staged_files(repo: str | Path | None = None) -> list[str]:
    repository=find_repo_root(repo)
    try:
        cached_diff = subprocess.run(
            ["git","diff","--cached","--name-only","--no-renames","-z"],
            # -z preserves filenames containing spaces or newlines. --no-renames exposes both paths of a rename so we can filter them separately later.
            cwd=repository,
            capture_output=True,
            check=True,
            text=True
        )


    except subprocess.CalledProcessError as e:
        raise GitCommandError("Failed to read staged files.") from e

    return [f for f in cached_diff.stdout.split("\0") if f]


if __name__ == "__main__":
    path = os.getenv("PATHCALCULATOR")
    # res_find_repo_root = find_repo_root(path)
    repo_root = find_repo_root(path)

    # 1. All staged files
    diff_all = get_staged_diff(repo_root)
    print("=== All staged files ===")
    print(repr(diff_all) if diff_all == "" else diff_all)

    # 2. Empty selection (files=[])
    diff_empty = get_staged_diff(repo_root, files=[])
    print("=== Empty selection ===")
    print(repr(diff_empty))

    # 3. Selected file (files=["calculator.py"])
    diff_selected = get_staged_diff(repo_root, files=["calculator.py"])
    print("=== Selected file (calculator.py) ===")
    print(repr(diff_selected) if diff_selected == "" else diff_selected)

    # 4. Unmatched file (files=["nonexistent-test-file.py"])
    diff_unmatched = get_staged_diff(
        repo_root, files=["nonexistent-test-file.py"]
    )
    print("=== Unmatched file (nonexistent-test-file.py) ===")
    print(repr(diff_unmatched))
    # res_staged=get_staged_diff(path)
    # print(res_find_repo_root)
    # print(res_staged)
    # print(get_staged_files(res_find_repo_root))
