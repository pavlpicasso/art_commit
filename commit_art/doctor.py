from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import date

from commit_art.config import CommitArtConfig
from commit_art.generator import generate_plan, summarize_plan
from commit_art.git_runner import GitApplyError, _ensure_safe_repo_path, _run_git, inspect_repo
from commit_art.map_parser import CommitMapError, validate_commit_map


@dataclass(frozen=True)
class DoctorCheck:
    status: str
    name: str
    message: str


def run_doctor(config: CommitArtConfig, today: date | None = None, year: int | None = None) -> list[DoctorCheck]:
    checks: list[DoctorCheck] = []

    checks.append(_check_executable("git", required=True))
    checks.append(_check_executable("gh", required=False))
    checks.extend(_check_author_email(config))
    checks.extend(_check_origin_config(config))
    checks.extend(_check_map(config, today=today, year=year))
    checks.extend(_check_repo(config))
    checks.append(
        DoctorCheck(
            "WARN",
            "GitHub profile settings",
            "Private repository contributions require GitHub profile setting 'Include private contributions' to be enabled.",
        )
    )

    return checks


def has_errors(checks: list[DoctorCheck]) -> bool:
    return any(check.status == "ERROR" for check in checks)


def format_doctor_checks(checks: list[DoctorCheck]) -> str:
    return "\n".join(f"[{check.status}] {check.name}: {check.message}" for check in checks)


def _check_executable(name: str, required: bool) -> DoctorCheck:
    path = shutil.which(name)
    if path:
        return DoctorCheck("OK", f"{name} executable", path)
    if required:
        return DoctorCheck("ERROR", f"{name} executable", f"{name!r} is required but was not found in PATH.")
    return DoctorCheck("WARN", f"{name} executable", f"{name!r} was not found in PATH. GitHub repo creation helper will not work.")


def _check_author_email(config: CommitArtConfig) -> list[DoctorCheck]:
    if "@" not in config.author_email:
        return [DoctorCheck("ERROR", "Author email", "author_email must be an email address.")]

    checks = [
        DoctorCheck(
            "OK",
            "Author email",
            "author_email is configured. It must match a verified email on the target GitHub account.",
        )
    ]
    if config.author_email.endswith("@example.com"):
        checks.append(
            DoctorCheck(
                "WARN",
                "Author email placeholder",
                "Replace the example author_email with a verified GitHub email or GitHub noreply address.",
            )
        )
    return checks


def _check_origin_config(config: CommitArtConfig) -> list[DoctorCheck]:
    if not config.origin:
        return [DoctorCheck("ERROR", "Origin config", "origin is empty.")]

    checks = [DoctorCheck("OK", "Origin config", config.origin)]
    if "your-name" in config.origin or "example" in config.origin:
        checks.append(DoctorCheck("WARN", "Origin placeholder", "Replace origin with the real GitHub repository URL."))
    if "github.com" not in config.origin and not config.origin.endswith(".git"):
        checks.append(DoctorCheck("WARN", "Origin shape", "origin does not look like a GitHub URL or git remote path."))
    return checks


def _check_map(config: CommitArtConfig, today: date | None, year: int | None) -> list[DoctorCheck]:
    try:
        validate_commit_map(config.commit_map, config.levels)
        plan = generate_plan(config.commit_map, config.levels, today=today, year=year)
    except (CommitMapError, ValueError) as error:
        return [DoctorCheck("ERROR", "Contribution map", str(error))]

    active_days, total_commits = summarize_plan(plan)
    if total_commits == 0:
        return [DoctorCheck("WARN", "Contribution map", "Map is valid but produces no commits.")]
    return [DoctorCheck("OK", "Contribution map", f"{active_days} active days, {total_commits} commits.")]


def _check_repo(config: CommitArtConfig) -> list[DoctorCheck]:
    checks: list[DoctorCheck] = []
    try:
        _ensure_safe_repo_path(config.repo_dir)
    except GitApplyError as error:
        return [DoctorCheck("ERROR", "repo_dir safety", str(error))]

    checks.append(DoctorCheck("OK", "repo_dir safety", f"{config.repo_dir} stays inside the workspace."))
    status = inspect_repo(config)

    if not status.exists:
        checks.append(DoctorCheck("WARN", "repo_dir", f"{config.repo_dir} does not exist yet. Run apply first."))
        return checks
    if not status.is_dir:
        checks.append(DoctorCheck("ERROR", "repo_dir", f"{config.repo_dir} is not a directory."))
        return checks
    if not status.is_git:
        if status.is_empty:
            checks.append(DoctorCheck("WARN", "Git repository", f"{config.repo_dir} is empty. Run apply to initialize it."))
        else:
            checks.append(DoctorCheck("ERROR", "Git repository", f"{config.repo_dir} is not a git repository."))
        return checks

    checks.append(DoctorCheck("OK", "Git repository", f"{config.repo_dir} is initialized."))
    if status.is_dirty:
        checks.append(DoctorCheck("WARN", "Working tree", "Repository has uncommitted changes."))
    else:
        checks.append(DoctorCheck("OK", "Working tree", "Repository is clean."))

    if status.branch == config.branch:
        checks.append(DoctorCheck("OK", "Branch", f"Current branch matches config: {config.branch}."))
    else:
        checks.append(DoctorCheck("WARN", "Branch", f"Current branch is {status.branch or '-'}, config branch is {config.branch}."))

    if config.branch != "gh-pages":
        checks.append(
            DoctorCheck(
                "WARN",
                "GitHub contribution branch",
                "GitHub counts commits on the repository default branch or gh-pages. Ensure this branch is the default branch.",
            )
        )

    if status.origin == config.origin:
        checks.append(DoctorCheck("OK", "Remote origin", "Repository origin matches config."))
    else:
        checks.append(DoctorCheck("WARN", "Remote origin", f"Repo origin is {status.origin or '-'}, config origin is {config.origin}."))

    commit_count = _commit_count(config)
    if commit_count is None:
        checks.append(DoctorCheck("WARN", "Commit count", "Could not read commit count."))
    elif commit_count == 0:
        checks.append(DoctorCheck("WARN", "Commit count", "Repository has no commits. Run apply first."))
    else:
        checks.append(DoctorCheck("OK", "Commit count", f"Repository has {commit_count} commits."))

    return checks


def _commit_count(config: CommitArtConfig) -> int | None:
    result = _run_git(config.repo_dir, ["rev-list", "--count", "HEAD"], config, check=False)
    if result.returncode != 0:
        return None
    try:
        return int(result.stdout.strip())
    except ValueError:
        return None
