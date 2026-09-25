#!/usr/bin/env bash
# Prepare the gpu-server workspace. Safe to run while another job holds the H100.
set -euo pipefail
ROOT="${ROOT:-/home/prodius/projects/bei50}"
cd "$ROOT"

python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -U pip
pip install ultralytics rasterio  # AGPL-3.0 + BSD

mkdir -p datasets models/weights data/tiles logs
echo "venv ready at $ROOT/.venv"
echo "GPU:"
nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv,noheader || true
echo "Next:"
echo "  python models/prepare_riseholme.py"
echo "  python models/prepare_dronewaste.py"
echo "  # wait until nvidia-smi memory.used is low, then:"
echo "  python models/train_yolo.py --task segment --data models/configs/vineyard.yaml --profile h100 --arch yolo11"
echo "  python models/train_yolo.py --task detect --data models/configs/waste.yaml --profile h100 --arch yolo12"
