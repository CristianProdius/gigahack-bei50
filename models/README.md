# YOLO / SAM / GRowSeg

Fine-tune on **other** public data (Riseholme, DroneWaste). Do not train on Sireț3 labels drawn outside Marcaj.

Locked stack: [`docs/sota-research.md`](../docs/sota-research.md).

## Prepare datasets (H100 or any box with disk)

```bash
python models/prepare_riseholme.py --root datasets/riseholme --out datasets/riseholme-yolo
python models/prepare_dronewaste.py --root datasets/dronewaste --out datasets/dronewaste-yolo
```

Riseholme zip is 3.3 GB (CC-BY-4.0). DroneWaste images tarball is 3.8 GB (CC-BY-4.0).

## Vineyard instance segmentation

Default: **YOLO11m-seg** (what Riseholme was trained as). Optional A/B: `--arch yolo26`.

```bash
python models/train_yolo.py --task segment --data models/configs/vineyard.yaml --profile h100 --arch yolo11
```

16 GB: `--profile gpu16`.

## Waste boxes

Default: **YOLO12** detect, one class. Optional `--arch yolo26`.

```bash
python models/train_yolo.py --task detect --data models/configs/waste.yaml --profile h100 --arch yolo12
```

## Infer 311 tiles

```bash
python models/infer_yolo.py --weights models/weights/vineyard.pt --tiles data/tiles --out data/predictions
python models/infer_yolo.py --weights models/weights/waste.pt --tiles data/tiles --out data/predictions_waste --conf 0.4
python models/infer_growseg.py --tiles data/tiles --out data/growseg --clone
python models/infer_sam.py --tiles data/tiles --boxes data/predictions --out data/sam_refine
```

## Remote H100 (`ssh gpu-server`)

Workspace: `/home/prodius/projects/bei50`. As of 25 Sep 2026 the H100 still held a root SGLang Qwen3.6-35B job (~76 GB). Downloads and convert can run while that is up. Training waits for VRAM.

```bash
rsync -az --exclude '.git' --exclude 'data/challenge/04_source' --exclude '.venv' \
  ./ gpu-server:/home/prodius/projects/bei50/
ssh gpu-server 'bash /home/prodius/projects/bei50/models/remote/bootstrap_h100.sh'
```

Weights are gitignored. Put the public URL you actually trained in the root README.

Ultralytics is AGPL-3.0. This repo is public. SAM / SAM2 / MobileSAM are Apache-2.0. GRowSeg is MIT.
