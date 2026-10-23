from commitbot.processing.diff_parser import split_diff_by_file


def split_oversized_section(section: str, max_chars: int) -> list[str]:
    """Split a file diff at line boundaries, repeating file and hunk context."""
    if max_chars < 1:
        raise ValueError("max_chars must be at least 1")

    lines = section.splitlines(keepends=True)

    first_hunk = next(
        (i for i, line in enumerate(lines) if line.startswith("@@ ")),
        None,
    )
    if first_hunk is None:
        raise ValueError(
            "Oversized diff section has no hunk header; "
            "increase max_diff_chars."
        )

    file_header = "".join(lines[:first_hunk])
    if not file_header.endswith("\n"):
        file_header += "\n"

    label = "Partial file diff; repeated headers provide context.\n"
    fragments: list[str] = []
    current_lines: list[str] = []
    prefix = ""
    current_length = 0

    for line in lines[first_hunk:]:
        if line.startswith("@@ "):
            # Begin a new hunk with its own context.
            if current_lines:
                fragments.append(prefix + "".join(current_lines))
                current_lines = []

            hunk_header = line
            if not hunk_header.endswith("\n"):
                hunk_header += "\n"

            prefix = label + file_header + hunk_header
            current_length = len(prefix)
            continue

        if len(prefix) + len(line) > max_chars:
            raise ValueError(
                "A diff line cannot fit with its file and hunk headers. "
                "Increase max_diff_chars."
            )

        if current_length + len(line) > max_chars:
            fragments.append(prefix + "".join(current_lines))
            current_lines = []
            current_length = len(prefix)

        current_lines.append(line)
        current_length += len(line)

    if current_lines:
        fragments.append(prefix + "".join(current_lines))

    if not fragments:
        raise ValueError(
            "Oversized diff contains no hunk content to summarize."
        )

    return fragments


def chunk_diff(diff_str: str, max_chars: int) -> list[str]:
    """Combine file diffs, splitting oversized files with repeated context."""
    if max_chars < 1:
        raise ValueError("max_chars must be at least 1")

    if not diff_str:
        return []

    chunks: list[str] = []
    current_chunk = ""

    for section in split_diff_by_file(diff_str):
        if len(section) > max_chars:
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""

            chunks.extend(split_oversized_section(section, max_chars))

        elif len(current_chunk) + len(section) <= max_chars:
            current_chunk += section

        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = section

    if current_chunk:
        chunks.append(current_chunk)

    return chunks