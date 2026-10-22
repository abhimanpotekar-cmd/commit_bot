import fnmatch
from pathlib import PurePosixPath
from typing import Sequence


def should_exclude_file(file_path: str, patterns: Sequence[str]) -> bool:
    """Check if a repository-relative file path matches any exclusion pattern."""
    normalized_path = file_path.replace("\\", "/")
    filename = PurePosixPath(normalized_path).name

    for pattern in patterns:
        normalized_pattern = pattern.replace("\\", "/")

        if "/" in normalized_pattern:
            if fnmatch.fnmatchcase(normalized_path, normalized_pattern):
                return True
        else:
            if fnmatch.fnmatchcase(filename, normalized_pattern):
                return True

    return False

if __name__=="__main__":
    test_cases = [
        ("backend/.env", [".env"], True),
        ("certs/private.key", ["*.key"], True),
        ("src/main.py", ["*.key"], False),
        (r"backend\.env", [".env"], True),
        ("certs/private.key", ["certs/*.key"], True),
        ("src/main.py", [], False),
    ]

    for path, patterns, expected in test_cases:
        actual = should_exclude_file(path, patterns)
        matches = actual == expected
        print(
            f"Path: {path:<20} | "
            f"Actual: {str(actual):<5} | "
            f"Expected: {str(expected):<5} | "
            f"Pass: {matches}"
        )