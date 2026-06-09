import unittest
from datetime import date

from commit_art.calendar import first_contribution_day, first_contribution_day_for_year


class CalendarTest(unittest.TestCase):
    def test_first_contribution_day_uses_rolling_year_rule(self) -> None:
        self.assertEqual(first_contribution_day(date(2026, 6, 8)), date(2025, 6, 8))

    def test_first_contribution_day_for_year_uses_january_grid(self) -> None:
        self.assertEqual(first_contribution_day_for_year(2024), date(2023, 12, 31))


if __name__ == "__main__":
    unittest.main()
