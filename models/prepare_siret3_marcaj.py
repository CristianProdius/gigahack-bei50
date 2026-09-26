#!/usr/bin/env python3
"""Marcaj CVAT export + official examples → YOLO-seg plant chips."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "processing" / "src"))

from siret3.example_yolo import write_plant_yolo  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--marcaj-zip", required=True)
    p.add_argument("--examples-zip", default="data/challenge/05_examples/siret3_examples_cvat.zip")
    p.add_argument("--tiles", default="data/tiles")
    p.add_argument("--out", default="datasets/siret3-marcaj-yolo")
    args = p.parse_args()
    zips = [Path(args.marcaj_zip)]
    examples = Path(args.examples_zip)
    if examples.is_file():
        zips.append(examples)
    stats = write_plant_yolo(zips, Path(args.tiles), Path(args.out))
    print(
        f"wrote {stats['chips']} chips / {stats['plant_instances']} plants "
        f"from {stats['tiles']} tiles -> {args.out}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
