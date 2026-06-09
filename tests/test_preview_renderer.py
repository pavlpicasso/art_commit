import unittest

from commit_art.config import DEFAULT_LEVELS
from commit_art.preview_renderer import render_visual_map


class PreviewRendererTest(unittest.TestCase):
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
