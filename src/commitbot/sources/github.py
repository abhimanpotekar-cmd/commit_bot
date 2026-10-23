import urllib.parse


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