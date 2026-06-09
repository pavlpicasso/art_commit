import unittest
from pathlib import Path

from commit_art.config import CommitArtConfig
from commit_art.doctor import format_doctor_checks, has_errors, run_doctor


class DoctorTest(unittest.TestCase):
    def test_doctor_reports_placeholder_email_and_origin_warnings(self) -> None:
        checks = run_doctor(CommitArtConfig(repo_dir=Path("missing-doctor-repo")), year=2024)
        names = [check.name for check in checks]

        self.assertIn("Author email placeholder", names)
        self.assertIn("Origin placeholder", names)
        self.assertIn("repo_dir", names)

    def test_doctor_reports_errors_for_bad_repo_path(self) -> None:
        checks = run_doctor(CommitArtConfig(repo_dir=Path(".")), year=2024)

        self.assertTrue(has_errors(checks))
        self.assertIn("repo_dir safety", [check.name for check in checks])

    def test_doctor_reports_map_error(self) -> None:
        checks = run_doctor(CommitArtConfig(commit_map=[" " * 52]), year=2024)

        self.assertTrue(has_errors(checks))
        self.assertIn("Contribution map", [check.name for check in checks])

    def test_format_doctor_checks_outputs_status_lines(self) -> None:
        checks = run_doctor(CommitArtConfig(repo_dir=Path("missing-doctor-repo")), year=2024)

        self.assertIn("[", format_doctor_checks(checks))


if __name__ == "__main__":
    unittest.main()
