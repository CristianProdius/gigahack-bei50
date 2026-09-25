# gigahack-bei50

GigaHack Sireț3 vineyard / Marcaj: research, one-shot CVAT 1.1 import, planar measurements in **EPSG:32635**, a closed inspection walk, and a MapLibre viewer.

Deadline: Sunday 27 Sep 2026, 15:00 Chișinău. Marcaj is the scored annotation source.

Challenge context (do not lose):

- Official brief + must-haves: [`docs/challenge.md`](docs/challenge.md)
- Score card (25 / 10 / 15 / 10 / 25 / 15): [`docs/scoring.md`](docs/scoring.md)
- How to draw labels: [`docs/annotation-rules.md`](docs/annotation-rules.md)
- Provider briefing vs PDF: [`docs/provider-briefing.md`](docs/provider-briefing.md)
- SOTA lock (what we train): [`docs/sota-research.md`](docs/sota-research.md)
- What this repo still has to build: [`docs/must-implement.md`](docs/must-implement.md)
- Weekend runbook: [`docs/vineyard-plan.md`](docs/vineyard-plan.md)
- Research catalog: [`docs/vineyard-research.md`](docs/vineyard-research.md)
- Agent file index: [`AGENTS.md`](AGENTS.md)

## What this repo is

A usable scaffold plus the evidence pack. It does **not** invent Sireț3 labels. Training uses other public datasets. Manual Sireț3 drawing stays in Marcaj.

```
docs/                 research + plan
data/challenge/       official Marcaj pack (tiles, route, rules, examples, source ortho)
processing/           rasterio / geopandas / shapely / NetworkX pipeline
models/               YOLO11 + SAM/SAM2/MobileSAM stubs
web/                  Next.js + MapLibre (port 43173)
data/tiles/           unzip the 311 siret3_rXXX_cYYY.tif here before inventory
route.geojson         inspector walk: gaps + waste (25% file; sample until Marcaj export)
route_farmer.geojson  farmer walk: waste only (required; generate with the inspector file)
measurements.csv      planar m / m² (sample until Marcaj export)
```

Agent notes: [`AGENTS.md`](AGENTS.md). Pack index: [`data/challenge/README.md`](data/challenge/README.md).

## Official data pack

Copied from the Marcaj Drive download into [`data/challenge/`](data/challenge/). Tile ZIPs and the source orthomosaic stay local (gitignored, about 1 GB). GeoJSON, PDFs, previews, and the example CVAT zip are in the tree.

| Path | What |
| --- | --- |
| `data/challenge/01_tiles/siret3_challenge_tiles_part1of5.zip` … `part5of5.zip` | 311 GeoTIFF tiles, EPSG:32635, 0.025 m/px, 2048×2048 px (51.2 m). Parts are ≤ 90 MB. |
| `data/challenge/01_tiles/overview.png` | 1 m/px overview. Tiles in yellow, route START in red. |
| `data/challenge/02_route/start.geojson` | Start and finish. Point in EPSG:32635: X 629504.70, Y 5220250.75 (47.1230335 N, 28.7073776 E), tile `siret3_r018_c010.tif`. |
| `data/challenge/02_route/passages.geojson` | Authorised passages. MultiPolygon, `type` = `passage`. |
| `data/challenge/02_route/forbidden.geojson` | Forbidden zones. MultiPolygon, `type` = `forbidden`. |
| `data/challenge/02_route/study_area.geojson` | Outline of the 311 tiles. |
| `data/challenge/02_route/preview_passages_forbidden.png` | Preview of passages and forbidden zones. |
| `data/challenge/03_docs/` | Challenge description, annotation rules, Marcaj quick start (PDF). |
| `data/challenge/04_source/siret3_source_orthomosaic_EPSG4326.tif` | Full source orthomosaic, EPSG:4326, as on OpenAerialMap. For whole-survey training only. |
| `data/challenge/05_examples/siret3_examples_cvat.zip` | Two annotated tiles in CVAT for images 1.1. Not scored. |
| `data/challenge/05_examples/preview_siret3_r021_c012.jpg` | Young vines, block `V01`: 25 regular rows, 399 canopies, 24 bare-soil inter-rows. |
| `data/challenge/05_examples/preview_siret3_r006_c004.jpg` | Sparse rows, block `V02`: 26 rows (5 disrupted), 251 canopies, mixed inter-rows. |

Unzip tiles into `data/tiles/` before `siret3 inventory`. Upload pre-annotations as CVAT 1.1 ZIPs of at most 90 MB (one ZIP per part works). All five parts, 311 files, then publish. Pre-annotations cannot be imported after publishing.

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
   python models/train_yolo.py --task segment --data models/configs/vineyard.yaml --profile h100
   python models/train_yolo.py --task detect --data models/configs/waste.yaml --profile h100
   ```

   16 GB: `--profile gpu16` or `HARDWARE_PROFILE=gpu16` (`yolo11s-seg`, imgsz 1024, batch 4).

2. **Infer tiles.**

   ```bash
   python models/infer_yolo.py --weights models/weights/vineyard.pt --tiles data/tiles --out data/predictions
   ```

3. **Stitch IDs and write CVAT 1.1 ZIPs** (311 original GeoTIFF names, ≤ 90 MB each, import **once** before publish).

   ```bash
   siret3 inventory data/tiles --out data/tile_index.csv
   siret3 stitch data/predictions/merged.geojson --out data/stitched.geojson
   siret3 cvat-export data/tiles --out team_upload.zip
   ```

   Dry-run three tiles before the full zip. Then publish in Marcaj.

4. **Measurements + route** from the Marcaj export (planar EPSG:32635, no DEM).

   ```bash
   siret3 measurements data/stitched.geojson --out measurements.csv
   siret3 route data/stitched.geojson --targets inspections,waste --out route.geojson
   siret3 route data/stitched.geojson --targets waste --out route_farmer.geojson
   ```

   Start must snap within 5 m. Both walks use inter-row + authorised passages only. Inspector = 25% file. Farmer = waste collect.

5. **Web UI.** Refresh the map. Replace SAMPLE layers. Show inspector (blue) and farmer (red) with each `length_m`.

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

## Status

Official pack is on disk under `data/challenge/`. Tile ZIPs, the source orthomosaic, weights, and the scored Marcaj dump are not in git. Sample `route.geojson` and `measurements.csv` are still synthetic until the Marcaj export.
