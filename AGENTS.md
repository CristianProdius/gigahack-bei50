# Agent notes — gigahack-bei50

GigaHack 2026, Marcaj Vineyard AI Field Challenge, Sireț3. Deadline Sunday 27 Sep 2026, 15:00 Europe/Chisinau. Scored labels live only in Marcaj. This file says where the official files are and what each one is.

**Read these before writing code.** They are the challenge, the scores, and the remaining work. Official PDFs win if a note disagrees.

| File | What it is |
| --- | --- |
| [`docs/challenge.md`](docs/challenge.md) | Official brief: problem, must-haves, Marcaj, submission, rules |
| [`docs/scoring.md`](docs/scoring.md) | 100% score card and how each slice is computed |
| [`docs/annotation-rules.md`](docs/annotation-rules.md) | How to draw every label and attribute |
| [`docs/provider-briefing.md`](docs/provider-briefing.md) | Verbal briefing vs official PDF (PDF wins) |
| [`docs/sota-research.md`](docs/sota-research.md) | Last 3–6 month papers and the locked weekend stack |
| [`docs/must-implement.md`](docs/must-implement.md) | Brief → this repo: gaps, pipeline, checklists |
| [`docs/vineyard-plan.md`](docs/vineyard-plan.md) | Weekend runbook |
| [`docs/vineyard-research.md`](docs/vineyard-research.md) | Open datasets and tools |
| [`docs/siret3-dataset.md`](docs/siret3-dataset.md) | Official Sireț3 imagery card (area, GSD, sensor, licence) |
| [`data/challenge/README.md`](data/challenge/README.md) | Pack file index |

Human README: [`README.md`](README.md).

## Official pack

The Google Drive download is copied to `data/challenge/` (about 1 GB). Tile ZIPs and the source orthomosaic are gitignored. Everything else in that folder is tracked.

| Path | What it is |
| --- | --- |
| `data/challenge/01_tiles/siret3_challenge_tiles_part1of5.zip` … `part5of5.zip` | The 311 challenge tiles. GeoTIFF, EPSG:32635, 0.025 m/px, 2048×2048 px (51.2 m on a side). Five ZIPs, each at most 94 MB (part 5 is ~10 MB). Gitignored. |
| `data/challenge/01_tiles/overview.png` | 1 m/px overview. Challenge tiles outlined in yellow, route START in red. |
| `data/challenge/02_route/start.geojson` | Route start and finish. One Point. EPSG:32635 coordinates 629504.70, 5220250.75. WGS84 47.1230335 N, 28.7073776 E. Falls on tile `siret3_r018_c010.tif`. Dirt-road junction at the north-west corner of the block. |
| `data/challenge/02_route/passages.geojson` | Authorised passages (roads, tracks, headlands). One MultiPolygon, `type` = `passage`. OSM highways buffered, plus five passages digitised from the orthomosaic. |
| `data/challenge/02_route/forbidden.geojson` | Forbidden zones (village core, buildings, compounds). One MultiPolygon, `type` = `forbidden`. |
| `data/challenge/02_route/study_area.geojson` | Outline of the 311 tiles. One Polygon. |
| `data/challenge/02_route/preview_passages_forbidden.png` | Picture of passages and forbidden zones. |
| `data/challenge/03_docs/Vineyard_AI_Field_Challenge_description.pdf` | Tasks, submission, rules, judging. |
| `data/challenge/03_docs/Vineyard_AI_annotation_rules.pdf` | Labels, attributes, and worked cases. Read this before changing the CVAT writer. |
| `data/challenge/03_docs/Marcaj_quick_start_for_teams.pdf` | Sign in, build and upload ZIPs, publish, correct, submit. |
| `data/challenge/03_docs/Marcaj_Siret3_Dataset_Brief_EN.pdf` | Organising-committee imagery card: 145 ha, 3.52 cm/px, Mavic 3E, 658.6 MB source. Transcribed in [`docs/siret3-dataset.md`](docs/siret3-dataset.md). |
| `data/challenge/04_source/siret3_source_orthomosaic_EPSG4326.tif` | Full original orthomosaic, **658.6 MB** (brief), EPSG:4326, as published on OpenAerialMap. Whole-survey training only. Gitignored. |
| `data/challenge/05_examples/siret3_examples_cvat.zip` | Two example tiles in CVAT for images 1.1 (`annotations.xml` + `images/`). Same format as the upload. Not scored. |
| `data/challenge/05_examples/preview_siret3_r021_c012.jpg` | Block `V01`: 25 rows, all `regular`, 399 canopies, 24 inter-rows, all `bare_soil`. Young vines on tilled soil, one polygon per plant. |
| `data/challenge/05_examples/preview_siret3_r006_c004.jpg` | Block `V02`: 26 rows, 5 `disrupted`, 251 canopies, 25 inter-rows (21 `bare_soil`, 4 `mixed`). Grass strips. White vine tubes and stakes are not waste. |

Every GeoJSON in `02_route/` declares CRS `EPSG:32635` (WGS 84 / UTM 35N, metres).

Imagery licence: CC BY 4.0, credit 3DATA COLLECT / OpenAerialMap. Route data includes OpenStreetMap, ODbL.

## How to use the tiles

Unzip into `data/tiles/` (those `.tif` files are gitignored) before `siret3 inventory`:

```bash
unzip 'data/challenge/01_tiles/siret3_challenge_tiles_part*.zip' -d data/tiles
```

Pack model output as CVAT for images 1.1: `annotations.xml` plus `images/` with the tiles unchanged and under their original names. At most 90 MB per ZIP. Uploading one ZIP per official part is enough. Upload all five parts, confirm 311 files, then publish. Pre-annotations cannot be imported after publishing. Correct in Marcaj and submit every job before 15:00 Sunday 27 September.

Scoring uses a hidden subset. Annotate all 311 tiles.

## Label schema (from the example ZIP)

The example `annotations.xml` is the schema to match. `processing/src/siret3/cvat11.py` now writes these official enums (not the old `trellis` / `guyot` / `grass` stub).

| Label | Geometry | Attributes |
| --- | --- | --- |
| `vineyard` | polygon | `vineyard_id` |
| `waste` | rectangle | `vineyard_id` |
| `row` | polyline | `vineyard_id`, `row_id`, `row_structure` = `regular` / `disrupted` / `unassessable` |
| `interrow_area` | polygon | `vineyard_id`, `interrow_cover` = `bare_soil` / `vegetation` / `mixed` / `unassessable` |

Example images inside the zip: `siret3_r021_c012.tif`, `siret3_r006_c004.tif`, both 2048×2048.

## Repo map

| Path | What |
| --- | --- |
| `processing/` | `siret3` CLI: inventory, stitch (derive rows/IDs), CVAT 1.1 export, inspect, measurements, closed route. |
| `models/` | YOLO11m-seg canopy + YOLO12 waste. Train on Riseholme / DroneWaste only. Infer: `models/infer_yolo.py`. |
| `web/` | Next.js + MapLibre on port 43173. Sample layers are synthetic until the Marcaj export. |
| `route.geojson`, `route_farmer.geojson`, `measurements.csv` | Inspector (25%) + farmer (waste-only) + jury CSV. Samples until rebuilt from the Marcaj export. |
| `data/tiles/` | 311 unzipped challenge tiles (local, gitignored). |
| `models/weights/` | Gitignored. Local `vineyard.pt` (43 MB, copied from H100 25 Sep). `waste.pt` after train. |

GitHub (live): [CristianProdius/bei50](https://github.com/CristianProdius/bei50). Do not use the leftover public starter `cristian-frunze/gigahack-bei50` (no admin from this machine).

## Weekend state (2026-09-26 01:10)

Deadline Sunday 27 Sep 2026, 15:00 Europe/Chisinau. Locked stack: public-data train → GIS derive → one Marcaj import → hand-correct. Do not label Sireț3 outside Marcaj. H100 is free.

### Done in code (43→44 tests in `processing/`)

- Parse official example CVAT; pixel ↔ EPSG:32635 (`cvat_parse.py`, `georef.py`).
- Derive rows / inter-rows / IDs / attributes from **one polygon per plant** (`derive.py`, `ids.py`). Gold on examples: V01 25 rows / 399 plants, V02 26 rows / 251 plants. `row_structure` from ≥ 5 m along-row gap. `interrow_cover` from ExG when `--tiles` is set.
- Block IDs `V01`…; row IDs `V01-R01`…; roads split blocks. Official `passages.geojson` holes are kept so vineyard interiors are not treated as road. `join_m` default 6.0 (5.0 split V02 on the examples).
- Five-part CVAT ZIPs, original TIFF names, official enums, hard fail at 90 MB (`cvat11.py`).
- `siret3 inspect`: gap midpoints `INS-{row_id}-{n}` (not a Marcaj label).
- `siret3 measurements`: union canopy / inter-row m²+ha, `n_blocks`, `n_rows`, stitched row length.
- `siret3 route`: closed LineString **EPSG:32635**, official start 629504.70, 5220250.75 ± 5 m, passable = inter-row ∪ passages − forbidden (holes kept), fail if > 2% length illegal. One Feature only (`length_m` + `start_x`/`start_y` properties). **26 Sep: two walks required** — inspector `route.geojson` (gaps + waste, `--targets inspections,waste`, the 25% file) and farmer `route_farmer.geojson` (waste only, `--targets waste`).
- Spec/plan: `docs/superpowers/specs/2026-09-25-closed-route-design.md`, `docs/superpowers/plans/2026-09-25-closed-route.md`.

### Models / GPU (`ssh gpu-server`, `/home/prodius/projects/bei50`)

- Canopy **YOLO11m-seg** on Riseholme: done. Local `models/weights/vineyard.pt`. Classes: vineyard / vine_row / pole / trunk. Remote val mAP50 ~0.73. On Sireț3 (imgsz 1280, conf 0.25) it fired **0 plant `vineyard` masks** — 113 `vine_row` strips after dropping poles/trunks. `project.py` remaps `vine_row` → vineyard polygons; `derive` takes the major-axis as the row.
- Waste **YOLO12m detect** on DroneWaste: **60 / 60 epochs done**. Last val mAP50 **0.394**. `best.pt` copied to `models/weights/waste.pt` (remote + local). Infer at `--conf 0.4` → **60 boxes on 39 tiles**.
- `infer_311.sh` finished 26 Sep ~01:05: 311 canopy + 311 waste GeoJSON. H100 idle.

### Still to do (score-critical)

1. **Marcaj (human):** published pack is `data/cvat_zips_plants/`. Empty tiles → No objects. Correct plants/rows/inter-rows/IDs, **submit every job**.
2. After export: `siret3 marcaj-import` (do **not** stitch/re-derive) → `measurements.csv` + inspector `route.geojson` + farmer `route_farmer.geojson` + `siret3 web-layers`.
3. README: weight URL, 311-tile time, hardware, deployed UI link.

Known leftovers: inter-row corridors can still miss hand-drawn holes; targets > 2 m from passable are dropped. Route now defaults `--passages` / `--forbidden` to `data/challenge/02_route/` when those files exist.

### After Marcaj export

```bash
siret3 marcaj-import data/marcaj_export --tiles data/tiles --out data/marcaj_32635.geojson
siret3 inspect data/marcaj_32635.geojson --out inspections.geojson
siret3 measurements data/marcaj_32635.geojson --out measurements.csv
siret3 route data/marcaj_32635.geojson --targets inspections,waste --out route.geojson
siret3 route data/marcaj_32635.geojson --targets waste --out route_farmer.geojson
siret3 web-layers --layers data/marcaj_32635.geojson \
  --inspector route.geojson --farmer route_farmer.geojson \
  --measurements measurements.csv --inspections inspections.geojson \
  --forbidden data/challenge/02_route/forbidden.geojson \
  --passages data/challenge/02_route/passages.geojson \
  --out-dir web/public/layers
```

### Commands

```bash
# after waste train exits (script refuses if train_yolo detect is still up)
ssh gpu-server 'bash /home/prodius/projects/bei50/models/remote/infer_311.sh'

siret3 project data/predictions data/predictions_waste --tiles data/tiles --out data/predictions_32635.geojson
siret3 stitch data/predictions_32635.geojson --tiles data/tiles --passages data/challenge/02_route/passages.geojson --out data/stitched.geojson
siret3 cvat-export data/tiles --shapes data/stitched.geojson --parts data/challenge/01_tiles --out-dir data/cvat_zips
siret3 inspect data/stitched.geojson --out inspections.geojson
siret3 measurements data/stitched.geojson --out measurements.csv
siret3 route data/stitched.geojson --targets inspections,waste \
  --start-file data/challenge/02_route/start.geojson \
  --passages data/challenge/02_route/passages.geojson \
  --forbidden data/challenge/02_route/forbidden.geojson \
  --out route.geojson
siret3 route data/stitched.geojson --targets waste \
  --start-file data/challenge/02_route/start.geojson \
  --passages data/challenge/02_route/passages.geojson \
  --forbidden data/challenge/02_route/forbidden.geojson \
  --out route_farmer.geojson
```

`siret3 project` turns per-tile pixel GeoJSON into one EPSG:32635 FeatureCollection (one affine open per tile). CVAT part ZIPs store GeoTIFFs uncompressed (`ZIP_STORED`) and deflate XML only. Shaped export 26 Sep 01:10 (113 vine_row + 113 rows + 38 inter-rows + 60 waste): part1 89.523, part2 89.323, part3 88.910, part4 **89.782**, part5 9.949 MiB — all under 90 MiB (94,371,840). Part 4 has ~0.22 MiB headroom.

Marcaj (human): correct + submit every job. Pack that was published: `data/cvat_zips_plants/`. Agents cannot click Marcaj. After export, `siret3 marcaj-import` then measurements / both routes / `web-layers`.

## Do not

- Draw Sireț3 labels anywhere except Marcaj.
- Use AGRIDS or the Kaggle Riseholme mirror (NC / ND).
- Commit `data/challenge/01_tiles/*.zip`, `data/challenge/04_source/*.tif`, `data/tiles/*.tif`, or extra checkpoints (`vineyard_siret3.pt`). Tracked weights are `models/weights/vineyard.pt` and `waste.pt`.
- Treat the root `route.geojson` start as official. The official start is `data/challenge/02_route/start.geojson`.
- Start a second H100 job if someone else is already on the card (check `nvidia-smi` first).
- Merge `origin/frontend` into `main`. That branch is an **unrelated-history orphan** (repo-root Next on :3000, SVG DEMO DATA). A merge overwrites `web/`, `processing/`, and the official pack. The scored UI is [`web/`](web/) on `main` (MapLibre, :43173). Copy IA onto `web/` only. A GitHub Action fails PRs from `frontend` → `main`.
