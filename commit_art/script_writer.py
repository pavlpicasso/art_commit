from __future__ import annotations

from pathlib import Path

from commit_art.config import CommitArtConfig
from commit_art.generator import PlannedCommitDay


def build_bash_script(config: CommitArtConfig, plan: list[PlannedCommitDay]) -> str:
    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "",
        "git init",
        f'git checkout -B "{config.branch}"',
        f'printf "# Commit Art\\n" > "{config.commit_file}"',
        "",
    ]

    for item in plan:
        lines.append(f'printf "\\n## {item.day.isoformat()}\\n" >> "{config.commit_file}"')
        for index in range(item.count):
            minute = f"{index:02d}"
            message = f"{config.message_prefix} #{index + 1}"
            commit_date = f"{item.day.isoformat()}T{config.commit_hour:02d}:{minute}:00{config.timezone}"
            lines.extend(
                [
                    f'printf "* {message}\\n" >> "{config.commit_file}"',
                    f'git add "{config.commit_file}"',
                    f'git commit -m "{message}" --date="{commit_date}"',
                    "",
                ]
            )

    lines.extend(
        [
            f'git remote add origin "{config.origin}" || git remote set-url origin "{config.origin}"',
            f'echo "Generated {sum(item.count for item in plan)} commits. Run git push -u origin {config.branch} --force explicitly if this is intentional."',
            "",
        ]
    )
    return "\n".join(lines)


def build_powershell_script(config: CommitArtConfig, plan: list[PlannedCommitDay]) -> str:
    lines = [
        "$ErrorActionPreference = 'Stop'",
        "",
        "git init",
        f'git checkout -B "{config.branch}"',
        f'Set-Content -Path "{config.commit_file}" -Value "# Commit Art"',
        "",
    ]

    for item in plan:
        lines.append(f'Add-Content -Path "{config.commit_file}" -Value ""')
        lines.append(f'Add-Content -Path "{config.commit_file}" -Value "## {item.day.isoformat()}"')
        for index in range(item.count):
            minute = f"{index:02d}"
            message = f"{config.message_prefix} #{index + 1}"
            commit_date = f"{item.day.isoformat()}T{config.commit_hour:02d}:{minute}:00{config.timezone}"
            lines.extend(
                [
                    f'Add-Content -Path "{config.commit_file}" -Value "* {message}"',
                    f'git add "{config.commit_file}"',
                    f'git commit -m "{message}" --date="{commit_date}"',
                    "",
                ]
            )

    lines.extend(
        [
            f'git remote add origin "{config.origin}"; if ($LASTEXITCODE -ne 0) {{ git remote set-url origin "{config.origin}" }}',
            f'Write-Host "Generated {sum(item.count for item in plan)} commits. Run git push -u origin {config.branch} --force explicitly if this is intentional."',
            "",
        ]
    )
    return "\n".join(lines)


def write_script(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")
