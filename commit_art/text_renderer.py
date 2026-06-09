from __future__ import annotations

from commit_art.map_parser import MAP_COLUMNS, MAP_ROWS


class TextRenderError(ValueError):
    """Raised when text cannot be rendered into a contribution map."""


FONT_5X7: dict[str, tuple[str, ...]] = {
    "A": (" ### ", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"),
    "B": ("#### ", "#   #", "#   #", "#### ", "#   #", "#   #", "#### "),
    "C": (" ####", "#    ", "#    ", "#    ", "#    ", "#    ", " ####"),
    "D": ("#### ", "#   #", "#   #", "#   #", "#   #", "#   #", "#### "),
    "E": ("#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#####"),
    "F": ("#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#    "),
    "G": (" ####", "#    ", "#    ", "#  ##", "#   #", "#   #", " ####"),
    "H": ("#   #", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"),
    "I": ("#####", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "#####"),
    "J": ("#####", "   # ", "   # ", "   # ", "   # ", "#  # ", " ##  "),
    "K": ("#   #", "#  # ", "# #  ", "##   ", "# #  ", "#  # ", "#   #"),
    "L": ("#    ", "#    ", "#    ", "#    ", "#    ", "#    ", "#####"),
    "M": ("#   #", "## ##", "# # #", "#   #", "#   #", "#   #", "#   #"),
    "N": ("#   #", "##  #", "# # #", "#  ##", "#   #", "#   #", "#   #"),
    "O": (" ### ", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "),
    "P": ("#### ", "#   #", "#   #", "#### ", "#    ", "#    ", "#    "),
    "Q": (" ### ", "#   #", "#   #", "#   #", "# # #", "#  # ", " ## #"),
    "R": ("#### ", "#   #", "#   #", "#### ", "# #  ", "#  # ", "#   #"),
    "S": (" ####", "#    ", "#    ", " ### ", "    #", "    #", "#### "),
    "T": ("#####", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  "),
    "U": ("#   #", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "),
    "V": ("#   #", "#   #", "#   #", "#   #", "#   #", " # # ", "  #  "),
    "W": ("#   #", "#   #", "#   #", "# # #", "# # #", "## ##", "#   #"),
    "X": ("#   #", "#   #", " # # ", "  #  ", " # # ", "#   #", "#   #"),
    "Y": ("#   #", "#   #", " # # ", "  #  ", "  #  ", "  #  ", "  #  "),
    "Z": ("#####", "    #", "   # ", "  #  ", " #   ", "#    ", "#####"),
    "0": (" ### ", "#   #", "#  ##", "# # #", "##  #", "#   #", " ### "),
    "1": ("  #  ", " ##  ", "# #  ", "  #  ", "  #  ", "  #  ", "#####"),
    "2": (" ### ", "#   #", "    #", "   # ", "  #  ", " #   ", "#####"),
    "3": ("#### ", "    #", "    #", " ### ", "    #", "    #", "#### "),
    "4": ("#   #", "#   #", "#   #", "#####", "    #", "    #", "    #"),
    "5": ("#####", "#    ", "#    ", "#### ", "    #", "    #", "#### "),
    "6": (" ### ", "#    ", "#    ", "#### ", "#   #", "#   #", " ### "),
    "7": ("#####", "    #", "   # ", "  #  ", " #   ", " #   ", " #   "),
    "8": (" ### ", "#   #", "#   #", " ### ", "#   #", "#   #", " ### "),
    "9": (" ### ", "#   #", "#   #", " ####", "    #", "    #", " ### "),
    "-": ("     ", "     ", "     ", " ### ", "     ", "     ", "     "),
    "_": ("     ", "     ", "     ", "     ", "     ", "     ", "#####"),
    "!": ("  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "     ", "  #  "),
    "?": (" ### ", "#   #", "    #", "   # ", "  #  ", "     ", "  #  "),
    ".": ("     ", "     ", "     ", "     ", "     ", "     ", "  #  "),
    " ": ("     ", "     ", "     ", "     ", "     ", "     ", "     "),
}


def render_text_map(text: str, level: str = "#", letter_spacing: int = 1, align: str = "center") -> list[str]:
    normalized = text.upper()
    if not normalized:
        raise TextRenderError("Text must not be empty.")
    if len(level) != 1 or level == " ":
        raise TextRenderError("Level must be exactly one non-space character.")
    if letter_spacing < 0:
        raise TextRenderError("Letter spacing must be zero or greater.")
    if align not in {"left", "center", "right"}:
        raise TextRenderError("Align must be one of: left, center, right.")

    rows = ["" for _ in range(MAP_ROWS)]
    for index, char in enumerate(normalized):
        glyph = FONT_5X7.get(char)
        if glyph is None:
            raise TextRenderError(f"Unsupported character: {char!r}.")
        if index:
            for row in range(MAP_ROWS):
                rows[row] += " " * letter_spacing
        for row in range(MAP_ROWS):
            rows[row] += glyph[row].replace("#", level)

    width = len(rows[0])
    if width > MAP_COLUMNS:
        raise TextRenderError(f"Rendered text is {width} columns wide, maximum is {MAP_COLUMNS}.")

    if align == "left":
        left_padding = 0
    elif align == "right":
        left_padding = MAP_COLUMNS - width
    else:
        left_padding = (MAP_COLUMNS - width) // 2

    right_padding = MAP_COLUMNS - width - left_padding
    return [(" " * left_padding) + row + (" " * right_padding) for row in rows]


def format_toml_map(commit_map: list[str]) -> str:
    lines = ["map = ["]
    lines.extend(f'  "{row}",' for row in commit_map)
    lines.append("]")
    return "\n".join(lines)
