#!/usr/bin/env bash
# Convert DroneWaste when the tarball is complete, then train YOLO12 detect.
set -euo pipefail
ROOT="${ROOT:-/home/prodius/projects/bei50}"
cd "$ROOT"
# shellcheck disable=SC1091
source .venv/bin/activate

part=datasets/dronewaste/images.tar.gz.part
dest=datasets/dronewaste/images.tar.gz
need=3500000000

echo "waiting for DroneWaste tarball"
while true; do
  if [[ -f "$dest" ]] && [[ "$(stat -c%s "$dest")" -ge "$need" ]]; then
    break
  fi
  if [[ -f "$part" ]] && ! pgrep -f "dronewaste/images.tar.gz.part" >/dev/null; then
    sz="$(stat -c%s "$part")"
    echo "curl done, size=$sz"
    if [[ "$sz" -ge "$need" ]]; then
      mv "$part" "$dest"
      break
    fi
    echo "tarball too small, abort"
    exit 1
  fi
  if [[ -f "$part" ]]; then
    echo "  $(stat -c%s "$part") / $need"
  fi
  sleep 15
done

echo "converting DroneWaste"
python models/prepare_dronewaste.py --root datasets/dronewaste --out datasets/dronewaste-yolo --skip-download

echo "waiting for canopy train to release GPU if it is still running"
while pgrep -f "train_yolo.py --task segment" >/dev/null; do
  sleep 30
done

echo "training YOLO12 waste"
python models/train_yolo.py --task detect --data models/configs/waste.yaml --profile h100 --arch yolo12 --epochs 60
echo "dronewaste train done"
