import subprocess
from dotenv import load_dotenv
load_dotenv()
import os
from pathlib import Path
from typing import List

from commitbot.exceptions import GitCommandError
from commitbot.sources.local_git import find_repo_root
def get_recent_commit_messages(repo:str|Path|None=None,limit:int=10)->List[str]:
    if limit < 1:
        raise ValueError("limit must be at least 1")
    repository = find_repo_root(repo)
    check_head = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", "HEAD"],
        cwd=repository,
        capture_output=True,
        check=False,
        text=True,
    )

    if check_head.returncode == 1:
        return []
    elif check_head.returncode != 0:
        raise GitCommandError(
            f"Failed to verify HEAD in repository: {check_head.stderr.strip()}"
        )
    try:


        command_result = subprocess.run(
            ["git" ,"log" ,"-n" ,str(limit) ,"--format=%s"],
            cwd=repository,
            capture_output = True,
            check = True,
            text = True
        )
        commit_list = list()

        for line in command_result.stdout.splitlines():
            commit_list.append(line.strip())
        return commit_list
    except subprocess.CalledProcessError as e:
        # Git ran but failed (e.g. not a repo)

        raise GitCommandError("Failed to read recent commit messages.") from e

if __name__ == "__main__":
    path = os.getenv("PATHNEW")
    print(get_recent_commit_messages(path,limit=2))

