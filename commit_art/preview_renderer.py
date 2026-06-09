from __future__ import annotations

from commit_art.map_parser import MAP_COLUMNS, MAP_ROWS, commit_count_for_cell, validate_commit_map


ANSI_RESET = "\033[0m"
ANSI_LEVELS = [
    "\033[48;5;236m",
    "\033[48;5;22m",
    "\033[48;5;28m",
    "\033[48;5;34m",
    "\033[48;5;40m",
]
PLAIN_LEVELS = ["  ", "..", "::", "**", "##"]


def render_visual_map(commit_map: list[str], levels: dict[str, int], color: bool = True) -> str:
    validate_commit_map(commit_map, levels)

    lines = ["    " + "".join(f"{week % 10} " for week in range(1, MAP_COLUMNS + 1))]
    for row_index, row in enumerate(commit_map):
        label = _weekday_label(row_index)
        cells = [_render_cell(commit_count_for_cell(char, levels), levels, color=color) for char in row]
        lines.append(f"{label} " + "".join(cells))

    lines.append("")
    lines.append(_render_legend(levels, color=color))
    return "\n".join(lines)


def _render_cell(count: int, levels: dict[str, int], color: bool) -> str:
    index = _level_index(count, levels)
    if not color:
        return PLAIN_LEVELS[index]
    return f"{ANSI_LEVELS[index]}  {ANSI_RESET}"


def _render_legend(levels: dict[str, int], color: bool) -> str:
    sorted_counts = sorted(levels.values())
    parts = [_render_cell(0, levels, color)]
    parts.extend(_render_cell(count, levels, color) for count in sorted_counts)
    return "Less " + "".join(parts) + " More"


def _level_index(count: int, levels: dict[str, int]) -> int:
    if count <= 0:
        return 0

    sorted_counts = sorted(levels.values())
    for index, threshold in enumerate(sorted_counts, start=1):
        if count <= threshold:
            return index
    return len(sorted_counts)


def _weekday_label(row_index: int) -> str:
    labels = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    if row_index < 0 or row_index >= MAP_ROWS:
        raise ValueError(f"Weekday row index must be between 0 and {MAP_ROWS - 1}.")
    return labels[row_index]
