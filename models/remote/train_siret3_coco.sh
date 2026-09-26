#!/usr/bin/env bash
# Train plants from COCO YOLO11m-seg on the official Sireț3 example tiles only.
# Do not load vineyard.pt / Riseholme (that dump has 0 plant masks).
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

echo "prepare official example chips only"
python models/prepare_siret3_examples.py \
  --zip data/challenge/05_examples/siret3_examples_cvat.zip \
  --tiles data/tiles \
  --out datasets/siret3-examples-yolo

echo "train YOLO11m-seg from COCO (yolo11m-seg.pt), not Riseholme"
python models/train_yolo.py \
  --task segment \
  --data datasets/siret3-examples-yolo/siret3-examples.yaml \
  --profile h100 \
  --arch yolo11 \
  --epochs 60 \
  --name segment-siret3-coco \
  --copy-best models/weights/vineyard_siret3_v2.pt \
  --imgsz 640 \
  --batch 24 \
  --lr0 0.008 \
  --copy-paste 0.5 \
  --degrees 25 \
  --flipud 0.5 \
  --mixup 0.1 \
  --scale 0.6 \
  --translate 0.15 \
  --patience 15 \
  --max-det 2000 \
  --close-mosaic 12
echo "siret3 COCO plant train done"
