from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import tomllib
from typing import Any


DEFAULT_MAP = [
    "   *####     #      ###   #####   #   #    *###*    ",
    "   #                  #   #       #  #    #     #   ",
    "   #       #####      #   #       # #     #     #   ",
    "   *###*     #        #   ###     ##*     #     #   ",
    "       #     #        #   #       #  #    #     #   ",
    "       #     #    #   #   #       #   #   #     #   ",
    "   ####*   #####   *##*   #####   #    #   *###*    ",
]

DEFAULT_LEVELS = {".": 4, ":": 8, "*": 12, "#": 20}


@dataclass(frozen=True)
class CommitArtConfig:
    commit_map: list[str] = field(default_factory=lambda: DEFAULT_MAP.copy())
    levels: dict[str, int] = field(default_factory=lambda: DEFAULT_LEVELS.copy())
    repo_dir: Path = Path("repo")
    commit_file: str = "commit_art.md"
    origin: str = "https://github.com/your-name/commit-art.git"
    branch: str = "master"
    timezone: str = "+0300"
    commit_hour: int = 12
    message_prefix: str = "Commit art"
    author_name: str = "Commit Art"
    author_email: str = "commit-art@example.com"


class ConfigError(ValueError):
    """Raised when config.toml contains invalid values."""


def load_config(path: Path) -> CommitArtConfig:
    if not path.exists():
        return CommitArtConfig()

    with path.open("rb") as file:
        data = tomllib.load(file)

    if not isinstance(data, dict):
        raise ConfigError("Config root must be a TOML table.")

    return CommitArtConfig(
        commit_map=_read_commit_map(data.get("map", DEFAULT_MAP)),
        levels=_read_levels(data.get("levels", DEFAULT_LEVELS)),
        repo_dir=Path(_read_str(data, "repo_dir", "repo")),
        commit_file=_read_str(data, "commit_file", "commit_art.md"),
        origin=_read_str(data, "origin", "https://github.com/your-name/commit-art.git"),
        branch=_read_str(data, "branch", "master"),
        timezone=_read_str(data, "timezone", "+0300"),
        commit_hour=_read_int(data, "commit_hour", 12),
        message_prefix=_read_str(data, "message_prefix", "Commit art"),
        author_name=_read_str(data, "author_name", "Commit Art"),
        author_email=_read_str(data, "author_email", "commit-art@example.com"),
    )


def _read_commit_map(value: Any) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(row, str) for row in value):
        raise ConfigError("Config field 'map' must be an array of strings.")
    return value.copy()


def _read_levels(value: Any) -> dict[str, int]:
    if not isinstance(value, dict):
        raise ConfigError("Config field 'levels' must be a table.")

    levels: dict[str, int] = {}
    for key, count in value.items():
        if not isinstance(key, str) or len(key) != 1:
            raise ConfigError("Each key in 'levels' must be exactly one character.")
        if key == " ":
            raise ConfigError("Space is reserved for empty cells and cannot be configured in 'levels'.")
        if not isinstance(count, int) or count < 1:
            raise ConfigError(f"Level {key!r} must be a positive integer.")
        levels[key] = count

    if not levels:
        raise ConfigError("Config field 'levels' must not be empty.")
    return levels


def _read_str(data: dict[str, Any], key: str, default: str) -> str:
    value = data.get(key, default)
    if not isinstance(value, str):
        raise ConfigError(f"Config field '{key}' must be a string.")
    return value


def _read_int(data: dict[str, Any], key: str, default: int) -> int:
    value = data.get(key, default)
    if not isinstance(value, int):
        raise ConfigError(f"Config field '{key}' must be an integer.")
    return value
