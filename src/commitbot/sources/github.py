from typing import Any

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