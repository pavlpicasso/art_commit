import shutil
import stat
import unittest
from pathlib import Path

from commit_art.config import CommitArtConfig
from commit_art.git_runner import (
    GitApplyError,
    GitPushError,
    _build_chunk_push_args,
    _build_push_args,
    _chunk_end_indexes,
    _ensure_safe_repo_path,
    _prepare_repo_dir,
    inspect_repo,
    push_repo,
)


TEST_DIR = Path(__file__).parent


class GitRunnerTest(unittest.TestCase):
    def test_apply_rejects_non_empty_non_git_directory(self) -> None:
        repo_dir = TEST_DIR / "fixtures" / "non_empty_repo"
        config = CommitArtConfig(repo_dir=repo_dir)

        with self.assertRaises(GitApplyError):
            _prepare_repo_dir(config, allow_existing=False)

    def test_reset_repo_removes_readonly_git_objects(self) -> None:
        repo_dir = TEST_DIR / "tmp_readonly_reset_repo"
        object_dir = repo_dir / ".git" / "objects" / "00"
        object_file = object_dir / "readonly-object"

        if repo_dir.exists():
            shutil.rmtree(repo_dir)
        object_dir.mkdir(parents=True)
        object_file.write_text("object", encoding="utf-8")
        object_file.chmod(stat.S_IREAD)

        try:
            _prepare_repo_dir(CommitArtConfig(repo_dir=repo_dir), allow_existing=False, reset_repo=True)
            self.assertTrue(repo_dir.exists())
            self.assertEqual(list(repo_dir.iterdir()), [])
        finally:
            if object_file.exists():
                object_file.chmod(stat.S_IREAD | stat.S_IWRITE)
            if repo_dir.exists():
                shutil.rmtree(repo_dir)

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

        self.assertEqual(
            _build_push_args(config, force=True, set_upstream=True),
            ["push", "-u", "origin", "main", "--force-with-lease"],
        )

    def test_build_push_args_can_skip_upstream(self) -> None:
        config = CommitArtConfig(branch="main")

        self.assertEqual(_build_push_args(config, force=False, set_upstream=False), ["push", "origin", "main"])

    def test_build_chunk_push_args_force_pushes_commit_to_branch(self) -> None:
        config = CommitArtConfig(branch="master")

        self.assertEqual(
            _build_chunk_push_args(config, "abc123", set_upstream=True),
            ["push", "-u", "origin", "abc123:refs/heads/master", "--force"],
        )

    def test_chunk_end_indexes_include_final_commit(self) -> None:
        self.assertEqual(_chunk_end_indexes(1460, 500), [499, 999, 1459])
        self.assertEqual(_chunk_end_indexes(1500, 500), [499, 999, 1499])
        self.assertEqual(_chunk_end_indexes(1, 500), [0])


if __name__ == "__main__":
    unittest.main()
