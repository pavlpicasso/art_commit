import unittest

from commit_art.text_renderer import TextRenderError, format_toml_map, render_text_map


class TextRendererTest(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
