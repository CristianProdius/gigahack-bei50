#!/usr/bin/env python3
"""Convert the official (not scored) Sireț3 example CVAT into YOLO-seg chips."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "processing" / "src"))

from siret3.example_yolo import write_example_yolo  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--zip", default="data/challenge/05_examples/siret3_examples_cvat.zip")
    p.add_argument("--tiles", default="data/tiles")
    p.add_argument("--out", default="datasets/siret3-examples-yolo")
    args = p.parse_args()
    stats = write_example_yolo(Path(args.zip), Path(args.tiles), Path(args.out))
    print(f"wrote {stats['chips']} chips / {stats['plant_instances']} plants from {stats['tiles']} tiles -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
