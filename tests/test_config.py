import unittest
from pathlib import Path

from commit_art.config import CommitArtConfig, ConfigError, load_config


TEST_DIR = Path(__file__).parent


class ConfigTest(unittest.TestCase):
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

    def test_config_has_author_defaults(self) -> None:
        config = CommitArtConfig()

        self.assertEqual(config.author_name, "Commit Art")
        self.assertEqual(config.author_email, "commit-art@example.com")

    def test_default_levels_support_four_non_empty_intensities(self) -> None:
        config = CommitArtConfig()

        self.assertEqual(config.levels, {".": 4, ":": 8, "*": 12, "#": 20})


if __name__ == "__main__":
    unittest.main()
