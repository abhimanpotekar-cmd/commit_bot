from typing import List

def build_commit_context(staged_diff: str, recent_message: List[str]) -> str:
    if staged_diff.strip() == "":
        raise ValueError("No staged changes to describe.")

    if not recent_message:
        joined_messages = "No commit history available"
    else:
        joined_messages = "\n".join(recent_message)

    return (
        f"Recent commit titles -- style examples only : {joined_messages}\n\n"
        f"Staged diff -- changes to describe : {staged_diff}"
    )
