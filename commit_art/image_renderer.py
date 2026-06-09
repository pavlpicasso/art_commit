from __future__ import annotations

from pathlib import Path
from typing import Any

from commit_art.map_parser import MAP_COLUMNS, MAP_ROWS


class ImageRenderError(ValueError):
    """Raised when an image cannot be converted into a contribution map."""


def render_image_map(
    path: Path,
    levels: dict[str, int],
    mode: str = "contain",
    invert: bool = False,
) -> list[str]:
    try:
        from PIL import Image
    except ImportError as error:
        raise ImageRenderError("Image import requires Pillow. Install it with: pip install pillow") from error

    try:
        with Image.open(path) as image:
            return image_to_map(image, levels=levels, mode=mode, invert=invert)
    except OSError as error:
        raise ImageRenderError(f"Could not read image {path}: {error}") from error


def image_to_map(image: Any, levels: dict[str, int], mode: str = "contain", invert: bool = False) -> list[str]:
    if not levels:
        raise ImageRenderError("At least one configured level is required.")
    if mode not in {"stretch", "contain", "cover"}:
        raise ImageRenderError("Image mode must be one of: stretch, contain, cover.")

    try:
        from PIL import Image, ImageOps
    except ImportError as error:
        raise ImageRenderError("Image import requires Pillow. Install it with: pip install pillow") from error

    source = image.convert("RGBA")
    canvas = Image.new("RGBA", source.size, (255, 255, 255, 255))
    canvas.alpha_composite(source)
    source = canvas.convert("L")

    resampling = getattr(Image.Resampling, "LANCZOS", Image.LANCZOS)
    target_size = (MAP_COLUMNS, MAP_ROWS)
    if mode == "stretch":
        prepared = source.resize(target_size, resampling)
    elif mode == "cover":
        prepared = ImageOps.fit(source, target_size, method=resampling, centering=(0.5, 0.5))
    else:
        contained = ImageOps.contain(source, target_size, method=resampling)
        prepared = Image.new("L", target_size, 255)
        offset = ((MAP_COLUMNS - contained.width) // 2, (MAP_ROWS - contained.height) // 2)
        prepared.paste(contained, offset)

    symbols = _symbols_by_intensity(levels)
    rows: list[str] = []
    for y in range(MAP_ROWS):
        chars = []
        for x in range(MAP_COLUMNS):
            gray = prepared.getpixel((x, y))
            intensity = gray if invert else 255 - gray
            chars.append(_symbol_for_intensity(intensity, symbols))
        rows.append("".join(chars))
    return rows


def _symbols_by_intensity(levels: dict[str, int]) -> list[str]:
    return [symbol for symbol, _count in sorted(levels.items(), key=lambda item: item[1])]


def _symbol_for_intensity(intensity: int, symbols: list[str]) -> str:
    if intensity <= 0:
        return " "

    bucket_count = len(symbols) + 1
    bucket = min(bucket_count - 1, int(intensity * bucket_count / 256))
    if bucket <= 0:
        return " "
    return symbols[bucket - 1]
