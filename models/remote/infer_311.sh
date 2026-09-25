#!/usr/bin/env bash
# Infer 311 tiles on the H100. Do not start while waste train is running.
set -euo pipefail
ROOT="${ROOT:-/home/prodius/projects/bei50}"
cd "$ROOT"
# shellcheck disable=SC1091
source .venv/bin/activate

if pgrep -f "train_yolo.py --task detect" >/dev/null; then
  echo "waste train still running; not starting infer"
  exit 2
fi

best=runs/detect/models/runs/detect-yolo12-h100/weights/best.pt
if [[ -f "$best" ]]; then
  mkdir -p models/weights
  cp -f "$best" models/weights/waste.pt
  echo "copied $best -> models/weights/waste.pt"
fi

if [[ ! -f models/weights/vineyard.pt ]]; then
  echo "missing models/weights/vineyard.pt"
  exit 1
fi
if [[ ! -f models/weights/waste.pt ]]; then
  echo "missing models/weights/waste.pt"
  exit 1
fi

echo "infer canopy"
python models/infer_yolo.py --weights models/weights/vineyard.pt --tiles data/tiles --out data/predictions
echo "infer waste"
python models/infer_yolo.py --weights models/weights/waste.pt --tiles data/tiles --out data/predictions_waste --conf 0.4
echo "infer_311 done"
