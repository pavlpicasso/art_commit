from __future__ import annotations


MAP_ROWS = 7
MAP_COLUMNS = 52


class CommitMapError(ValueError):
    """Raised when a contribution map cannot be converted to commits."""


def validate_commit_map(commit_map: list[str], levels: dict[str, int]) -> None:
    if len(commit_map) != MAP_ROWS:
        raise CommitMapError(f"Commit map must contain {MAP_ROWS} rows, got {len(commit_map)}.")

    allowed = set(levels) | {" "}
    for row_number, row in enumerate(commit_map, start=1):
        if len(row) != MAP_COLUMNS:
            raise CommitMapError(
                f"Commit map row {row_number} must contain {MAP_COLUMNS} characters, got {len(row)}."
            )

        unknown = sorted(set(row) - allowed)
        if unknown:
            printable = ", ".join(repr(char) for char in unknown)
            raise CommitMapError(f"Commit map row {row_number} contains unsupported characters: {printable}.")


def commit_count_for_cell(char: str, levels: dict[str, int]) -> int:
    if char == " ":
        return 0
    return levels[char]
