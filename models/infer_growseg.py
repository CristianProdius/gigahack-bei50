#!/usr/bin/env python3
"""Zero-shot GRowSeg row prior (SegFormer-B5, MIT) on Sireț3 tiles.

Weights/card: https://huggingface.co/links-ads/gaia-growseg
Code: git clone https://huggingface.co/links-ads/vitigeoss-growseg
Challenge tiles are 0.025 m/px; authors recommend 1–1.5 cm/px so
scaling_factor ≈ 0.025 / 0.015 ≈ 1.67.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--tiles", default="data/tiles")
    p.add_argument("--out", default="data/growseg")
    p.add_argument("--repo", default="vendor/vitigeoss-growseg")
    p.add_argument("--scaling-factor", type=float, default=1.67)
    p.add_argument("--patch-size", type=int, default=512)
    p.add_argument("--clone", action="store_true")
    args = p.parse_args()

    repo = Path(args.repo)
    if args.clone and not (repo / "main.py").is_file():
        repo.parent.mkdir(parents=True, exist_ok=True)
        subprocess.check_call(
            ["git", "lfs", "install"],
        )
        subprocess.check_call(
            ["git", "clone", "https://huggingface.co/links-ads/vitigeoss-growseg", str(repo)]
        )

    main_py = repo / "main.py"
    tiles = sorted(Path(args.tiles).glob("siret3_r*_c*.tif"))
    if not tiles:
        raise SystemExit(f"no tiles in {args.tiles}")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    if not main_py.is_file():
        print(
            "GRowSeg repo missing. Clone with:\n"
            "  git lfs install && git clone https://huggingface.co/links-ads/vitigeoss-growseg vendor/vitigeoss-growseg\n"
            f"Would run {len(tiles)} tiles -> {out} scaling_factor={args.scaling_factor}"
        )
        (out / "README.txt").write_text(
            "Place vitigeoss-growseg at vendor/vitigeoss-growseg then re-run.\n",
            encoding="utf-8",
        )
        return 2

    for tile in tiles:
        dest = out / f"{tile.stem}.tif"
        cmd = [
            "python",
            str(main_py),
            str(tile),
            str(dest),
            "--patch_size",
            str(args.patch_size),
            "--scaling_factor",
            str(args.scaling_factor),
        ]
        print(" ".join(cmd))
        subprocess.check_call(cmd)
    manifest = {"n": len(tiles), "scaling_factor": args.scaling_factor, "repo": str(repo)}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
