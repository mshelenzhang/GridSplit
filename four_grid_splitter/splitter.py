"""Core implementation for deterministic grid image splitting."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError


OUTPUT_NAMES = {
    (1, 2): ("01_left", "02_right"),
    (2, 1): ("01_top", "02_bottom"),
    (2, 2): (
        "01_top_left",
        "02_top_right",
        "03_bottom_left",
        "04_bottom_right",
    ),
}


class SplitGridError(RuntimeError):
    """Raised when an image cannot be split according to the module contract."""


def _write_manifest(output_dir: Path, manifest: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "manifest.json"
    temporary_path = output_dir / ".manifest.json.tmp"
    temporary_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(path)


def split_grid(
    input_path: str | Path,
    output_dir: str | Path,
    grid_rows: int = 2,
    grid_cols: int = 2,
) -> dict[str, Any]:
    """Split one supported grid image and return its machine-readable manifest.

    Crops are saved as PNG files so decoded source pixels are not resampled or
    subjected to additional lossy compression. For odd dimensions, the extra
    pixel is assigned deterministically to the right column and/or bottom row.
    """
    source = Path(input_path).expanduser().resolve()
    destination = Path(output_dir).expanduser().resolve()
    manifest: dict[str, Any] = {
        "success": False,
        "input_path": str(source),
        "output_dir": str(destination),
        "grid_rows": grid_rows,
        "grid_cols": grid_cols,
        "source_size": None,
        "outputs": [],
        "error": None,
    }

    try:
        layout = (grid_rows, grid_cols)
        if layout not in OUTPUT_NAMES:
            raise SplitGridError(
                "This version supports only 1x2 horizontal, 2x1 vertical, and 2x2 grid layouts."
            )
        if not source.is_file():
            raise SplitGridError(f"Input image does not exist or is not a file: {source}")

        destination.mkdir(parents=True, exist_ok=True)
        with Image.open(source) as image:
            image.load()
            width, height = image.size
            if width < grid_cols or height < grid_rows:
                raise SplitGridError(
                    f"Image size {width}x{height} is smaller than the requested "
                    f"{grid_cols}x{grid_rows} grid."
                )

            x_edges = [(index * width) // grid_cols for index in range(grid_cols + 1)]
            y_edges = [(index * height) // grid_rows for index in range(grid_rows + 1)]
            positions = tuple(
                (col, row)
                for row in range(grid_rows)
                for col in range(grid_cols)
            )
            manifest["source_size"] = {"width": width, "height": height}

            for order, (name, (col, row)) in enumerate(
                zip(OUTPUT_NAMES[layout], positions), start=1
            ):
                box = (
                    x_edges[col],
                    y_edges[row],
                    x_edges[col + 1],
                    y_edges[row + 1],
                )
                output_path = destination / f"{name}.png"
                crop = image.crop(box)
                crop.save(output_path, format="PNG", optimize=False)
                manifest["outputs"].append(
                    {
                        "order": order,
                        "name": name,
                        "path": str(output_path),
                        "size": {"width": crop.width, "height": crop.height},
                        "box": {
                            "left": box[0],
                            "top": box[1],
                            "right": box[2],
                            "bottom": box[3],
                        },
                    }
                )

        manifest["success"] = True
        _write_manifest(destination, manifest)
        return manifest
    except (OSError, ValueError, UnidentifiedImageError, SplitGridError) as exc:
        manifest["error"] = str(exc)
        try:
            _write_manifest(destination, manifest)
        except OSError:
            pass
        if isinstance(exc, SplitGridError):
            raise
        raise SplitGridError(str(exc)) from exc
