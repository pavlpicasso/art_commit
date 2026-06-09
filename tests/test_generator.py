import unittest
from datetime import date

from commit_art.config import DEFAULT_LEVELS, DEFAULT_MAP
from commit_art.generator import generate_plan, summarize_plan


class GeneratorTest(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
