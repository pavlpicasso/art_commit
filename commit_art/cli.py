from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from commit_art.config import ConfigError, load_config
from commit_art.git_runner import GitApplyError, GitPushError, apply_plan, inspect_repo, push_repo
from commit_art.generator import generate_plan, summarize_plan
from commit_art.map_parser import CommitMapError, validate_commit_map
from commit_art.preview_renderer import render_visual_map
from commit_art.script_writer import build_bash_script, build_powershell_script, write_script
from commit_art.text_renderer import TextRenderError, format_toml_map, render_text_map


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate dated commits for GitHub contribution art.")
    parser.add_argument("--config", type=Path, default=Path("config.toml"), help="Path to the TOML config file.")
    parser.add_argument("--today", help="Use a fixed current date in YYYY-MM-DD format.")
    parser.add_argument("--year", type=int, help="Draw commits for the 52-week grid containing January 1 of this year.")

    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate", help="Validate the configured 7x52 contribution map.")
    validate.add_argument("--today", default=argparse.SUPPRESS, help="Use a fixed current date in YYYY-MM-DD format.")
    validate.add_argument(
        "--year",
        type=int,
        default=argparse.SUPPRESS,
        help="Draw commits for the 52-week grid containing January 1 of this year.",
    )

    preview = subparsers.add_parser("preview", help="Print planned commit dates and counts.")
    preview.add_argument("--today", default=argparse.SUPPRESS, help="Use a fixed current date in YYYY-MM-DD format.")
    preview.add_argument(
        "--year",
        type=int,
        default=argparse.SUPPRESS,
        help="Draw commits for the 52-week grid containing January 1 of this year.",
    )
    preview.add_argument("--limit", type=int, default=20, help="How many planned days to print.")
    preview.add_argument("--visual", action="store_true", help="Render the 7x52 contribution map.")
    preview.add_argument("--no-color", action="store_true", help="Render visual preview without ANSI colors.")

    script = subparsers.add_parser("generate-script", help="Write a script that creates the dated commits.")
    script.add_argument("--today", default=argparse.SUPPRESS, help="Use a fixed current date in YYYY-MM-DD format.")
    script.add_argument(
        "--year",
        type=int,
        default=argparse.SUPPRESS,
        help="Draw commits for the 52-week grid containing January 1 of this year.",
    )
    script.add_argument("--shell", choices=("bash", "powershell"), default="powershell")
    script.add_argument("--output", type=Path, help="Where to write the generated script.")

    subparsers.add_parser("repo-status", help="Inspect the configured repo_dir before applying commits.")

    apply = subparsers.add_parser("apply", help="Create the dated commits directly with git.")
    apply.add_argument("--today", default=argparse.SUPPRESS, help="Use a fixed current date in YYYY-MM-DD format.")
    apply.add_argument(
        "--year",
        type=int,
        default=argparse.SUPPRESS,
        help="Draw commits for the 52-week grid containing January 1 of this year.",
    )
    apply.add_argument(
        "--allow-existing",
        action="store_true",
        help="Allow applying commits inside an existing git repository in repo_dir.",
    )
    apply.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Allow applying commits inside an existing repository with uncommitted changes.",
    )
    apply.add_argument(
        "--reset-repo",
        action="store_true",
        help="Delete and recreate repo_dir before applying commits.",
    )

    push = subparsers.add_parser("push", help="Push repo_dir to the configured origin.")
    push.add_argument("--force", action="store_true", help="Use --force-with-lease when pushing.")
    push.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Allow pushing when repo_dir has uncommitted changes.",
    )
    push.add_argument(
        "--no-set-upstream",
        action="store_true",
        help="Do not pass -u/--set-upstream to git push.",
    )

    text = subparsers.add_parser("text", help="Render text as a 7x52 contribution map.")
    text.add_argument("text", help="Text to render. Supported: A-Z, 0-9, space, - _ ! ? .")
    text.add_argument("--level", default="#", help="Configured intensity symbol to use for filled pixels.")
    text.add_argument("--letter-spacing", type=int, default=1, help="Blank columns between characters.")
    text.add_argument("--align", choices=("left", "center", "right"), default="center")

    return parser


def parse_today(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def parse_year(value: int | None) -> int | None:
    if value is None:
        return None
    if value < 1970 or value > 9999:
        raise ValueError("Year must be between 1970 and 9999.")
    return value


def print_map(commit_map: list[str]) -> None:
    for row in commit_map:
        print(f"{row}|")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
        today = parse_today(getattr(args, "today", None))
        year = parse_year(getattr(args, "year", None))
        validate_commit_map(config.commit_map, config.levels)
        plan = generate_plan(config.commit_map, config.levels, today=today, year=year)
    except (CommitMapError, ConfigError, ValueError) as error:
        print(f"Error: {error}")
        return 1

    if args.command == "validate":
        active_days, total_commits = summarize_plan(plan)
        print("Commit map is valid:")
        print_map(config.commit_map)
        print(f"Active days: {active_days}")
        print(f"Total commits: {total_commits}")
        return 0

    if args.command == "preview":
        active_days, total_commits = summarize_plan(plan)
        print(f"Active days: {active_days}")
        print(f"Total commits: {total_commits}")
        if args.visual:
            print("")
            print(render_visual_map(config.commit_map, config.levels, color=not args.no_color))
            return 0

        print("")
        for item in plan[: args.limit]:
            print(f"{item.day.isoformat()}: {item.count}")
        if len(plan) > args.limit:
            print(f"... {len(plan) - args.limit} more active days")
        return 0

    if args.command == "generate-script":
        content = build_bash_script(config, plan) if args.shell == "bash" else build_powershell_script(config, plan)
        output = args.output or config.repo_dir / ("make-commits.sh" if args.shell == "bash" else "make-commits.ps1")
        write_script(output, content)
        print(f"Wrote {args.shell} script: {output}")
        print("The script creates local commits only. Push with --force manually after reviewing the target repository.")
        return 0

    if args.command == "repo-status":
        status = inspect_repo(config)
        print(f"Path: {status.path}")
        print(f"Exists: {status.exists}")
        print(f"Directory: {status.is_dir}")
        print(f"Empty: {status.is_empty}")
        print(f"Git repository: {status.is_git}")
        print(f"Dirty: {status.is_dirty}")
        print(f"Branch: {status.branch or '-'}")
        print(f"Origin: {status.origin or '-'}")
        return 0

    if args.command == "apply":
        try:
            total_commits = apply_plan(
                config,
                plan,
                allow_existing=args.allow_existing,
                reset_repo=args.reset_repo,
                allow_dirty=args.allow_dirty,
            )
        except GitApplyError as error:
            print(f"Error: {error}")
            return 1

        print(f"Created {total_commits} commits in {config.repo_dir}")
        print("No push was performed. Review the repository before pushing.")
        return 0

    if args.command == "push":
        try:
            output = push_repo(
                config,
                force=args.force,
                allow_dirty=args.allow_dirty,
                set_upstream=not args.no_set_upstream,
            )
        except GitPushError as error:
            print(f"Error: {error}")
            return 1

        print(f"Pushed {config.branch} to {config.origin}")
        if output:
            print(output)
        return 0

    if args.command == "text":
        if args.level not in config.levels:
            print(f"Error: level {args.level!r} is not configured in [levels].")
            return 1
        try:
            commit_map = render_text_map(
                args.text,
                level=args.level,
                letter_spacing=args.letter_spacing,
                align=args.align,
            )
            validate_commit_map(commit_map, config.levels)
        except (TextRenderError, CommitMapError) as error:
            print(f"Error: {error}")
            return 1

        print(format_toml_map(commit_map))
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2
