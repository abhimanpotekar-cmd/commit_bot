from typing import List

def build_commit_context(staged_diff: str, recent_message: List[str],is_summary:bool=False) -> str:

    if staged_diff.strip() == "":
        raise ValueError("No staged changes to describe.")

    if not recent_message:
        joined_messages = "No commit history available"
    else:
        joined_messages = "\n".join(recent_message)
    diff_label = (
        "Summaries of staged changes -- derived from diff fragments; may omit details."
        if is_summary
        else "Staged diff -- changes to describe"
    )
    return (
        f"Recent commit titles -- style examples only : {joined_messages}\n\n"
        f"{diff_label} : {staged_diff}"
    )
