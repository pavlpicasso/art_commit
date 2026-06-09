import unittest

from commit_art.config import DEFAULT_LEVELS
from commit_art.image_renderer import ImageRenderError, image_to_map


class ImageRendererTest(unittest.TestCase):
    def test_image_to_map_returns_7_by_52_map(self) -> None:
        from PIL import Image

        image = Image.new("L", (52, 7), 255)
        image.putpixel((0, 0), 0)

        commit_map = image_to_map(image, DEFAULT_LEVELS, mode="stretch")

        self.assertEqual(len(commit_map), 7)
        self.assertTrue(all(len(row) == 52 for row in commit_map))
        self.assertEqual(commit_map[0][0], "#")
        self.assertEqual(commit_map[0][1], " ")

    def test_image_to_map_invert_uses_bright_pixels(self) -> None:
        from PIL import Image

        image = Image.new("L", (52, 7), 0)
        image.putpixel((0, 0), 255)

        commit_map = image_to_map(image, DEFAULT_LEVELS, mode="stretch", invert=True)

        self.assertEqual(commit_map[0][0], "#")
        self.assertEqual(commit_map[0][1], " ")

    def test_image_to_map_rejects_invalid_mode(self) -> None:
        from PIL import Image

        with self.assertRaises(ImageRenderError):
            image_to_map(Image.new("L", (1, 1), 255), DEFAULT_LEVELS, mode="tile")

    def test_image_to_map_supports_contain_and_cover(self) -> None:
        from PIL import Image

        image = Image.new("L", (10, 10), 0)

        contain_map = image_to_map(image, DEFAULT_LEVELS, mode="contain")
        cover_map = image_to_map(image, DEFAULT_LEVELS, mode="cover")

        self.assertEqual(len(contain_map), 7)
        self.assertEqual(len(cover_map), 7)


if __name__ == "__main__":
    unittest.main()
