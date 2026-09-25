# YOLO / SAM stubs

Fine-tune on **other** public data (Riseholme, DroneWaste). Do not train on Sireț3 labels drawn outside Marcaj.

## Vineyard instance segmentation (H100)

```bash
# after downloading Riseholme COCO (CC-BY-4.0)
# https://doi.org/10.5281/zenodo.19234907
python models/train_yolo.py --task segment --data models/configs/vineyard.yaml --profile h100
```

16 GB path:

```bash
HARDWARE_PROFILE=gpu16 python models/train_yolo.py --task segment --data models/configs/vineyard.yaml --profile gpu16
```

## Waste boxes

```bash
# DroneWaste CC-BY-4.0 https://doi.org/10.5281/zenodo.17045559
# collapse 20 EWC classes to one "waste" class in the YAML
python models/train_yolo.py --task detect --data models/configs/waste.yaml --profile h100
```

## Infer 311 tiles

```bash
python models/infer_yolo.py --weights models/weights/vineyard.pt --tiles data/tiles --out data/predictions
python models/infer_sam.py --tiles data/tiles --boxes data/predictions --out data/sam_refine
```

Weights are gitignored. Put the public URL you actually trained in the root README.

Ultralytics is AGPL-3.0. This repo is public. SAM / SAM2 / MobileSAM are Apache-2.0.
