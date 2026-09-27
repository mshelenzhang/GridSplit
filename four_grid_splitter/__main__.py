"""Command-line entry point for four_grid_splitter."""

from __future__ import annotations

import argparse
import json
import sys

from .splitter import SplitGridError, split_grid


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Split horizontal 2-panel, vertical 2-panel, or 2x2 grid images into separate PNG files without resizing."
    )
    parser.add_argument("--input-path", required=True, help="Path to the input image")
    parser.add_argument("--output-dir", required=True, help="Directory for output files")
    parser.add_argument("--grid-rows", type=int, default=2, help="Number of grid rows (default: 2)")
    parser.add_argument("--grid-cols", type=int, default=2, help="Number of grid columns (default: 2)")
    args = parser.parse_args()

    try:
        manifest = split_grid(
            input_path=args.input_path,
            output_dir=args.output_dir,
            grid_rows=args.grid_rows,
            grid_cols=args.grid_cols,
        )
    except SplitGridError as exc:
        print(json.dumps({"success": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1

    print(json.dumps(manifest, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
