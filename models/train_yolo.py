#!/usr/bin/env python3
"""Ultralytics YOLO11 fine-tune stub. Public AGPL-3.0 weights + datasets only."""

from __future__ import annotations

import argparse
import os
from pathlib import Path


PROFILES = {
    "h100": {"model": {"segment": "yolo11m-seg.pt", "detect": "yolo11m.pt"}, "imgsz": 1280, "batch": 16},
    "gpu16": {"model": {"segment": "yolo11s-seg.pt", "detect": "yolo11s.pt"}, "imgsz": 1024, "batch": 4},
}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--task", choices=["segment", "detect"], required=True)
    p.add_argument("--data", required=True)
    p.add_argument("--profile", choices=sorted(PROFILES), default=os.environ.get("HARDWARE_PROFILE", "h100"))
    p.add_argument("--epochs", type=int, default=80)
    p.add_argument("--project", default="models/runs")
    p.add_argument("--name", default=None)
    args = p.parse_args()

    cfg = PROFILES[args.profile]
    weights = cfg["model"][args.task]
    name = args.name or f"{args.task}-{args.profile}"

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
    dest = Path("models/weights")
    dest.mkdir(parents=True, exist_ok=True)
    print(f"copy best.pt from {args.project}/{name}/weights/best.pt to {dest}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
