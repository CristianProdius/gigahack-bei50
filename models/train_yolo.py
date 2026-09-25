#!/usr/bin/env python3
"""Ultralytics YOLO11 fine-tune. Public AGPL-3.0 weights + datasets only. No Sireț3 labels."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import time
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hardware import PROFILES, report, resolve_profile  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--task", choices=["segment", "detect"], required=True)
    p.add_argument("--data", required=True)
    p.add_argument("--profile", choices=sorted(PROFILES), default=None)
    p.add_argument("--epochs", type=int, default=80)
    p.add_argument("--project", default="models/runs")
    p.add_argument("--name", default=None)
    p.add_argument("--weights", default=None, help="override base checkpoint")
    p.add_argument("--imgsz", type=int, default=None)
    p.add_argument("--batch", type=int, default=None)
    p.add_argument("--device", default=None)
    p.add_argument("--copy-to", default="models/weights")
    args = p.parse_args()

    profile = resolve_profile(args.profile)
    cfg = PROFILES[profile]
    weights = args.weights or cfg[args.task]
    imgsz = args.imgsz or cfg["imgsz"]
    batch = args.batch or cfg["batch"]
    name = args.name or f"{args.task}-{profile}"
    hw = report()
    print("hardware:", json.dumps(hw, indent=2))
    print(f"train {args.task} profile={profile} weights={weights} imgsz={imgsz} batch={batch}")

    try:
        from ultralytics import YOLO
    except ImportError:
        print("ultralytics is not installed. pip install ultralytics  (AGPL-3.0)")
        return 2

    device = args.device
    if device is None:
        device = 0 if "cuda" in hw["torch_device"] else "cpu"

    t0 = time.time()
    model = YOLO(weights)
    project = str(Path(args.project).resolve())
    Path(project).mkdir(parents=True, exist_ok=True)
    model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=imgsz,
        batch=batch,
        amp=device != "cpu",
        project=project,
        name=name,
        exist_ok=True,
        device=device,
        workers=min(8, os.cpu_count() or 2),
    )
    elapsed = time.time() - t0
    trainer = getattr(model, "trainer", None)
    run_dir = Path(getattr(trainer, "save_dir", "") or (Path(project) / name))
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "hardware.json").write_text(
        json.dumps({**hw, "seconds": elapsed, "epochs": args.epochs, "save_dir": str(run_dir)}, indent=2),
        encoding="utf-8",
    )
    best = run_dir / "weights" / "best.pt"
    dest_dir = Path(args.copy_to)
    dest_dir.mkdir(parents=True, exist_ok=True)
    if best.is_file():
        dest = dest_dir / f"{name}.pt"
        shutil.copy2(best, dest)
        print(f"copied {best} -> {dest}")
    print(f"train wall_s={elapsed:.1f} gpu={hw['nvidia_smi']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
