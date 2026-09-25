#!/usr/bin/env bash
# Convert Riseholme as soon as the zip is complete, then train YOLO11m-seg.
set -euo pipefail
ROOT="${ROOT:-/home/prodius/projects/bei50}"
cd "$ROOT"
# shellcheck disable=SC1091
source .venv/bin/activate

part=datasets/riseholme/riseholme-vineyard.zip.part
dest=datasets/riseholme/riseholme-vineyard.zip
need=3000000000

echo "waiting for Riseholme zip"
while true; do
  if [[ -f "$dest" ]] && [[ "$(stat -c%s "$dest")" -ge "$need" ]]; then
    break
  fi
  if [[ -f "$part" ]] && ! pgrep -f "riseholme-vineyard.zip.part" >/dev/null; then
    sz="$(stat -c%s "$part")"
    echo "curl done, size=$sz"
    if [[ "$sz" -ge "$need" ]]; then
      mv "$part" "$dest"
      break
    fi
    echo "zip too small, abort"
    exit 1
  fi
  if [[ -f "$part" ]]; then
    echo "  $(stat -c%s "$part") / $need"
  fi
  sleep 15
done

echo "converting Riseholme"
python models/prepare_riseholme.py --root datasets/riseholme --out datasets/riseholme-yolo --skip-download
echo "training YOLO11m-seg"
python models/train_yolo.py --task segment --data models/configs/vineyard.yaml --profile h100 --arch yolo11 --epochs 60
echo "riseholme train done"
