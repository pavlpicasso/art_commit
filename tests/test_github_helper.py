import unittest
from pathlib import Path

from commit_art.github_helper import GitHubCreateError, _build_github_create_args


class GitHubHelperTest(unittest.TestCase):
    def test_build_github_create_args_uses_private_source_by_default_shape(self) -> None:
        self.assertEqual(
            _build_github_create_args(
                name="owner/commit-art",
                visibility="private",
                description="Contribution art",
                source=Path("repo"),
                remote="origin",
                push=True,
            ),
            [
                "repo",
                "create",
                "owner/commit-art",
                "--private",
                "--description",
                "Contribution art",
                "--source",
                "repo",
                "--remote",
                "origin",
                "--push",
            ],
        )

    def test_build_github_create_args_supports_remote_only_creation(self) -> None:
        self.assertEqual(
            _build_github_create_args(name="commit-art", visibility="public"),
            ["repo", "create", "commit-art", "--public"],
        )

    def test_build_github_create_args_rejects_invalid_visibility(self) -> None:
        with self.assertRaises(GitHubCreateError):
            _build_github_create_args(name="commit-art", visibility="secret")

    def test_build_github_create_args_rejects_push_without_source(self) -> None:
        with self.assertRaises(GitHubCreateError):
            _build_github_create_args(name="commit-art", visibility="private", push=True)


if __name__ == "__main__":
    unittest.main()
