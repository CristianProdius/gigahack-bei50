#!/usr/bin/env python3
"""Build a 1-class plant YOLO-seg set: official example chips + copy-paste + empty negatives.

Riseholme's COCO `vineyard` class is empty (Roboflow dummy). Do not mix it in.
"""

from __future__ import annotations

import argparse
import random
import shutil
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "processing" / "src"))

from siret3.example_yolo import (  # noqa: E402
    _plants_from_example_zip,
    _read_rgb,
    _save_rgb,
    write_example_yolo,
    yolo_seg_line,
)
from siret3.synth_plants import crop_plant, paste_plants_on_background  # noqa: E402


def _list_tiles(tiles_dir: Path) -> list[Path]:
    return sorted(tiles_dir.glob("siret3_r*_c*.tif"))


def _chip(rgb: np.ndarray, size: int, rng: random.Random) -> np.ndarray:
    h, w = rgb.shape[:2]
    if h < size or w < size:
        out = np.zeros((size, size, 3), dtype=np.uint8)
        out[:h, :w] = rgb
        return out
    x0 = rng.randint(0, w - size)
    y0 = rng.randint(0, h - size)
    return rgb[y0 : y0 + size, x0 : x0 + size].copy()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--zip", default="data/challenge/05_examples/siret3_examples_cvat.zip")
    p.add_argument("--tiles", default="data/tiles")
    p.add_argument("--examples-out", default="datasets/siret3-examples-yolo")
    p.add_argument("--out", default="datasets/siret3-mix-yolo")
    p.add_argument("--chip", type=int, default=640)
    p.add_argument("--n-synth", type=int, default=900)
    p.add_argument("--n-neg", type=int, default=250)
    p.add_argument("--seed", type=int, default=0)
    args = p.parse_args()

    tiles_dir = Path(args.tiles)
    examples_out = Path(args.examples_out)
    stats = write_example_yolo(Path(args.zip), tiles_dir, examples_out, chip=args.chip)
    print(f"real chips {stats}")

    images = _plants_from_example_zip(Path(args.zip))
    gold_names = {name for name, _ in images}
    cutouts: list[tuple[np.ndarray, list[tuple[float, float]]]] = []
    for name, plants in images:
        rgb = _read_rgb(tiles_dir / name)
        for poly in plants:
            cut, local = crop_plant(rgb, poly, pad=2)
            if int(cut[..., 3].sum()) == 0:
                continue
            cutouts.append((cut, local))
    if not cutouts:
        raise SystemExit("no plant cutouts from example ZIP")

    tiles = _list_tiles(tiles_dir)
    bg_tiles = [t for t in tiles if t.name not in gold_names] or tiles
    rng = random.Random(args.seed)

    out = Path(args.out)
    if out.exists():
        shutil.rmtree(out)
    for split in ("train", "val"):
        (out / "images" / split).mkdir(parents=True)
        (out / "labels" / split).mkdir(parents=True)

    # copy real example chips
    for split in ("train", "val"):
        src_img = examples_out / "images" / split
        src_lab = examples_out / "labels" / split
        for im in src_img.glob("*"):
            shutil.copy2(im, out / "images" / split / f"real_{im.name}")
            lab = src_lab / f"{im.stem}.txt"
            if lab.is_file():
                shutil.copy2(lab, out / "labels" / split / f"real_{im.stem}.txt")

    n_synth = 0
    for i in range(args.n_synth):
        bg_path = rng.choice(bg_tiles)
        bg = _chip(_read_rgb(bg_path), args.chip, rng)
        n_pl = rng.randint(4, 28)
        image, polys = paste_plants_on_background(
            bg, cutouts, n_plants=n_pl, rng_seed=args.seed + i + 1
        )
        if not polys:
            continue
        stem = f"synth_{i:04d}"
        split = "val" if i % 12 == 0 else "train"
        _save_rgb(out / "images" / split / f"{stem}.jpg", image)
        lines = [yolo_seg_line(0, poly, args.chip, args.chip) for poly in polys]
        (out / "labels" / split / f"{stem}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
        n_synth += 1

    n_neg = 0
    for i in range(args.n_neg):
        bg_path = rng.choice(bg_tiles)
        bg = _chip(_read_rgb(bg_path), args.chip, rng)
        stem = f"neg_{i:04d}"
        split = "val" if i % 10 == 0 else "train"
        _save_rgb(out / "images" / split / f"{stem}.jpg", bg)
        (out / "labels" / split / f"{stem}.txt").write_text("", encoding="utf-8")
        n_neg += 1

    (out / "siret3-mix.yaml").write_text(
        "\n".join(
            [
                f"path: {out.resolve()}",
                "train: images/train",
                "val: images/val",
                "names:",
                "  0: vineyard",
                "",
            ]
        ),
        encoding="utf-8",
    )
    n_train = len(list((out / "images" / "train").glob("*")))
    n_val = len(list((out / "images" / "val").glob("*")))
    print(f"cutouts {len(cutouts)} synth {n_synth} neg {n_neg} train {n_train} val {n_val} -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
