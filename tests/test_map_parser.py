import unittest

from commit_art.config import DEFAULT_LEVELS
from commit_art.map_parser import CommitMapError, validate_commit_map


class MapParserTest(unittest.TestCase):
    def test_validate_rejects_wrong_row_count(self) -> None:
        with self.assertRaises(CommitMapError):
            validate_commit_map([" " * 52], {"*": 10, "#": 20})

    def test_validate_rejects_wrong_column_count(self) -> None:
        bad_map = [" " * 52 for _ in range(7)]
        bad_map[0] = " " * 51

        with self.assertRaises(CommitMapError):
            validate_commit_map(bad_map, {"*": 10, "#": 20})

    def test_validate_accepts_all_default_intensity_symbols(self) -> None:
        commit_map = [".:*#" + (" " * 48)] + [" " * 52 for _ in range(6)]

        validate_commit_map(commit_map, DEFAULT_LEVELS)


if __name__ == "__main__":
    unittest.main()
