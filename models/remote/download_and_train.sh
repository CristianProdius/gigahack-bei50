#!/usr/bin/env bash
# Finish dataset prep. Train only when the H100 has free VRAM.
set -euo pipefail
ROOT="${ROOT:-/home/prodius/projects/bei50}"
cd "$ROOT"
# shellcheck disable=SC1091
source .venv/bin/activate

wait_file() {
  local part="$1" dest="$2" min_bytes="$3"
  echo "waiting for $part (>= $min_bytes bytes)"
  while true; do
    if [[ -f "$dest" ]] && [[ "$(stat -c%s "$dest")" -ge "$min_bytes" ]]; then
      echo "have $dest"
      return 0
    fi
    if [[ -f "$part" ]]; then
      local sz
      sz="$(stat -c%s "$part")"
      echo "  $part $sz"
      # curl done? part stops growing for 20s and no curl on that file
      sleep 10
    else
      sleep 10
    fi
    # If curl finished, rename
    if [[ -f "$part" ]] && ! pgrep -f "$part" >/dev/null; then
      local psz
      psz="$(stat -c%s "$part")"
      if [[ "$psz" -ge "$min_bytes" ]]; then
        mv "$part" "$dest"
        echo "moved $part -> $dest"
        return 0
      fi
    fi
  done
}

wait_file datasets/riseholme/riseholme-vineyard.zip.part datasets/riseholme/riseholme-vineyard.zip 3000000000
wait_file datasets/dronewaste/images.tar.gz.part datasets/dronewaste/images.tar.gz 3500000000

python models/prepare_riseholme.py --root datasets/riseholme --out datasets/riseholme-yolo --skip-download
python models/prepare_dronewaste.py --root datasets/dronewaste --out datasets/dronewaste-yolo --skip-download

echo "datasets converted. waiting for GPU memory < 12 GiB"
while true; do
  used="$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1 | tr -d ' ')"
  echo "  gpu used ${used} MiB"
  if [[ "$used" -lt 12000 ]]; then
    break
  fi
  sleep 60
done

python models/train_yolo.py --task segment --data models/configs/vineyard.yaml --profile h100 --arch yolo11 --epochs 60
python models/train_yolo.py --task detect --data models/configs/waste.yaml --profile h100 --arch yolo12 --epochs 60
echo "training done"
