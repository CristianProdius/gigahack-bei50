#!/usr/bin/env python3
"""SAM / SAM2 / MobileSAM box-prompt stub for canopy cleanup."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--tiles", required=True)
    p.add_argument("--boxes", required=True, help="directory of per-tile GeoJSON from infer_yolo")
    p.add_argument("--out", default="data/sam_refine")
    p.add_argument("--backend", choices=["sam2", "sam", "mobilesam"], default="sam2")
    args = p.parse_args()

    print(
        f"{args.backend} prompt refine is stubbed. "
        "Install facebookresearch/sam2 (Apache-2.0) or ChaoningZhang/MobileSAM for 16 GB. "
        f"Would read boxes from {args.boxes} and write masks to {args.out}."
    )
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    n = 0
    for src in Path(args.boxes).glob("*.geojson"):
        data = json.loads(src.read_text(encoding="utf-8"))
        (out / src.name).write_text(json.dumps(data, indent=2), encoding="utf-8")
        n += 1
    print(f"copied {n} geojson files (no SAM weights loaded)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
