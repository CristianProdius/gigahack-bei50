#!/usr/bin/env bash
# Fine-tune YOLO11m-seg on Marcaj-corrected plants + official example tiles.
set -euo pipefail
ROOT="${ROOT:-/home/prodius/projects/bei50}"
cd "$ROOT"
# shellcheck disable=SC1091
source .venv/bin/activate

if pgrep -f "python.*train_yolo.py" >/dev/null; then
  echo "another train_yolo is running; not starting"
  exit 2
fi

MARCAJ_ZIP="${MARCAJ_ZIP:-data/marcaj_export/marcaj_cvat_2026-09-26.zip}"
if [[ ! -f "$MARCAJ_ZIP" ]]; then
  echo "missing $MARCAJ_ZIP"
  exit 1
fi

python models/prepare_siret3_marcaj.py \
  --marcaj-zip "$MARCAJ_ZIP" \
  --tiles data/tiles \
  --out datasets/siret3-marcaj-yolo

python models/train_yolo.py \
  --task segment \
  --data datasets/siret3-marcaj-yolo/siret3-plants.yaml \
  --profile h100 \
  --arch yolo11 \
  --weights yolo11m-seg.pt \
  --epochs 40 \
  --name segment-siret3-marcaj \
  --copy-best models/weights/vineyard_marcaj.pt \
  --imgsz 640 \
  --batch 24 \
  --lr0 0.005 \
  --copy-paste 0.35 \
  --degrees 15 \
  --flipud 0.5 \
  --max-det 2000 \
  --patience 12 \
  --close-mosaic 8
echo "marcaj plant fine-tune done"
