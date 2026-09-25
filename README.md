# gigahack-bei50

GigaHack Sireț3 vineyard / Marcaj: research, one-shot CVAT 1.1 import, planar measurements in **EPSG:32635**, a closed inspection walk, and a MapLibre viewer.

Deadline: Sunday 27 Sep 2026, 15:00 Chișinău. Marcaj is the scored annotation source.

- Research: [`docs/vineyard-research.md`](docs/vineyard-research.md) (full open-repo catalog: Riseholme / LCAS mapping, GRowSeg, OrthoSeg, ICAERUS, DroneWaste, UOPNOA, YOLO/SAM, GIS, CVAT, routing, MapLibre)
- Weekend runbook: [`docs/vineyard-plan.md`](docs/vineyard-plan.md)

## What this repo is

A usable scaffold plus the evidence pack. It does **not** invent Sireț3 labels. Training uses other public datasets. Manual Sireț3 drawing stays in Marcaj.

```
docs/                 research + plan
processing/           rasterio / geopandas / shapely / NetworkX pipeline
models/               YOLO11 + SAM/SAM2/MobileSAM stubs
web/                  Next.js + MapLibre (port 43173)
data/tiles/           drop 311 siret3_rXXX_cYYY.tif here
route.geojson         closed walk (sample until Marcaj export)
measurements.csv      planar m / m² (sample until Marcaj export)
```

## Install

### Processing

```bash
cd processing
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
siret3 --help
```

Optional OR-Tools routing: `pip install -e ".[route-ortools]"`.

Optional Docker:

```bash
docker build -t siret3-processing .
docker run --rm -v "$PWD:/data" siret3-processing inventory /data/data/tiles --allow-partial --out /data/data/tile_index.csv
```

### Web map

```bash
cd web
npm install
npm run dev
```

Opens [http://127.0.0.1:43173](http://127.0.0.1:43173). Sample layers are synthetic near the Sireț3 bbox. The raster is the public OpenAerialMap XYZ for item `683060c4025981aa411253c8`.

## Repro: model → one import → publish → measure → route → map

1. **Model (H100).** Riseholme COCO [10.5281/zenodo.19234907](https://doi.org/10.5281/zenodo.19234907) (CC-BY-4.0) + DroneWaste [10.5281/zenodo.17045559](https://doi.org/10.5281/zenodo.17045559) (CC-BY-4.0).

   ```bash
   python models/download_riseholme.py
   python models/prepare_riseholme.py
   python models/train_yolo.py --task segment --data datasets/riseholme-yolo/data.yaml --profile h100
   python models/train_yolo.py --task detect --data models/configs/waste.yaml --profile h100

   CPU dry-run on this VM (no GPU):

   python models/make_synth_yolo.py
   python models/train_yolo.py --task segment --data models/configs/synth-vineyard.yaml --profile cpu --epochs 1
   ```

   16 GB: `--profile gpu16` or `HARDWARE_PROFILE=gpu16` (`yolo11s-seg`, imgsz 1024, batch 4).

2. **Infer tiles.**

   ```bash
   python models/infer_yolo.py --weights models/weights/vineyard.pt --tiles data/tiles --out data/predictions
   ```

3. **Stitch IDs and write `team_upload.zip`** (311 original GeoTIFF names, import **once**).

   ```bash
   siret3 inventory data/tiles --out data/tile_index.csv
   python models/infer_yolo.py --weights models/weights/vineyard.pt --tiles data/tiles --out data/predictions
   siret3 stitch data/predictions --tiles data/tiles --out data/stitched.geojson
   siret3 cvat-export data/tiles --geojson data/stitched.geojson --out team_upload.zip
   ```

   Dry-run three tiles before the full zip. Then publish in Marcaj.

4. **Measurements + route** from the Marcaj export (planar EPSG:32635, no DEM).

   ```bash
   siret3 measurements data/stitched.geojson --out measurements.csv
   siret3 route data/stitched.geojson --start 28.71080,47.12140 --out route.geojson
   ```

   Start must snap within 5 m. Walk uses inter-row + authorised passages only.

5. **Web UI.** Refresh the map. Replace `web/public/layers/sample.geojson` and root `route.geojson` with the real export.

## Sireț3 imagery

| | |
| --- | --- |
| OpenAerialMap | [Sireț3 STAC item](https://api.imagery.hotosm.org/stac/collections/openaerialmap/items/683060c4025981aa411253c8) |
| Date | 20 May 2025 |
| GSD | 3.52 cm/px |
| Licence | CC BY 4.0, producer 3DATA COLLECT |
| XYZ | `https://api.imagery.hotosm.org/raster/collections/openaerialmap/items/683060c4025981aa411253c8/tiles/WebMercatorQuad/{z}/{x}/{y}?assets=visual` |

Attribute: 3DATA COLLECT / Open Imagery Network, CC BY 4.0.

## Paid APIs

None required. If you later use Ultralytics Platform, Roboflow train, Replicate, or Hugging Face Inference, list the name and cost here before the pitch.

## Licences we actually touch

- Ultralytics YOLO: AGPL-3.0 (repo is public)
- SAM / SAM2 / MobileSAM: Apache-2.0
- Riseholme COCO (Zenodo): CC-BY-4.0
- DroneWaste dataset: CC-BY-4.0
- Sireț3: CC-BY-4.0

AGRIDS YOLO zip and the Kaggle Riseholme mirror are **NC / ND**. Do not use them.

## Hardware (this VM vs H100)

`models/hardware.py` picks `h100` / `gpu16` / `cpu` from `nvidia-smi` or `HARDWARE_PROFILE`.

This cloud workspace has **no NVIDIA device** (`nvidia-smi` missing, `torch.cuda.is_available() == False`). Nothing in the environment points at a reachable H100 (`GPU_HOST` / `H100` unset). Training here is CPU-only (`yolo11n-seg`, imgsz 640, 1-epoch dry-run). On the user's H100:

```bash
python models/hardware.py
HARDWARE_PROFILE=h100 python models/train_yolo.py --task segment --data datasets/riseholme-yolo/data.yaml --profile h100
```

## Status

- Research catalog is in [`docs/vineyard-research.md`](docs/vineyard-research.md).
- Processing CLI: inventory, stitch (pixel→EPSG:32635, IDs, inter-rows), CVAT 1.1 zip, planar measurements, closed walk.
- Sample COG chips may sit in `data/tiles/` for software tests. The organiser **311** pack is not in git. Do not publish those chips as the scored Marcaj set.
- Weights and dataset zips are gitignored. Riseholme / DroneWaste live under `data/source/` when downloaded.
