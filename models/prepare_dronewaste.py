#!/usr/bin/env python3
"""Download DroneWaste (CC-BY-4.0) and collapse 20 EWC classes to one waste box class.

Source: https://doi.org/10.5281/zenodo.17045559
Paper is CC BY-NC-ND (cite only). Images stay CC-BY-4.0.
"""

from __future__ import annotations

import argparse
import json
import random
import shutil
import subprocess
import tarfile
from collections import defaultdict
from pathlib import Path


IMAGES_URL = "https://zenodo.org/api/records/17045559/files/images.tar.gz/content"
ANN_URL = "https://zenodo.org/api/records/17045559/files/dronewaste_v1.0.json/content"


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_file() and dest.stat().st_size > 1_000:
        print(f"already have {dest} ({dest.stat().st_size} bytes)")
        return
    tmp = dest.with_suffix(dest.suffix + ".part")
    print(f"downloading {url} -> {dest}")
    subprocess.check_call(["curl", "-L", "--fail", "--retry", "5", "-o", str(tmp), url])
    tmp.rename(dest)


def _coco_to_yolo_boxes(coco: dict, images_root: Path, out: Path, val_frac: float, seed: int) -> None:
    """Write a single-class YOLO detect dataset. All categories become waste=0."""
    rng = random.Random(seed)
    images_by_id = {im["id"]: im for im in coco["images"]}
    anns_by_image: dict[int, list] = defaultdict(list)
    for ann in coco["annotations"]:
        anns_by_image[ann["image_id"]].append(ann)

    ids = list(images_by_id)
    rng.shuffle(ids)
    n_val = max(1, int(len(ids) * val_frac))
    splits = {"val": ids[:n_val], "train": ids[n_val:]}

    if out.exists():
        shutil.rmtree(out)
    for split, image_ids in splits.items():
        img_dir = out / "images" / split
        lbl_dir = out / "labels" / split
        img_dir.mkdir(parents=True, exist_ok=True)
        lbl_dir.mkdir(parents=True, exist_ok=True)
        for image_id in image_ids:
            im = images_by_id[image_id]
            file_name = im["file_name"]
            src = images_root / file_name
            if not src.is_file():
                # some dumps nest images/
                alt = images_root / Path(file_name).name
                src = alt if alt.is_file() else src
            if not src.is_file():
                matches = list(images_root.rglob(Path(file_name).name))
                if not matches:
                    print(f"missing image {file_name}")
                    continue
                src = matches[0]
            dest_img = img_dir / src.name
            if not dest_img.exists():
                dest_img.symlink_to(src.resolve())
            w = float(im["width"])
            h = float(im["height"])
            lines = []
            for ann in anns_by_image[image_id]:
                x, y, bw, bh = ann["bbox"]  # COCO xywh
                cx = (x + bw / 2.0) / w
                cy = (y + bh / 2.0) / h
                nw = bw / w
                nh = bh / h
                lines.append(f"0 {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}")
            (lbl_dir / f"{src.stem}.txt").write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        print(f"{split}: {len(image_ids)} images")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", default="datasets/dronewaste")
    p.add_argument("--out", default="datasets/dronewaste-yolo")
    p.add_argument("--val-frac", type=float, default=0.15)
    p.add_argument("--skip-download", action="store_true")
    args = p.parse_args()

    root = Path(args.root)
    images_tar = root / "images.tar.gz"
    ann_path = root / "dronewaste_v1.0.json"
    images_root = root / "images"
    if not args.skip_download:
        _download(ANN_URL, ann_path)
        _download(IMAGES_URL, images_tar)
    has_images = images_root.exists() and (
        any(images_root.rglob("*.jpg")) or any(images_root.rglob("*.png"))
    )
    if not has_images:
        if not images_tar.is_file():
            raise SystemExit(f"missing {images_tar}; download first or drop --skip-download")
        print(f"extract {images_tar}")
        with tarfile.open(images_tar) as tf:
            tf.extractall(root)

    coco = json.loads(ann_path.read_text(encoding="utf-8"))
    n_cat = len(coco.get("categories") or [])
    print(f"collapsing {n_cat} EWC classes -> waste")
    _coco_to_yolo_boxes(coco, images_root if images_root.exists() else root, Path(args.out), args.val_frac, seed=2026)
    print("dataset ready. train with:\n  python models/train_yolo.py --task detect --data models/configs/waste.yaml --profile h100 --arch yolo12")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
