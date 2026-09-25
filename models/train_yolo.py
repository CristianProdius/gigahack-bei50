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
    args = p.parse_args()

    arch = args.arch or DEFAULT_ARCH[args.task]
    cfg = PROFILES[args.profile][args.task]
    if arch not in cfg:
        raise SystemExit(f"{arch} is not configured for {args.task} on {args.profile}")
    weights = cfg[arch]
    name = args.name or f"{args.task}-{arch}-{args.profile}"

    try:
        from ultralytics import YOLO
    except ImportError:
        print("ultralytics is not installed. pip install ultralytics  (AGPL-3.0)")
        print(f"Would train {weights} on {args.data} imgsz={cfg['imgsz']} batch={cfg['batch']}")
        return 2

    model = YOLO(weights)
    model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=cfg["imgsz"],
        batch=cfg["batch"],
        amp=True,
        project=args.project,
        name=name,
        exist_ok=True,
    )
    best = Path(args.project) / name / "weights" / "best.pt"
    dest = Path(args.copy_best) if args.copy_best else Path("models/weights") / (
        "vineyard.pt" if args.task == "segment" else "waste.pt"
    )
    dest.parent.mkdir(parents=True, exist_ok=True)
    if best.is_file():
        shutil.copy2(best, dest)
        print(f"copied {best} -> {dest}")
    else:
        print(f"train finished but {best} missing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
