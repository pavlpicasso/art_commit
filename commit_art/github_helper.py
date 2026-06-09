from __future__ import annotations

import subprocess
from pathlib import Path

from commit_art.config import CommitArtConfig


class GitHubCreateError(RuntimeError):
    """Raised when a GitHub repository cannot be created through gh."""


def create_github_repository(
    config: CommitArtConfig,
    name: str,
    visibility: str = "private",
    description: str | None = None,
    use_source: bool = True,
    remote: str = "origin",
    push: bool = False,
) -> str:
    source = config.repo_dir if use_source else None
    args = _build_github_create_args(
        name=name,
        visibility=visibility,
        description=description,
        source=source,
        remote=remote,
        push=push,
    )

    try:
        result = subprocess.run(
            ["gh", *args],
            text=True,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError as error:
        raise GitHubCreateError("GitHub CLI 'gh' is not installed or is not available in PATH.") from error

    if result.returncode != 0:
        details = (result.stderr or result.stdout).strip()
        raise GitHubCreateError(f"gh {' '.join(args)} failed: {details}")

    return (result.stdout or result.stderr).strip()


def _build_github_create_args(
    name: str,
    visibility: str,
    description: str | None = None,
    source: Path | None = None,
    remote: str = "origin",
    push: bool = False,
) -> list[str]:
    if not name.strip():
        raise GitHubCreateError("Repository name must not be empty.")
    if visibility not in {"private", "public", "internal"}:
        raise GitHubCreateError("Visibility must be one of: private, public, internal.")
    if source is None and push:
        raise GitHubCreateError("--push requires a source repository.")
    if source is not None and not remote.strip():
        raise GitHubCreateError("Remote name must not be empty when source is used.")

    args = ["repo", "create", name, f"--{visibility}"]
    if description:
        args.extend(["--description", description])
    if source is not None:
        args.extend(["--source", str(source), "--remote", remote])
    if push:
        args.append("--push")
    return args
