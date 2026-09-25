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
| `data/challenge/04_source/siret3_source_orthomosaic_EPSG4326.tif` | Full original orthomosaic, 628 MB, EPSG:4326, as published on OpenAerialMap. Whole-survey training only. Gitignored. |
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
| `route.geojson`, `measurements.csv` | Sample until rebuilt from the Marcaj export. |
| `data/tiles/` | 311 unzipped challenge tiles (local, gitignored). |
| `models/weights/` | Gitignored. Local `vineyard.pt` (43 MB, copied from H100 25 Sep). `waste.pt` after train. |

GitHub (live): [CristianProdius/bei50](https://github.com/CristianProdius/bei50). Do not use the leftover public starter `cristian-frunze/gigahack-bei50` (no admin from this machine).

## Weekend state (2026-09-25 night)

Deadline Sunday 27 Sep 2026, 15:00 Europe/Chisinau. Locked stack: public-data train → GIS derive → one Marcaj import → hand-correct. Do not label Sireț3 outside Marcaj. Do not start another H100 job until waste train ends.

### Done in code (43→44 tests in `processing/`)

- Parse official example CVAT; pixel ↔ EPSG:32635 (`cvat_parse.py`, `georef.py`).
- Derive rows / inter-rows / IDs / attributes from **one polygon per plant** (`derive.py`, `ids.py`). Gold on examples: V01 25 rows / 399 plants, V02 26 rows / 251 plants. `row_structure` from ≥ 5 m along-row gap. `interrow_cover` from ExG when `--tiles` is set.
- Block IDs `V01`…; row IDs `V01-R01`…; roads split blocks. Official `passages.geojson` holes are kept so vineyard interiors are not treated as road. `join_m` default 6.0 (5.0 split V02 on the examples).
- Five-part CVAT ZIPs, original TIFF names, official enums, hard fail at 90 MB (`cvat11.py`).
- `siret3 inspect`: gap midpoints `INS-{row_id}-{n}` (not a Marcaj label).
- `siret3 measurements`: union canopy / inter-row m²+ha, `n_blocks`, `n_rows`, stitched row length.
- `siret3 route`: closed LineString **EPSG:32635**, official start 629504.70, 5220250.75 ± 5 m, passable = inter-row ∪ passages − forbidden (holes kept), fail if > 2% length illegal. One Feature only (`length_m` + `start_x`/`start_y` properties).
- Spec/plan: `docs/superpowers/specs/2026-09-25-closed-route-design.md`, `docs/superpowers/plans/2026-09-25-closed-route.md`.

### Models / GPU (`ssh gpu-server`, `/home/prodius/projects/bei50`)

- Canopy **YOLO11m-seg** on Riseholme: done. Local `models/weights/vineyard.pt`. Remote val mAP50 ~0.73.
- Waste **YOLO12m detect** on DroneWaste (1 class, 4245 train / 748 val, ~76% empty images, native 640 px, we train imgsz 1280): still running as of ~23:41 local, epoch ~31–33 / 60, mAP50 ~0.27 and still climbing. Published 20-class ceiling is 38.5% (YOLO12x). Only GPU process is `prodius` PID 1070492. Angel is not on the card. Do not start a second job.
- After epoch 60: copy `runs/detect/models/runs/detect-yolo12-h100/weights/best.pt` → `models/weights/waste.pt` (remote + local). Infer waste at `--conf 0.4`.

### Still to do (score-critical)

1. Wait for waste train (~75–90 min from 23:41). Copy `waste.pt`.
2. Infer all 311 tiles on the H100 (faster than this Mac): canopy then waste.
3. `siret3 stitch` + `siret3 cvat-export --parts` → 5 ZIPs ≤ 90 MB. Dry-run part 4 (already 89.75 MiB of TIFFs).
4. Marcaj: upload all five, confirm 311, **publish once**, correct, **submit every job**.
5. Rebuild `route.geojson` + `measurements.csv` from the **Marcaj export**, not raw model output.
6. Web: replace SAMPLE layers; README: weight URL, 311-tile time, hardware.

Known leftovers (do not block infer): inter-row export is exterior-only (can overlap canopy); `legal_path` uses a 0.35 m pad vs 0.05 m score slop; targets > 2 m from passable are dropped; stitch `--tiles` missing → `bare_soil` not `unassessable`; CLI `--passages`/`--forbidden` have no official-pack default.

### Commands

```bash
# after waste.pt exists on gpu-server
ssh gpu-server 'cd /home/prodius/projects/bei50 && .venv/bin/python models/infer_yolo.py --weights models/weights/vineyard.pt --tiles data/tiles --out data/predictions'
ssh gpu-server 'cd /home/prodius/projects/bei50 && .venv/bin/python models/infer_yolo.py --weights models/weights/waste.pt --tiles data/tiles --out data/predictions_waste --conf 0.4'

siret3 stitch data/predictions/merged.geojson --tiles data/tiles --passages data/challenge/02_route/passages.geojson --out data/stitched.geojson
siret3 cvat-export data/tiles --shapes data/stitched.geojson --parts data/challenge/01_tiles --out-dir data/cvat_zips
siret3 inspect data/stitched.geojson --out inspections.geojson
siret3 measurements data/stitched.geojson --out measurements.csv
siret3 route data/stitched.geojson \
  --start-file data/challenge/02_route/start.geojson \
  --passages data/challenge/02_route/passages.geojson \
  --forbidden data/challenge/02_route/forbidden.geojson \
  --out route.geojson
```

Infer writes per-tile GeoJSON in **pixel** space. Project with `georef.pixels_to_xy` and merge into one FeatureCollection before `siret3 stitch` (that glue is not a CLI command yet).

## Do not

- Draw Sireț3 labels anywhere except Marcaj.
- Use AGRIDS or the Kaggle Riseholme mirror (NC / ND).
- Commit `data/challenge/01_tiles/*.zip`, `data/challenge/04_source/*.tif`, `data/tiles/*.tif`, or `models/weights/`.
- Treat the root `route.geojson` start as official. The official start is `data/challenge/02_route/start.geojson`.
- Start another H100 job while waste train holds the card.
