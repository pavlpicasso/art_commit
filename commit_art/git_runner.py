from __future__ import annotations

import os
import shutil
import stat
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from commit_art.config import CommitArtConfig
from commit_art.generator import PlannedCommitDay


class GitApplyError(RuntimeError):
    """Raised when commits cannot be applied to the local repository."""


class GitPushError(RuntimeError):
    """Raised when commits cannot be pushed safely."""


@dataclass(frozen=True)
class RepoStatus:
    path: Path
    exists: bool
    is_dir: bool
    is_empty: bool
    is_git: bool
    is_dirty: bool
    branch: str | None
    origin: str | None


@dataclass(frozen=True)
class PushChunk:
    commit_count: int
    commit: str
    output: str


def apply_plan(
    config: CommitArtConfig,
    plan: list[PlannedCommitDay],
    allow_existing: bool = False,
    reset_repo: bool = False,
    allow_dirty: bool = False,
) -> int:
    repo_dir = config.repo_dir
    _prepare_repo_dir(config, allow_existing=allow_existing, reset_repo=reset_repo, allow_dirty=allow_dirty)

    _run_git(repo_dir, ["init"], config)
    _run_git(repo_dir, ["checkout", "-B", config.branch], config)

    commit_path = repo_dir / config.commit_file
    commit_path.parent.mkdir(parents=True, exist_ok=True)
    commit_path.write_text("# Commit Art\n", encoding="utf-8", newline="\n")

    total_commits = 0
    for item in plan:
        _append(commit_path, f"\n## {item.day.isoformat()}\n")
        for index in range(item.count):
            minute = f"{index:02d}"
            message = f"{config.message_prefix} #{index + 1}"
            commit_date = f"{item.day.isoformat()}T{config.commit_hour:02d}:{minute}:00{config.timezone}"

            _append(commit_path, f"* {message}\n")
            _run_git(repo_dir, ["add", config.commit_file], config)
            _run_git(
                repo_dir,
                ["commit", "-m", message, f"--date={commit_date}"],
                config,
                extra_env={
                    "GIT_AUTHOR_DATE": commit_date,
                    "GIT_COMMITTER_DATE": commit_date,
                },
            )
            total_commits += 1

    if config.origin:
        _set_origin(repo_dir, config)

    return total_commits


def push_repo(
    config: CommitArtConfig,
    force: bool = False,
    allow_dirty: bool = False,
    set_upstream: bool = True,
) -> str:
    _ensure_safe_repo_path(config.repo_dir)
    status = inspect_repo(config)

    if not status.exists:
        raise GitPushError(f"{config.repo_dir} does not exist. Run apply first.")
    if not status.is_dir:
        raise GitPushError(f"{config.repo_dir} is not a directory.")
    if not status.is_git:
        raise GitPushError(f"{config.repo_dir} is not a git repository. Run apply first.")
    if status.is_dirty and not allow_dirty:
        raise GitPushError(f"{config.repo_dir} has uncommitted changes. Re-run with --allow-dirty if this is intentional.")
    if not config.origin:
        raise GitPushError("origin is empty in config.toml.")

    try:
        if status.origin != config.origin:
            _set_origin(config.repo_dir, config)

        result = _run_git(config.repo_dir, _build_push_args(config, force=force, set_upstream=set_upstream), config)
    except GitApplyError as error:
        raise GitPushError(str(error)) from error
    return (result.stdout or result.stderr).strip()


def push_repo_in_chunks(
    config: CommitArtConfig,
    chunk_size: int,
    delay_seconds: int = 0,
    allow_dirty: bool = False,
    set_upstream: bool = True,
) -> list[PushChunk]:
    if chunk_size < 1:
        raise GitPushError("chunk_size must be greater than 0.")
    if delay_seconds < 0:
        raise GitPushError("delay_seconds must not be negative.")

    _ensure_pushable_repo(config, allow_dirty=allow_dirty)
    try:
        commits_result = _run_git(config.repo_dir, ["rev-list", "--reverse", "HEAD"], config)
    except GitApplyError as error:
        raise GitPushError(str(error)) from error
    commits = [line for line in commits_result.stdout.splitlines() if line]
    if not commits:
        raise GitPushError(f"{config.repo_dir} has no commits to push.")

    chunks: list[PushChunk] = []
    for index in _chunk_end_indexes(len(commits), chunk_size):
        commit = commits[index]
        try:
            result = _run_git(
                config.repo_dir,
                _build_chunk_push_args(config, commit, set_upstream=set_upstream),
                config,
            )
        except GitApplyError as error:
            raise GitPushError(str(error)) from error
        chunks.append(PushChunk(commit_count=index + 1, commit=commit, output=(result.stdout or result.stderr).strip()))
        if delay_seconds and index != len(commits) - 1:
            time.sleep(delay_seconds)

    return chunks


def _ensure_pushable_repo(config: CommitArtConfig, allow_dirty: bool) -> RepoStatus:
    _ensure_safe_repo_path(config.repo_dir)
    status = inspect_repo(config)

    if not status.exists:
        raise GitPushError(f"{config.repo_dir} does not exist. Run apply first.")
    if not status.is_dir:
        raise GitPushError(f"{config.repo_dir} is not a directory.")
    if not status.is_git:
        raise GitPushError(f"{config.repo_dir} is not a git repository. Run apply first.")
    if status.is_dirty and not allow_dirty:
        raise GitPushError(f"{config.repo_dir} has uncommitted changes. Re-run with --allow-dirty if this is intentional.")
    if not config.origin:
        raise GitPushError("origin is empty in config.toml.")

    try:
        if status.origin != config.origin:
            _set_origin(config.repo_dir, config)
    except GitApplyError as error:
        raise GitPushError(str(error)) from error

    return status


def _build_push_args(config: CommitArtConfig, force: bool, set_upstream: bool) -> list[str]:
    args = ["push"]
    if set_upstream:
        args.append("-u")
    args.extend(["origin", config.branch])
    if force:
        args.append("--force-with-lease")
    return args


def _build_chunk_push_args(config: CommitArtConfig, commit: str, set_upstream: bool) -> list[str]:
    args = ["push"]
    if set_upstream:
        args.append("-u")
    args.extend(["origin", f"{commit}:refs/heads/{config.branch}", "--force"])
    return args


def _chunk_end_indexes(commit_count: int, chunk_size: int) -> list[int]:
    indexes = list(range(chunk_size - 1, commit_count, chunk_size))
    final_index = commit_count - 1
    if not indexes or indexes[-1] != final_index:
        indexes.append(final_index)
    return indexes


def inspect_repo(config: CommitArtConfig) -> RepoStatus:
    repo_dir = config.repo_dir
    if not repo_dir.exists():
        return RepoStatus(repo_dir, exists=False, is_dir=False, is_empty=True, is_git=False, is_dirty=False, branch=None, origin=None)

    if not repo_dir.is_dir():
        return RepoStatus(repo_dir, exists=True, is_dir=False, is_empty=False, is_git=False, is_dirty=False, branch=None, origin=None)

    entries = list(repo_dir.iterdir())
    is_git = (repo_dir / ".git").is_dir()
    branch = None
    origin = None
    is_dirty = False

    if is_git:
        branch_result = _run_git(repo_dir, ["branch", "--show-current"], config, check=False)
        branch = branch_result.stdout.strip() or None if branch_result.returncode == 0 else None

        origin_result = _run_git(repo_dir, ["remote", "get-url", "origin"], config, check=False)
        origin = origin_result.stdout.strip() or None if origin_result.returncode == 0 else None

        is_dirty = _is_dirty(repo_dir, config)

    return RepoStatus(
        repo_dir,
        exists=True,
        is_dir=True,
        is_empty=len(entries) == 0,
        is_git=is_git,
        is_dirty=is_dirty,
        branch=branch,
        origin=origin,
    )


def _prepare_repo_dir(
    config: CommitArtConfig,
    allow_existing: bool,
    reset_repo: bool = False,
    allow_dirty: bool = False,
) -> None:
    repo_dir = config.repo_dir
    _ensure_safe_repo_path(repo_dir)

    if reset_repo:
        if repo_dir.exists():
            _remove_tree(repo_dir)
        _mkdir_repo_dir(repo_dir)
        return

    if not repo_dir.exists():
        _mkdir_repo_dir(repo_dir)
        return

    if not repo_dir.is_dir():
        raise GitApplyError(f"Repository path is not a directory: {repo_dir}")

    entries = list(repo_dir.iterdir())
    if not entries:
        return

    if (repo_dir / ".git").is_dir():
        if not allow_existing:
            raise GitApplyError(
                f"{repo_dir} is already a git repository. Re-run with --allow-existing to append commits "
                "or --reset-repo to recreate it."
            )
        if _is_dirty(repo_dir, config) and not allow_dirty:
            raise GitApplyError(f"{repo_dir} has uncommitted changes. Re-run with --allow-dirty if this is intentional.")
        return

    raise GitApplyError(f"{repo_dir} is not empty. Use an empty directory or --reset-repo to recreate it.")


def _ensure_safe_repo_path(repo_dir: Path) -> Path:
    workspace = Path.cwd().resolve()
    resolved = repo_dir.resolve()

    if resolved == workspace:
        raise GitApplyError("repo_dir must not be the project root. Use a dedicated child directory such as 'repo'.")

    if workspace not in resolved.parents:
        raise GitApplyError(f"repo_dir must stay inside the current workspace: {workspace}")

    return resolved


def _mkdir_repo_dir(repo_dir: Path) -> None:
    try:
        repo_dir.mkdir(parents=True, exist_ok=False)
    except OSError as error:
        raise GitApplyError(f"Could not create repo_dir {repo_dir}: {error}") from error


def _remove_tree(path: Path) -> None:
    try:
        shutil.rmtree(path, onexc=_make_writable_and_retry)
    except OSError as error:
        raise GitApplyError(f"Could not reset repo_dir {path}: {error}") from error


def _make_writable_and_retry(function, path: str, excinfo) -> None:
    try:
        os.chmod(path, stat.S_IREAD | stat.S_IWRITE)
        function(path)
    except OSError:
        if isinstance(excinfo, BaseException):
            raise excinfo
        raise excinfo[1]


def _is_dirty(repo_dir: Path, config: CommitArtConfig) -> bool:
    result = _run_git(repo_dir, ["status", "--porcelain"], config, check=False)
    return result.returncode == 0 and bool(result.stdout.strip())


def _set_origin(repo_dir: Path, config: CommitArtConfig) -> None:
    result = _run_git(repo_dir, ["remote", "get-url", "origin"], config, check=False)
    if result.returncode == 0:
        _run_git(repo_dir, ["remote", "set-url", "origin", config.origin], config)
    else:
        _run_git(repo_dir, ["remote", "add", "origin", config.origin], config)


def _run_git(
    repo_dir: Path,
    args: list[str],
    config: CommitArtConfig,
    extra_env: dict[str, str] | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(
        {
            "GIT_AUTHOR_NAME": config.author_name,
            "GIT_AUTHOR_EMAIL": config.author_email,
            "GIT_COMMITTER_NAME": config.author_name,
            "GIT_COMMITTER_EMAIL": config.author_email,
        }
    )
    if extra_env:
        env.update(extra_env)

    result = subprocess.run(
        ["git", *args],
        cwd=repo_dir,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    if check and result.returncode != 0:
        details = (result.stderr or result.stdout).strip()
        raise GitApplyError(f"git {' '.join(args)} failed: {details}")
    return result


def _append(path: Path, content: str) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as file:
        file.write(content)
