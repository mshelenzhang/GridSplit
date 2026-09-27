from __future__ import annotations

import json
import hashlib
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from four_grid_splitter import SplitGridError, split_grid


class SplitGridTests(unittest.TestCase):
    def _source(self, directory: Path, size: tuple[int, int], suffix: str) -> Path:
        image = Image.new("RGB", size)
        pixels = image.load()
        for y in range(size[1]):
            for x in range(size[0]):
                pixels[x, y] = (x % 256, y % 256, (x * 17 + y * 31) % 256)
        path = directory / f"source{suffix}"
        save_options = {"quality": 95, "subsampling": 0} if suffix == ".jpg" else {}
        image.save(path, **save_options)
        return path

    def _assert_pixel_preserving_split(self, suffix: str, size: tuple[int, int]) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self._source(root, size, suffix)
            output = root / "out"
            manifest = split_grid(source, output)

            self.assertTrue(manifest["success"])
            self.assertEqual([item["name"] for item in manifest["outputs"]], [
                "01_top_left", "02_top_right", "03_bottom_left", "04_bottom_right"
            ])
            self.assertEqual(manifest["source_size"], {"width": size[0], "height": size[1]})
            self.assertEqual(
                json.loads((output / "manifest.json").read_text(encoding="utf-8")),
                manifest,
            )

            with Image.open(source) as decoded_source:
                for item in manifest["outputs"]:
                    box_data = item["box"]
                    box = tuple(box_data[key] for key in ("left", "top", "right", "bottom"))
                    expected = decoded_source.crop(box)
                    with Image.open(item["path"]) as actual:
                        self.assertEqual(actual.size, expected.size)
                        self.assertEqual(actual.tobytes(), expected.tobytes())

            total_area = sum(
                item["size"]["width"] * item["size"]["height"]
                for item in manifest["outputs"]
            )
            self.assertEqual(total_area, size[0] * size[1])

    def test_even_png(self) -> None:
        self._assert_pixel_preserving_split(".png", (8, 6))

    def test_odd_png(self) -> None:
        self._assert_pixel_preserving_split(".png", (7, 5))

    def test_even_jpg(self) -> None:
        self._assert_pixel_preserving_split(".jpg", (8, 6))

    def test_odd_jpg(self) -> None:
        self._assert_pixel_preserving_split(".jpg", (7, 5))

    def test_horizontal_two_panel(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self._source(root, (7, 5), ".png")
            manifest = split_grid(source, root / "out", grid_rows=1, grid_cols=2)
            self.assertEqual(
                [item["name"] for item in manifest["outputs"]],
                ["01_left", "02_right"],
            )
            self.assertEqual(
                [item["size"] for item in manifest["outputs"]],
                [{"width": 3, "height": 5}, {"width": 4, "height": 5}],
            )

    def test_vertical_two_panel(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self._source(root, (7, 5), ".jpg")
            manifest = split_grid(source, root / "out", grid_rows=2, grid_cols=1)
            self.assertEqual(
                [item["name"] for item in manifest["outputs"]],
                ["01_top", "02_bottom"],
            )
            self.assertEqual(
                [item["size"] for item in manifest["outputs"]],
                [{"width": 7, "height": 2}, {"width": 7, "height": 3}],
            )

    def test_repeated_runs_are_byte_identical(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self._source(root, (7, 5), ".png")
            first = split_grid(source, root / "first")
            second = split_grid(source, root / "second")

            first_hashes = [
                hashlib.sha256(Path(item["path"]).read_bytes()).hexdigest()
                for item in first["outputs"]
            ]
            second_hashes = [
                hashlib.sha256(Path(item["path"]).read_bytes()).hexdigest()
                for item in second["outputs"]
            ]
            self.assertEqual(first_hashes, second_hashes)

    def test_rejects_other_grid_sizes_and_writes_failure_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self._source(root, (8, 6), ".png")
            output = root / "out"
            with self.assertRaises(SplitGridError):
                split_grid(source, output, grid_rows=3, grid_cols=3)
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            self.assertFalse(manifest["success"])
            self.assertTrue(manifest["error"])


if __name__ == "__main__":
    unittest.main()
