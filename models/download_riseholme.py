#!/usr/bin/env python3
"""Download Riseholme UAV vineyard COCO (Zenodo 19234907, CC-BY-4.0)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from urllib.request import urlretrieve

URL = "https://zenodo.org/records/19234907/files/riseholme-vineyard.zip?download=1"
DOI = "https://doi.org/10.5281/zenodo.19234907"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="data/source/riseholme-vineyard.zip")
    args = p.parse_args()
    dest = Path(args.out)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_file() and dest.stat().st_size > 1_000_000_000:
        print("already present", dest, dest.stat().st_size)
        return 0
    print("downloading", DOI, "->", dest)
    urlretrieve(URL, dest)
    print("bytes", dest.stat().st_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
