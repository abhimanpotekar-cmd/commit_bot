from typing import List


def build_commit_context(staged_diff: str,recent_message: List[str],is_summary: bool = False,source: str = "staged") -> str:
    if staged_diff.strip() == "":
        if source in ("pr", "pull_request"):
            raise ValueError("No pull request changes to describe.")
        raise ValueError("No staged changes to describe.")

    if not recent_message:
        joined_messages = "No commit history available"
    else:
        joined_messages = "\n".join(recent_message)

    if source in ("pr", "pull_request"):
        diff_label = (
            "Summaries of pull request changes -- derived from diff fragments; may omit details."
            if is_summary
            else "Pull request diff -- changes to describe"
        )
    else:
        diff_label = (
            "Summaries of staged changes -- derived from diff fragments; may omit details."
            if is_summary
            else "Staged diff -- changes to describe"
        )

    return (
        f"Recent commit titles -- style examples only : {joined_messages}\n\n"
        f"{diff_label} : {staged_diff}"
    )


def build_pull_request_context(pr_diff: str,recent_messages: List[str],is_summary: bool = False,) -> str:
    return build_commit_context(
        staged_diff=pr_diff,
        recent_message=recent_messages,
        is_summary=is_summary,
        source="pull_request",
    )


if __name__ == "__main__":
    diff_example = "diff --git a/app.py b/app.py\n+print('hello')"
    history_example = ["feat: add greeting"]
    print("=== Local Staged Context ===")
    print(build_commit_context(diff_example, history_example))
    print("\n=== PR Context ===")
    print(build_pull_request_context(diff_example, history_example))