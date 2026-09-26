#!/usr/bin/env python3
"""Fine-tune Ultralytics YOLO on public data only (Riseholme / DroneWaste).

Default lock (docs/sota-research.md): YOLO11m-seg for canopies, YOLO12 detect for waste.
YOLO26 is an optional A/B. Do not train on Sireț3 labels drawn outside Marcaj.
"""

from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path


# profile -> task -> (arch, weights, imgsz, batch)
PROFILES = {
    "h100": {
        "segment": {"yolo11": "yolo11m-seg.pt", "yolo26": "yolo26m-seg.pt", "imgsz": 1280, "batch": 16},
        "detect": {"yolo11": "yolo11m.pt", "yolo12": "yolo12m.pt", "yolo26": "yolo26m.pt", "imgsz": 1280, "batch": 16},
    },
    "gpu16": {
        "segment": {"yolo11": "yolo11s-seg.pt", "yolo26": "yolo26s-seg.pt", "imgsz": 1024, "batch": 4},
        "detect": {"yolo11": "yolo11s.pt", "yolo12": "yolo12s.pt", "yolo26": "yolo26s.pt", "imgsz": 1024, "batch": 4},
    },
}

DEFAULT_ARCH = {"segment": "yolo11", "detect": "yolo12"}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--task", choices=["segment", "detect"], required=True)
    p.add_argument("--data", required=True)
    p.add_argument("--profile", choices=sorted(PROFILES), default=os.environ.get("HARDWARE_PROFILE", "h100"))
    p.add_argument("--arch", choices=["yolo11", "yolo12", "yolo26"], default=None)
    p.add_argument("--epochs", type=int, default=80)
    p.add_argument("--project", default="models/runs")
    p.add_argument("--name", default=None)
    p.add_argument("--copy-best", default=None, help="optional dest .pt (default models/weights/{vineyard,waste}.pt)")
    p.add_argument("--weights", default=None, help="start from this .pt instead of a COCO checkpoint")
    p.add_argument("--imgsz", type=int, default=None)
    p.add_argument("--batch", type=int, default=None)
    p.add_argument("--lr0", type=float, default=None)
    p.add_argument("--copy-paste", type=float, default=0.0)
    p.add_argument("--degrees", type=float, default=0.0)
    p.add_argument("--flipud", type=float, default=0.0)
    p.add_argument("--mixup", type=float, default=0.0)
    p.add_argument("--scale", type=float, default=0.5)
    p.add_argument("--translate", type=float, default=0.1)
    p.add_argument("--hsv-s", type=float, default=0.7)
    p.add_argument("--hsv-v", type=float, default=0.4)
    p.add_argument("--patience", type=int, default=30)
    p.add_argument("--max-det", type=int, default=300)
    p.add_argument("--close-mosaic", type=int, default=10)
    args = p.parse_args()

    arch = args.arch or DEFAULT_ARCH[args.task]
    cfg = PROFILES[args.profile][args.task]
    if arch not in cfg:
        raise SystemExit(f"{arch} is not configured for {args.task} on {args.profile}")
    weights = args.weights or cfg[arch]
    name = args.name or f"{args.task}-{arch}-{args.profile}"

    try:
        from ultralytics import YOLO
    except ImportError:
        print("ultralytics is not installed. pip install ultralytics  (AGPL-3.0)")
        print(f"Would train {weights} on {args.data} imgsz={cfg['imgsz']} batch={cfg['batch']}")
        return 2

    model = YOLO(weights)
    train_kw = dict(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz or cfg["imgsz"],
        batch=args.batch or cfg["batch"],
        amp=True,
        project=args.project,
        name=name,
        exist_ok=True,
        copy_paste=args.copy_paste,
        degrees=args.degrees,
        flipud=args.flipud,
        mixup=args.mixup,
        scale=args.scale,
        translate=args.translate,
        hsv_s=args.hsv_s,
        hsv_v=args.hsv_v,
        patience=args.patience,
        max_det=args.max_det,
        close_mosaic=args.close_mosaic,
    )
    if args.lr0 is not None:
        train_kw["lr0"] = args.lr0
    model.train(**train_kw)
    dest = Path(args.copy_best) if args.copy_best else Path("models/weights") / (
        "vineyard.pt" if args.task == "segment" else "waste.pt"
    )
    dest.parent.mkdir(parents=True, exist_ok=True)
    best = None
    trainer = getattr(model, "trainer", None)
    if trainer is not None and getattr(trainer, "best", None):
        best = Path(trainer.best)
    if best is None or not best.is_file():
        guessed = Path(args.project) / name / "weights" / "best.pt"
        hits = [guessed, *Path("runs").glob(f"**/{name}/weights/best.pt")]
        best = next((p for p in hits if p.is_file()), guessed)
    if best.is_file():
        shutil.copy2(best, dest)
        print(f"copied {best} -> {dest}")
    else:
        print(f"train finished but {best} missing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
