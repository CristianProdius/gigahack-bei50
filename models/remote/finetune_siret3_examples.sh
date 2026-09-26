#!/usr/bin/env bash
# Train YOLO11m-seg on the official Sireț3 example plants only (no Riseholme).
set -euo pipefail
ROOT="${ROOT:-/home/prodius/projects/bei50}"
cd "$ROOT"
# shellcheck disable=SC1091
source .venv/bin/activate

if pgrep -f "python.*train_yolo.py" >/dev/null; then
  echo "another train_yolo is running; not starting"
  exit 2
fi

echo "prepare example chips (640 / both official tiles)"
python models/prepare_siret3_examples.py \
  --zip data/challenge/05_examples/siret3_examples_cvat.zip \
  --tiles data/tiles \
  --out datasets/siret3-examples-yolo

echo "train canopy on Sireț3 examples from COCO yolo11m-seg (not Riseholme)"
python models/train_yolo.py \
  --task segment \
  --data datasets/siret3-examples-yolo/siret3-examples.yaml \
  --profile h100 \
  --arch yolo11 \
  --epochs 80 \
  --name segment-siret3-plants \
  --copy-best models/weights/vineyard_siret3.pt \
  --imgsz 640 \
  --batch 24 \
  --lr0 0.01 \
  --copy-paste 0.4 \
  --degrees 20 \
  --flipud 0.5 \
  --max-det 2000 \
  --close-mosaic 20
echo "siret3 plant train done"
