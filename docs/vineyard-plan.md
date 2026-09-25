# Sireț3 vineyard map — weekend plan

Turn the Moldova Sireț3 orthomosaic into canopy / waste / row / inter-row annotations, planar measurements, a closed inspection walk, and a web map. **Marcaj is the scored annotation source.** Deadline: Sunday 27 Sep 2026, 15:00 Chișinău.

Official brief, scores, and remaining work: [challenge.md](./challenge.md), [scoring.md](./scoring.md), [annotation-rules.md](./annotation-rules.md), [must-implement.md](./must-implement.md). Provider briefing vs PDF: [provider-briefing.md](./provider-briefing.md). SOTA lock: [sota-research.md](./sota-research.md). Research catalog: [vineyard-research.md](./vineyard-research.md). This file is the weekend runbook.

## Bet

Fine-tune Riseholme COCO on Ultralytics **YOLO11m-seg** (optional A/B: YOLO26-seg or RF-DETR-Seg if the H100 is free) and a single-class waste detector (**YOLO12 or YOLO26**) on DroneWaste. Zero-shot **GRowSeg** as a row prior. **SAM2 box** polish on hard canopies only. Derive rows, inter-rows, 5 m gaps, IDs, ExG cover, and the route with GIS ([LCAS/uav-vineyard-mapping](https://github.com/LCAS/uav-vineyard-mapping) `poles_to_rows.py`, `mid_row_lines.py`). Import **once** into Marcaj with all 311 unchanged GeoTIFFs, then correct by hand. Do not write a new foundation model. Do not label Sireț3 anywhere except Marcaj. Do not train RowDetr, SAM3-as-detector, or ground bunch models. Full lock table: [sota-research.md](./sota-research.md).

## Locked constraints

| Rule | Detail |
| --- | --- |
| Deadline | Sunday 27 Sep 2026, 15:00 Europe/Chisinau |
| Scored labels | vineyard polygon, waste bbox, row polyline, interrow_area polygon |
| Attributes | `vineyard_id`, `row_id`, `row_structure` (`regular` / `disrupted` / `unassessable`), `interrow_cover` (`bare_soil` / `vegetation` / `mixed` / `unassessable`) |
| Import | CVAT 1.1 ZIPs, ≤ 90 MB each, 311 original `.tif` names. Upload all five parts, then publish. |
| CRS | Measurements horizontal in **EPSG:32635**. No DEM / slope correction. |
| Route | Closed walk, start = end, start snap ≤ 5 m, inter-row + authorised passages only, forbidden zones out. Official start: 28.7073776, 47.1230335 (EPSG:32635 X 629504.70, Y 5220250.75), tile `siret3_r018_c010.tif`. |
| Pack | `data/challenge/` — see [`AGENTS.md`](../AGENTS.md) |
| Sireț3 drawing | Marcaj only. Training on other public data is OK. No other team's labels. |
| APIs | Paid APIs allowed if listed in README. Prefer open weights. |

## Hardware

H100 is available. Still ship a 16 GB path so we can recover if the big box is busy.

| Profile | Canopy / rows | Waste | Prompt cleanup | Notes |
| --- | --- | --- | --- | --- |
| H100 (default) | `yolo11m-seg` or `yolo11l-seg`, imgsz 1280, batch 16+ | `yolo11m` detect, imgsz 1280 | SAM2-large on uncertain tiles | Overnight train Fri; Saturday infer 311 |
| 16 GB | `yolo11s-seg`, imgsz 1024, batch 4, AMP | `yolo11s` detect | MobileSAM or skip | Same scripts, `HARDWARE_PROFILE=gpu16` |
| CPU emergency | GRowSeg CPU + classical waste (colour + area) | skip YOLO | none | Only if GPUs die; quality will be weak |

VRAM sketch on 16 GB: YOLO11s-seg ~4–6 GB, leftover for one tile. Sequential, not concurrent. Do not load SAM2-large beside YOLO on 16 GB.

Weights stay on disk under `models/weights/` (gitignored). README links the public checkpoint we actually used.

## Sequence

### 0. Repo and research (this commit)

Docs, Python spatial package, YOLO/SAM stubs, MapLibre scaffold, sample `route.geojson` / `measurements.csv`. Public GitHub: `gigahack-bei50`.

### 1. Friday night / Saturday morning — models

1. Download Riseholme COCO ([10.5281/zenodo.19234907](https://doi.org/10.5281/zenodo.19234907), CC-BY-4.0) and DroneWaste ([10.5281/zenodo.17045559](https://doi.org/10.5281/zenodo.17045559), CC-BY-4.0).
2. Convert Riseholme with Ultralytics `convert_coco(..., use_segments=True)`. Map classes: `vineyard` → canopy, `vine_row` → row mask. Ignore `pole` / `trunk` in the Marcaj export (keep them in the YAML if they help the backbone).
3. Collapse DroneWaste's 20 EWC classes to one `waste` box class.
4. Train on H100 (`models/train_yolo.py`). Keep a `gpu16` command in the README.
5. Optional: run GRowSeg zero-shot on 5 Sireț3 tiles as a row prior (MIT weights; official code is Hugging Face `links-ads/vitigeoss-growseg`).
6. Optional: SAM2 box-prompt polish on low-confidence canopies. MobileSAM on 16 GB. FastSAM lives at `CASIA-LMC-Lab/FastSAM` (AGPL-3.0).
7. Optional GIS: clone `LCAS/uav-vineyard-mapping` (Apache-2.0) for pole→row and mid-row helpers. It does **not** ship YOLO11 weights.

Do **not** train on Sireț3 pixels that we drew ourselves outside Marcaj. Public pretrain only.

### 2. Saturday — one Marcaj import

1. Inventory 311 files: `siret3 inventory data/tiles` → `data/tile_index.csv`. Fail if any name is not `siret3_rXXX_cYYY.tif` or if count ≠ 311.
2. Dry-run export on 3 tiles. Open the XML. Confirm `name=` matches the TIFF file names. Import that mini-zip into a throwaway Marcaj task.
3. Infer all 311. Project to EPSG:32635. Stitch IDs (research §7).
4. Derive inter-row polygons: vineyard outline minus dilated canopies minus a thin row buffer, split by row centreline Voronoi. Set `interrow_cover` only to `bare_soil`, `vegetation`, `mixed`, or `unassessable` (see `data/challenge/05_examples/`).
5. Build CVAT 1.1 ZIPs with **all 311** TIFFs (byte copies) + `annotations.xml`, at most 90 MB each. One ZIP per official tile part is enough.
6. Import once. Check 311 images present. **Publish.** Pre-annotations cannot be imported after publishing.
7. Team-only correction in Marcaj. Agree IDs before anyone splits a vineyard.

If the dry-run import rejects `images/` prefixes or GeoTIFF, fix the writer and repeat the dry-run. Do not publish a 310-file zip.

### 3. Saturday late / Sunday morning — measurements and route

From the **published Marcaj export**, not from raw model output:

1. `siret3 measurements export.xml --out measurements.csv` (planar m² and m in 32635).
2. Build passable graph from inter-row + authorised passages, subtract forbidden zones.
3. Snap official start (≤ 5 m) or fail loud.
4. Closed walk via NetworkX TSP-on-shortest-paths, OR-Tools if the waypoint count blows up.
5. Write `route.geojson` (LineString, start = end).

### 4. Sunday — web UI and freeze

1. Point the MapLibre app at OAM XYZ for Sireț3 plus the GeoJSON layers.
2. Show vineyard IDs, row lengths, areas, waste boxes, route, start marker.
3. Empty / loading / error states already in the scaffold. Wire real files when they exist.
4. README: repro commands, weight URL, H100 vs 16 GB wall times, attribution (3DATA COLLECT, CC BY 4.0; Riseholme; DroneWaste).
5. Stop changing labels after the last Marcaj export we measure.

## Ownership

| Person | Owns |
| --- | --- |
| One | Model train/infer + CVAT writer |
| One | CRS, IDs, measurements, route |
| Everyone else | Marcaj jobs after publish |

Do not split vineyard IDs across annotators without the stitch map.

## Measurements (EPSG:32635)

`measurements.csv` columns (stable):

```
kind,id,vineyard_id,area_m2,length_m,n_parts,tile_names
```

- vineyard / interrow_area: `area_m2` from projected polygon area.
- row: `length_m` from projected LineString length.
- waste: `area_m2` of the projected bbox (axis-aligned in tile pixels, then transformed). Optional.
- No slope, no DSM, no geodesic on 4326.

## Route acceptance

- Geometry type LineString or MultiLineString merged to one ring.
- First point equals last point (or distance < 0.05 m).
- Distance from required start to first vertex ≤ 5 m.
- Every vertex inside passable ∪ 0.25 m tolerance.
- No vertex inside a forbidden zone.

## Web UI

Next.js + MapLibre in `web/`, preview port **43173**.

Layers: Sireț3 XYZ, vineyard fill, rows, inter-rows, waste boxes, route, start. Click a feature → ID + metres from `measurements.csv`.

Sample data in the repo is **synthetic near the Sireț3 bbox**, labelled SAMPLE. Replace with Marcaj export before the pitch.

## Out of scope

- Hospital minutes pipeline.
- Cloud annotation of Sireț3 outside Marcaj.
- Other teams' labels.
- Invented papers or fake LCAS trainers.
- Terrain correction.
- Buying domains, sending mail, or any Ken sales demo work.

## Daily checkpoints

| When | Done means |
| --- | --- |
| Fri EOD | Weights training or GRowSeg dry-run visible; 3-tile XML validates |
| Sat 18:00 | All five parts imported (311 files) and published |
| Sun 12:00 | `measurements.csv` + `route.geojson` + map screenshot |
| Sun 15:00 | Freeze |

If Saturday publish slips, skip GRowSeg polish and SAM. The import is the gate.
