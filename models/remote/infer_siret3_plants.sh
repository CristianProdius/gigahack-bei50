#!/usr/bin/env bash
# Chip-infer 311 Sireț3 tiles with the examples-only plant model.
# Writes data/predictions_plants — does not touch waste or the old strip GeoJSON.
set -euo pipefail
ROOT="${ROOT:-/home/prodius/projects/bei50}"
cd "$ROOT"
# shellcheck disable=SC1091
source .venv/bin/activate

if pgrep -f "models/train_yolo.py --task" >/dev/null; then
  echo "train_yolo is running; not starting infer"
  exit 2
fi
if pgrep -f "models/infer_yolo.py --weights" >/dev/null; then
  echo "infer_yolo is running; not starting another"
  exit 2
fi

WEIGHTS="${WEIGHTS:-models/weights/vineyard_siret3_v2.pt}"
if [[ ! -f "$WEIGHTS" ]]; then
  echo "missing $WEIGHTS"
  exit 1
fi

echo "infer plants chip 640 conf ${CONF:-0.12}"
python models/infer_yolo.py \
  --weights "$WEIGHTS" \
  --tiles "${TILES:-data/tiles}" \
  --out "${OUT:-data/predictions_plants}" \
  --chip 640 \
  --stride 320 \
  --imgsz 640 \
  --conf "${CONF:-0.12}" \
  --max-det 2000
echo "infer_siret3_plants done"
