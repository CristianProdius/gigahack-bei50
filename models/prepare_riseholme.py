#!/usr/bin/env python3
"""Download Riseholme COCO (CC-BY-4.0) and convert to YOLO-seg.

Source: https://doi.org/10.5281/zenodo.19234907
Roboflow layout: three seasons, each with train/valid/test/_annotations.coco.json
Do not use the AGRIDS or Kaggle mirrors (NC / ND).
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import zipfile
from pathlib import Path


ZENODO_URL = (
    "https://zenodo.org/api/records/19234907/files/riseholme-vineyard.zip/content"
)
ZIP_NAME = "riseholme-vineyard.zip"
CLASS_NAMES = ["vineyard", "vine_row", "pole", "trunk"]
SPLIT_MAP = {"train": "train", "valid": "val", "val": "val", "test": "test"}


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_file() and dest.stat().st_size > 1_000_000:
        print(f"already have {dest} ({dest.stat().st_size} bytes)")
        return
    tmp = dest.with_suffix(dest.suffix + ".part")
    print(f"downloading {url} -> {dest}")
    subprocess.check_call(["curl", "-L", "--fail", "--retry", "5", "-o", str(tmp), url])
    tmp.rename(dest)


def _ensure_extracted(zip_path: Path, extracted: Path) -> None:
    extracted.mkdir(parents=True, exist_ok=True)
    if any(extracted.rglob("_annotations.coco.json")):
        print(f"already extracted under {extracted}")
        return
    print(f"unzip {zip_path}")
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(extracted)


def _cat_id_to_name(coco: dict) -> dict[int, str]:
    out = {}
    for cat in coco.get("categories") or []:
        name = str(cat.get("name") or "").strip().lower().replace(" ", "_")
        if name in {"vine", "canopy", "grapevine"}:
            name = "vineyard"
        if name in {"row", "vine-row", "vinerow"}:
            name = "vine_row"
        out[int(cat["id"])] = name
    return out


def _write_yolo_label(ann_list: list, cats: dict[int, str], width: float, height: float, dest: Path) -> None:
    lines = []
    for ann in ann_list:
        name = cats.get(int(ann["category_id"]))
        if name not in CLASS_NAMES:
            continue
        cls = CLASS_NAMES.index(name)
        segs = ann.get("segmentation") or []
        if not segs or not isinstance(segs[0], list):
            # bbox fallback
            x, y, bw, bh = ann["bbox"]
            pts = [x, y, x + bw, y, x + bw, y + bh, x, y + bh]
        else:
            pts = segs[0]
        if len(pts) < 6:
            continue
        norm = []
        for i in range(0, len(pts) - 1, 2):
            norm.append(f"{float(pts[i]) / width:.6f}")
            norm.append(f"{float(pts[i + 1]) / height:.6f}")
        lines.append(f"{cls} " + " ".join(norm))
    dest.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def _convert_roboflow(extracted: Path, out: Path) -> None:
    if out.exists():
        shutil.rmtree(out)
    counts = {s: 0 for s in ("train", "val", "test")}
    for json_path in sorted(extracted.rglob("_annotations.coco.json")):
        split_name = json_path.parent.name.lower()
        split = SPLIT_MAP.get(split_name)
        if not split:
            print(f"skip unknown split {json_path}")
            continue
        coco = json.loads(json_path.read_text(encoding="utf-8"))
        cats = _cat_id_to_name(coco)
        print(f"{json_path.parent}: categories={cats}")
        images = {im["id"]: im for im in coco["images"]}
        anns: dict[int, list] = {}
        for ann in coco["annotations"]:
            anns.setdefault(ann["image_id"], []).append(ann)
        img_dir = out / "images" / split
        lbl_dir = out / "labels" / split
        img_dir.mkdir(parents=True, exist_ok=True)
        lbl_dir.mkdir(parents=True, exist_ok=True)
        for image_id, im in images.items():
            src = json_path.parent / im["file_name"]
            if not src.is_file():
                alt = json_path.parent / Path(im["file_name"]).name
                src = alt if alt.is_file() else src
            if not src.is_file():
                print(f"missing {src}")
                continue
            # unique name: season + file so three seasons do not collide
            season = json_path.parents[1].name.split(".")[0]
            dest_name = f"{season}__{src.name}"
            dest_img = img_dir / dest_name
            if dest_img.exists():
                dest_img.unlink()
            dest_img.symlink_to(src.resolve())
            _write_yolo_label(
                anns.get(image_id, []),
                cats,
                float(im["width"]),
                float(im["height"]),
                lbl_dir / f"{dest_img.stem}.txt",
            )
            counts[split] += 1
    print("images", counts)
    if counts["train"] == 0:
        raise SystemExit("no training images written")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", default="datasets/riseholme")
    p.add_argument("--out", default="datasets/riseholme-yolo")
    p.add_argument("--skip-download", action="store_true")
    args = p.parse_args()

    root = Path(args.root)
    zip_path = root / ZIP_NAME
    extracted = root / "extracted"
    if not args.skip_download:
        _download(ZENODO_URL, zip_path)
    if not zip_path.is_file():
        raise SystemExit(f"missing {zip_path}")
    _ensure_extracted(zip_path, extracted)
    _convert_roboflow(extracted, Path(args.out))
    print(
        "dataset ready. train with:\n"
        "  python models/train_yolo.py --task segment --data models/configs/vineyard.yaml --profile h100 --arch yolo11"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
