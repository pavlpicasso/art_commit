import unittest
from datetime import date
from pathlib import Path

from commit_art.calendar import first_contribution_day, first_contribution_day_for_year
from commit_art.config import DEFAULT_LEVELS, DEFAULT_MAP, CommitArtConfig, ConfigError, load_config
from commit_art.git_runner import (
    GitApplyError,
    GitPushError,
    _build_push_args,
    _ensure_safe_repo_path,
    _prepare_repo_dir,
    inspect_repo,
    push_repo,
)
from commit_art.generator import generate_plan, summarize_plan
from commit_art.map_parser import CommitMapError, validate_commit_map
from commit_art.preview_renderer import render_visual_map
from commit_art.text_renderer import TextRenderError, format_toml_map, render_text_map


TEST_DIR = Path(__file__).parent


class GeneratorTest(unittest.TestCase):
    def test_first_contribution_day_uses_rolling_year_rule(self) -> None:
        self.assertEqual(first_contribution_day(date(2026, 6, 8)), date(2025, 6, 8))

    def test_first_contribution_day_for_year_uses_january_grid(self) -> None:
        self.assertEqual(first_contribution_day_for_year(2024), date(2023, 12, 31))

    def test_validate_rejects_wrong_row_count(self) -> None:
        with self.assertRaises(CommitMapError):
            validate_commit_map([" " * 52], {"*": 10, "#": 20})

    def test_validate_rejects_wrong_column_count(self) -> None:
        bad_map = [" " * 52 for _ in range(7)]
        bad_map[0] = " " * 51

        with self.assertRaises(CommitMapError):
            validate_commit_map(bad_map, {"*": 10, "#": 20})

    def test_generate_plan_uses_configured_levels(self) -> None:
        commit_map = ["# " + (" " * 50), "* " + (" " * 50)] + [" " * 52 for _ in range(5)]

        plan = generate_plan(commit_map, {"*": 10, "#": 20}, today=date(2026, 6, 8))

        self.assertEqual(
            [(item.day, item.count) for item in plan],
            [
                (date(2025, 6, 8), 20),
                (date(2025, 6, 9), 10),
            ],
        )

    def test_generate_plan_supports_fixed_year(self) -> None:
        commit_map = ["# " + (" " * 50)] + [" " * 52 for _ in range(6)]

        plan = generate_plan(commit_map, {"*": 10, "#": 20}, year=2024)

        self.assertEqual([(item.day, item.count) for item in plan], [(date(2023, 12, 31), 20)])

    def test_generate_plan_rejects_today_and_year_together(self) -> None:
        with self.assertRaises(ValueError):
            generate_plan(DEFAULT_MAP, {"*": 10, "#": 20}, today=date(2026, 6, 8), year=2024)

    def test_default_map_summary_is_stable(self) -> None:
        plan = generate_plan(DEFAULT_MAP, DEFAULT_LEVELS, today=date(2026, 6, 8))

        self.assertEqual(summarize_plan(plan), (98, 1872))

    def test_default_levels_support_four_non_empty_intensities(self) -> None:
        config = CommitArtConfig()

        self.assertEqual(config.levels, {".": 4, ":": 8, "*": 12, "#": 20})

    def test_validate_accepts_all_default_intensity_symbols(self) -> None:
        commit_map = [".:*#" + (" " * 48)] + [" " * 52 for _ in range(6)]

        validate_commit_map(commit_map, DEFAULT_LEVELS)

    def test_load_config_reads_toml_file(self) -> None:
        config = load_config(TEST_DIR / "fixtures" / "custom_config.toml")

        self.assertEqual(config.origin, "https://github.com/example/art.git")
        self.assertEqual(config.branch, "main")
        self.assertEqual(config.repo_dir, Path("out"))
        self.assertEqual(config.commit_file, "art.md")
        self.assertEqual(config.timezone, "+0000")
        self.assertEqual(config.commit_hour, 10)
        self.assertEqual(config.message_prefix, "Art")
        self.assertEqual(config.author_name, "Example User")
        self.assertEqual(config.author_email, "example@example.com")
        self.assertEqual(config.levels, {"#": 3})
        self.assertEqual(config.commit_map[0][0], "#")

    def test_load_config_rejects_invalid_levels(self) -> None:
        with self.assertRaises(ConfigError):
            load_config(TEST_DIR / "fixtures" / "invalid_levels.toml")

    def test_apply_rejects_non_empty_non_git_directory(self) -> None:
        repo_dir = TEST_DIR / "fixtures" / "non_empty_repo"
        config = CommitArtConfig(repo_dir=repo_dir)

        with self.assertRaises(GitApplyError):
            _prepare_repo_dir(config, allow_existing=False)

    def test_config_has_author_defaults(self) -> None:
        config = CommitArtConfig()

        self.assertEqual(config.author_name, "Commit Art")
        self.assertEqual(config.author_email, "commit-art@example.com")

    def test_safe_repo_path_rejects_project_root(self) -> None:
        with self.assertRaises(GitApplyError):
            _ensure_safe_repo_path(Path("."))

    def test_safe_repo_path_rejects_parent_directory(self) -> None:
        with self.assertRaises(GitApplyError):
            _ensure_safe_repo_path(Path(".."))

    def test_inspect_repo_reports_non_empty_non_git_directory(self) -> None:
        status = inspect_repo(CommitArtConfig(repo_dir=TEST_DIR / "fixtures" / "non_empty_repo"))

        self.assertTrue(status.exists)
        self.assertTrue(status.is_dir)
        self.assertFalse(status.is_empty)
        self.assertFalse(status.is_git)

    def test_push_rejects_missing_repo(self) -> None:
        config = CommitArtConfig(repo_dir=Path("missing-test-repo"))

        with self.assertRaises(GitPushError):
            push_repo(config)

    def test_push_rejects_empty_origin(self) -> None:
        config = CommitArtConfig(repo_dir=TEST_DIR / "fixtures" / "non_empty_repo", origin="")

        with self.assertRaises(GitPushError):
            push_repo(config)

    def test_build_push_args_uses_force_with_lease(self) -> None:
        config = CommitArtConfig(branch="main")

        self.assertEqual(_build_push_args(config, force=True, set_upstream=True), ["push", "-u", "origin", "main", "--force-with-lease"])

    def test_build_push_args_can_skip_upstream(self) -> None:
        config = CommitArtConfig(branch="main")

        self.assertEqual(_build_push_args(config, force=False, set_upstream=False), ["push", "origin", "main"])

    def test_render_text_map_returns_7_by_52_map(self) -> None:
        commit_map = render_text_map("HI", level="#")

        self.assertEqual(len(commit_map), 7)
        self.assertTrue(all(len(row) == 52 for row in commit_map))
        self.assertTrue(any("#" in row for row in commit_map))

    def test_render_text_map_supports_alignment_and_level(self) -> None:
        commit_map = render_text_map("A", level=".", align="left")

        self.assertEqual(commit_map[0], " ... " + (" " * 47))
        self.assertTrue(all("#" not in row for row in commit_map))

    def test_render_text_map_rejects_unknown_character(self) -> None:
        with self.assertRaises(TextRenderError):
            render_text_map("@")

    def test_render_text_map_rejects_too_wide_text(self) -> None:
        with self.assertRaises(TextRenderError):
            render_text_map("ABCDEFGHIJK")

    def test_format_toml_map_outputs_config_snippet(self) -> None:
        commit_map = render_text_map("A", level="#", align="left")

        self.assertTrue(format_toml_map(commit_map).startswith("map = ["))

    def test_render_visual_map_outputs_weekday_rows(self) -> None:
        commit_map = ["# " + (" " * 50)] + [" " * 52 for _ in range(6)]

        rendered = render_visual_map(commit_map, DEFAULT_LEVELS, color=False)

        self.assertIn("Sun ##", rendered)
        self.assertIn("Mon", rendered)
        self.assertIn("Less", rendered)
        self.assertIn("More", rendered)

    def test_render_visual_map_can_use_ansi_colors(self) -> None:
        commit_map = ["# " + (" " * 50)] + [" " * 52 for _ in range(6)]

        rendered = render_visual_map(commit_map, DEFAULT_LEVELS, color=True)

        self.assertIn("\033[", rendered)


if __name__ == "__main__":
    unittest.main()
