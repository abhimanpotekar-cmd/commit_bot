import subprocess
from pathlib import Path
from commitbot.exceptions import NotGitRepositoryError, GitNotInstalledError

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
        return Path(result.stdout.strip()) #.stout turns raw bytes to a string
    except FileNotFoundError as e:
        raise GitNotInstalledError("Git executable not found. Install Git.") from e
    except subprocess.CalledProcessError as e:
        raise NotGitRepositoryError("Not a valid Git repository or Git command failed.") from e
