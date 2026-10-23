def split_diff_by_file(diff_str: str) -> list[str]:
    sections: list[str] = []
    current_lines: list[str] = []

    for line in diff_str.splitlines(keepends=True):
        # When a new file header is encountered and we already collected lines,
        # close the current file section and start a new one.
        if line.startswith("diff --git ") and current_lines:
            sections.append("".join(current_lines))
            current_lines = []

        current_lines.append(line)

    # Flush any remaining lines for the final file
    if current_lines:
        sections.append("".join(current_lines))

    return sections



if __name__ == "__main__":

    print("--- 1. Empty Diff ---")
    empty_result = split_diff_by_file("")
    print(f"Result: {empty_result}\n")


    print("--- 2. Single File Diff ---")
    calc_diff = (
        "diff --git a/calculator.py b/calculator.py\n"
        "index 83a21b2..d12ef43 100644\n"
        "--- a/calculator.py\n"
        "+++ b/calculator.py\n"
        "@@ -1,3 +1,3 @@\n"
        "-def add(a, b): return a - b\n"
        "+def add(a, b): return a + b\n"
    )
    calc_result = split_diff_by_file(calc_diff)
    print(f"Sections found: {len(calc_result)}")
    print(f"Section 0 content:\n{calc_result[0]}")


    print("--- 3. Two File Diff ---")
    two_file_diff = (
        "diff --git a/calculator.py b/calculator.py\n"
        "--- a/calculator.py\n"
        "+++ b/calculator.py\n"
        "@@ -1 +1 @@\n"
        "+# calculator logic\n"
        "diff --git a/README.md b/README.md\n"
        "--- a/README.md\n"
        "+++ b/README.md\n"
        "@@ -1 +1 @@\n"
        "+# Documentation\n"
    )
    two_result = split_diff_by_file(two_file_diff)
    print(f"Sections found: {len(two_result)}")
    for idx, sec in enumerate(two_result):
        print(f"\n--- Section {idx} ---")
        print(sec, end="")

    print("\n--- 4. Round-Trip Check ---")
    reconstructed = "".join(two_result)
    is_identical = reconstructed == two_file_diff
    print(f"Does joining match the original exactly? {is_identical}")