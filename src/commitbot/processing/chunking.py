

from commitbot.processing.diff_parser import split_diff_by_file


def chunk_diff(diff_str: str, max_chars: int) -> list[str]:
    """
    Splits a git diff into chunks that do not exceed max_chars.

    Combines consecutive file sections within max_chars. Oversized sections
    flush existing accumulations and are sliced into max_chars-sized windows.
    """
    if max_chars < 1:
        raise ValueError("max_chars must be at least 1")

    if not diff_str:
        return []

    file_sections = split_diff_by_file(diff_str)
    chunks: list[str] = []
    current_chunk = ""

    for section in file_sections:

        if len(section) > max_chars:

            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""


            start = 0
            while start < len(section):
                chunks.append(section[start: start + max_chars])
                start += max_chars


        elif len(current_chunk) + len(section) <= max_chars:
            current_chunk += section


        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = section


    if current_chunk:
        chunks.append(current_chunk)

    return chunks





if __name__ == "__main__":
    print("=== Case 1: Empty Diff ===")
    res1 = chunk_diff("", 100)
    print(f"Chunks returned : {res1}")
    print(f"Matches original: {'' == ''.join(res1)}\n")

    print("=== Case 2: max_chars = 0 ===")
    try:
        chunk_diff("diff --git a/a b/a\n", 0)
    except ValueError as e:
        print(f"Caught error    : {e}\n")

    sec_a = "diff --git a/calc.py b/calc.py\n+add()\n"
    sec_b = "diff --git a/util.py b/util.py\n+log()\n"
    small_diff = sec_a + sec_b
    limit_fit = 100

    print("=== Case 3: Sections Fit Together ===")
    print(f"Total diff length: {len(small_diff)} chars | limit: {limit_fit}")
    res3 = chunk_diff(small_diff, limit_fit)
    print(f"Number of chunks : {len(res3)}")
    for i, chunk in enumerate(res3):
        print(f"  Chunk {i} ({len(chunk)} chars):\n{repr(chunk)}")
    print(f"Every chunk <= {limit_fit}: {all(len(c) <= limit_fit for c in res3)}")
    print(f"Matches original     : {''.join(res3) == small_diff}\n")

    limit_tight = 45
    print("=== Case 4: Sections Exceed Limit Together ===")
    print(f"sec_a: {len(sec_a)} chars, sec_b: {len(sec_b)} chars | limit: {limit_tight}")
    res4 = chunk_diff(small_diff, limit_tight)
    print(f"Number of chunks : {len(res4)}")
    for i, chunk in enumerate(res4):
        print(f"  Chunk {i} ({len(chunk)} chars):\n{repr(chunk)}")
    print(f"Every chunk <= {limit_tight}: {all(len(c) <= limit_tight for c in res4)}")
    print(f"Matches original     : {''.join(res4) == small_diff}\n")

    oversized_diff = "diff --git a/big.py b/big.py\n" + ("x" * 70) + "\n"
    slice_limit = 30

    print("=== Case 5: Oversized Section Slicing ===")
    print(f"Total diff length: {len(oversized_diff)} chars | limit: {slice_limit}")
    res5 = chunk_diff(oversized_diff, slice_limit)
    print(f"Number of chunks : {len(res5)}")
    for i, chunk in enumerate(res5):
        print(f"  Chunk {i} ({len(chunk)} chars):\n{repr(chunk)}")
    print(f"Every chunk <= {slice_limit}: {all(len(c) <= slice_limit for c in res5)}")
    print(f"Matches original     : {''.join(res5) == oversized_diff}")