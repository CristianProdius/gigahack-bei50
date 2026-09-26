#!/usr/bin/env bash
# Train YOLO11m-seg from COCO on Sireț3 example plants + copy-paste + empty negatives.
# Riseholme has 0 per-plant vineyard masks — do not start from vineyard.pt.
set -euo pipefail
ROOT="${ROOT:-/home/prodius/projects/bei50}"
cd "$ROOT"
# shellcheck disable=SC1091
source .venv/bin/activate

if pgrep -f "models/train_yolo.py --task" >/dev/null; then
  echo "another train_yolo is running; not starting"
  exit 2
fi
if pgrep -f "models/infer_yolo.py --weights" >/dev/null; then
  echo "infer_yolo is running; not starting train"
  exit 2
fi

echo "prepare mix dataset (real chips + synth + negatives)"
python models/prepare_siret3_synth.py \
  --zip data/challenge/05_examples/siret3_examples_cvat.zip \
  --tiles data/tiles \
  --out datasets/siret3-mix-yolo

echo "train YOLO11m-seg from COCO yolo11m-seg.pt"
python models/train_yolo.py \
  --task segment \
  --data datasets/siret3-mix-yolo/siret3-mix.yaml \
  --profile h100 \
  --arch yolo11 \
  --epochs 80 \
  --name segment-siret3-mix \
  --copy-best models/weights/vineyard_siret3_mix.pt \
  --imgsz 640 \
  --batch 24 \
  --lr0 0.005 \
  --copy-paste 0.5 \
  --degrees 30 \
  --flipud 0.5 \
  --mixup 0.15 \
  --scale 0.6 \
  --translate 0.15 \
  --hsv-s 0.8 \
  --hsv-v 0.5 \
  --patience 20 \
  --max-det 2000 \
  --close-mosaic 15
echo "siret3 mix plant train done"
