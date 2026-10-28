from typing import Any
import json
import requests
import httpx
import urllib.parse
from commitbot.processing.filters import should_exclude_file
from commitbot.exceptions import GitHubAPIError


def parse_pull_request_url(url_str: str) -> tuple[str, str, int]:
    parsed = urllib.parse.urlparse(url_str)

    if parsed.scheme.lower() != "https" or parsed.hostname != "github.com":
        raise ValueError("Expected an HTTPS GitHub URL.")

    if (parsed.username is not None or parsed.password is not None or parsed.port is not None):
        raise ValueError("URL must not contain credentials or a port.")

    parts = parsed.path.removesuffix("/").split("/")

    if len(parts) != 5 or parts[0] != "" or parts[3] != "pull":
        raise ValueError("Expected /owner/repo/pull/number.")

    if not parts[1] or not parts[2]:
        raise ValueError("Owner and repository must not be empty.")

    for part in parts:
        if "%" in part:
            raise ValueError("Path must not contain percent encoding.")

        for char in part:
            if char.isspace():
                raise ValueError("Path must not contain whitespace.")

    if not parts[4].isascii() or not parts[4].isdigit():
        raise ValueError("Pull-request number must contain ASCII digits only.")

    pr_number = int(parts[4])
    if pr_number < 1:
        raise ValueError("Pull-request number must be greater than zero.")

    return parts[1], parts[2], pr_number

def create_github_client(token:str|None=None) -> httpx.Client:
    base_url= "https://api.github.com"
    if token is not None and token.strip()!="":
        return httpx.Client(base_url=base_url, timeout=30,
                                headers={"Accept": "application/vnd.github+json", "User-Agent": "commitbot","Authorization": f"Bearer {token.strip()}"},
                                follow_redirects=False)

    return httpx.Client(base_url=base_url, timeout=30,headers={"Accept":"application/vnd.github+json","User-Agent":"commitbot"},follow_redirects=False)


def get_pull_request(client:httpx.Client,repo:str,pr_num:int,owner:str) -> dict[str,Any]:
    try:
        response  = client.get(f"/repos/{owner}/{repo}/pulls/{pr_num}")
        response.raise_for_status()
        # execution stops if raise_for_status() unsuccessfull

        data =  response.json()
        if not isinstance(data, dict):
            raise GitHubAPIError("Expected a JSON object from GitHub")
        return data
    except httpx.TimeoutException as e:
        raise GitHubAPIError("GitHub request timed out") from e
    except httpx.RequestError as e:
        raise GitHubAPIError("Failed to send request to GitHub.") from e
    except httpx.HTTPStatusError as e:
        raise GitHubAPIError(f"GitHub API returned HTTP {e.response.status_code}") from e
    except ValueError as e:
        raise GitHubAPIError("GitHub returned invalid JSON") from e


def get_pull_request_files(client: httpx.Client,owner: str,repo: str,pr_num: int,) -> list[dict[str, Any]]:
    all_files: list[dict[str, Any]] = []
    page = 1

    try:
        while True:
            response = client.get(f"/repos/{owner}/{repo}/pulls/{pr_num}/files",params={"per_page": 100, "page": page},)
            response.raise_for_status()
            data = response.json()

            if not isinstance(data, list):
                raise GitHubAPIError("Expected a JSON list from GitHub.")

            for file_data in data:
                if not isinstance(file_data, dict):
                    raise GitHubAPIError(
                        "Expected each file entry to be a JSON object."
                    )

            all_files.extend(data)

            if len(data) < 100:
                break

            # Avoid silently accepting the endpoint's 3,000-file limit.
            if len(all_files) >= 3000:
                raise GitHubAPIError(
                    "Pull request reached GitHub's 3,000-file retrieval limit. "
                    "Complete file coverage cannot be confirmed."
                )

            page += 1

    except httpx.TimeoutException as e:
        raise GitHubAPIError("GitHub request timed out.") from e
    except httpx.RequestError as e:
        raise GitHubAPIError("Failed to send request to GitHub.") from e
    except httpx.HTTPStatusError as e:
        raise GitHubAPIError(
            f"GitHub API returned HTTP {e.response.status_code}."
        ) from e
    except ValueError as e:
        raise GitHubAPIError("GitHub returned invalid JSON.") from e

    return all_files

def filter_pull_request_files(files: list[dict[str, Any]],patterns: list[str],) -> list[dict[str, Any]]:
    allowed_files: list[dict[str, Any]] = []

    for file_data in files:
        filename = file_data.get("filename")

        if not isinstance(filename, str) or not filename.strip():
            raise GitHubAPIError("GitHub file entry has a missing or invalid filename.")

        if should_exclude_file(filename, patterns):
            continue

        if file_data.get("status") == "renamed":
            previous_filename = file_data.get("previous_filename")

            if previous_filename is not None:
                if (not isinstance(previous_filename, str)or not previous_filename.strip()):
                    raise GitHubAPIError("GitHub file entry has an invalid previous filename.")

                if should_exclude_file(previous_filename, patterns):
                    continue

        allowed_files.append(file_data)

    return allowed_files


def build_pull_request_diff(files: list[dict[str, Any]]) -> str:
    sections: list[str] = []

    for file_data in files:
        filename = file_data.get("filename")
        status = file_data.get("status")

        if not isinstance(filename, str) or not filename.strip():
            raise GitHubAPIError("Missing or invalid filename.")

        if not isinstance(status, str) or not status.strip():
            raise GitHubAPIError("Missing or invalid file status.")

        previous_filename = file_data.get("previous_filename")
        old_filename = filename

        if status == "renamed":
            if (not isinstance(previous_filename, str)or not previous_filename.strip()):
                raise GitHubAPIError("Renamed file has a missing or invalid previous filename.")
            old_filename = previous_filename

        old_path = json.dumps("a/" + old_filename)
        new_path = json.dumps("b/" + filename)

        section = (
            f"diff --git {old_path} {new_path}\n"
            f"GitHub change status: {status}\n"
        )

        if status == "renamed":
            section += (f"Previous filename: {json.dumps(previous_filename)}\n")

        source_path = "/dev/null" if status == "added" else old_path
        target_path = "/dev/null" if status == "removed" else new_path

        section += f"--- {source_path}\n+++ {target_path}\n"

        patch = file_data.get("patch")

        if patch is not None and not isinstance(patch, str):
            raise GitHubAPIError("Invalid patch value from GitHub.")

        if patch:
            section += patch
            if not section.endswith("\n"):
                section += "\n"
        else:
            section += ("Patch unavailable; only file metadata is known.\n")

        sections.append(section)

    return "\n".join(sections)




def get_recent_repository_messages(client: httpx.Client,owner: str,repo: str,ref: str,limit: int = 10,) -> list[str]:
    if limit < 1:
        raise ValueError("Limit cannot be less than 1.")

    messages: list[str] = []
    page = 1
    page_size = min(limit, 100)

    try:
        while len(messages) < limit:
            response = client.get(
                f"/repos/{owner}/{repo}/commits",
                params={
                    "sha": ref,
                    "per_page": page_size,
                    "page": page,
                },
            )
            response.raise_for_status()
            data = response.json()

            if not isinstance(data, list):
                raise GitHubAPIError("Expected a list of commits from GitHub.")

            for entry in data:
                if not isinstance(entry, dict):
                    raise GitHubAPIError("Invalid commit entry.")

                commit = entry.get("commit")
                if not isinstance(commit, dict):
                    raise GitHubAPIError("Missing or invalid commit details.")

                message = commit.get("message")
                if not isinstance(message, str):
                    raise GitHubAPIError("Missing or invalid commit message.")

                lines = message.splitlines()
                if not lines or not lines[0].strip():
                    raise GitHubAPIError("Commit title is empty.")

                messages.append(lines[0])

                if len(messages) == limit:
                    break

            if len(messages) == limit or len(data) < page_size:
                break

            page += 1

    except httpx.TimeoutException as e:
        raise GitHubAPIError("GitHub request timed out.") from e
    except httpx.RequestError as e:
        raise GitHubAPIError("Failed to send request to GitHub.") from e
    except httpx.HTTPStatusError as e:
        raise GitHubAPIError(f"GitHub API returned HTTP {e.response.status_code}.") from e
    except ValueError as e:
        raise GitHubAPIError("GitHub returned invalid JSON.") from e

    return messages

if __name__ == "__main__":
    result = parse_pull_request_url(
        "https://github.com/example/calculator/pull/12"
    )
    print("Valid URL:", result)
    print("Pass:", result == ("example", "calculator", 12))

    try:
        parse_pull_request_url(
            "https://github.com/example/calculator/issues/12"
        )
    except ValueError as e:
        print("Invalid URL rejected:", e)
    else:
        print("FAIL: Invalid URL was accepted")

    with create_github_client() as client:
        print(
            "No-token check:",
            "Authorization" not in client.headers,
        )

    with create_github_client("  dummy-token  ") as client:
        print(
            "Dummy-token check:",
            client.headers.get("Authorization") == "Bearer dummy-token",
        )

    pr_url = input("Enter a real public GitHub pull-request URL: ").strip()
    owner, repo, pr_number = parse_pull_request_url(pr_url)

    try:
        with create_github_client() as client:
            pull_request = get_pull_request(
                client=client,
                owner=owner,
                repo=repo,
                pr_num=pr_number,
            )

        print("Number:", pull_request["number"])
        print("Title:", pull_request["title"])
        print("State:", pull_request["state"])

    except GitHubAPIError as e:
        print("GitHub error:", e)
    with create_github_client() as client:
        pull_request = get_pull_request(
            client=client,
            owner=owner,
            repo=repo,
            pr_num=pr_number,
        )

        files = get_pull_request_files(
            client=client,
            owner=owner,
            repo=repo,
            pr_num=pr_number,
        )
        recent_messages = get_recent_repository_messages(
            client=client,
            owner=owner,
            repo=repo,
            ref=pull_request["base"]["sha"],
            limit=101,
        )

        print("Retrieved files:", len(files))
        print("Expected files:", pull_request["changed_files"])
        print("Counts match:", len(files) == pull_request["changed_files"])

        for file_data in files:
            print(
                "File:", file_data["filename"],
                "| Status:", file_data["status"],
                "| Has patch:", bool(file_data.get("patch")),
            )
    test_files = [
        {"filename": "src/main.py", "status": "modified", "patch": "+print('Hi')"},
        {"filename": "backend/.env", "status": "added", "patch": "+DUMMY=value"},
        {
            "filename": "config.txt",
            "previous_filename": ".env",
            "status": "renamed",
        },
        {"filename": "image.png", "status": "added"},
    ]

    filtered = filter_pull_request_files(test_files, [".env"])
    remaining = [entry["filename"] for entry in filtered]

    print("Remaining files:", remaining)
    print("Filtering passed:", remaining == ["src/main.py", "image.png"])
    print("Entries preserved:", filtered == [test_files[0], test_files[3]])

    excluded = filter_pull_request_files(test_files, ["*"])
    print("All-excluded check:", excluded == [])

    try:
        filter_pull_request_files([{"status": "added"}], [])
    except GitHubAPIError as e:
        print("Missing filename rejected:", e)
    else:
        print("FAIL: Missing filename was accepted")

    sample_files = [
        {
            "filename": "calculator.py",
            "status": "modified",
            "patch": "@@ -1 +1 @@\n-return a-b\n+return a+b",
        },
        {
            "filename": "docs/new guide.md",
            "previous_filename": "docs/old guide.md",
            "status": "renamed",
        },
        {
            "filename": "image.png",
            "status": "added",
        },
    ]

    sample_diff = build_pull_request_diff(sample_files)
    print("\n=== Constructed PR diff ===")
    print(sample_diff)

    print("Empty input check:", build_pull_request_diff([]) == "")
    print(
        "Patch preserved:",
        sample_files[0]["patch"] in sample_diff,
    )
    print(
        "Rename metadata included:",
        'Previous filename: "docs/old guide.md"' in sample_diff,
    )
    print(
        "Missing patch explained:",
        "Patch unavailable; only file metadata is known." in sample_diff,
    )



    print("\nRecent base-repository commit titles:")
    for number, message in enumerate(recent_messages, start=1):
        print(f"{number}. {message}")

    print("At most 3 titles:", len(recent_messages) <= 3)
    print(
        "Single-line titles:",
        all(
            "\n" not in message and "\r" not in message
            for message in recent_messages
        ),
    )
    print("\nRetrieved commit titles:", len(recent_messages))
    print("Pagination count check:", len(recent_messages) == 101)
    print(
        "Single-line titles:",
        all(
            "\n" not in message and "\r" not in message
            for message in recent_messages
        ),
    )
    print("First title:", recent_messages[0])
    print("Last title:", recent_messages[-1])