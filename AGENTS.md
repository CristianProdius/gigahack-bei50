# Agent notes — gigahack-bei50

GigaHack 2026, Marcaj Vineyard AI Field Challenge, Sireț3. Deadline Sunday 27 Sep 2026, 15:00 Europe/Chisinau. Scored labels live only in Marcaj. This file says where the official files are and what each one is.

**Read these before writing code.** They are the challenge, the scores, and the remaining work. Official PDFs win if a note disagrees.

| File | What it is |
| --- | --- |
| [`docs/challenge.md`](docs/challenge.md) | Official brief: problem, must-haves, Marcaj, submission, rules |
| [`docs/scoring.md`](docs/scoring.md) | 100% score card and how each slice is computed |
| [`docs/annotation-rules.md`](docs/annotation-rules.md) | How to draw every label and attribute |
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

The example `annotations.xml` is the schema to match. The stub in `processing/src/siret3/cvat11.py` still lists older select values (`trellis` / `guyot`, `grass` / `soil` / `cover_crop`). Do not copy those into an upload.

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
| `processing/` | `siret3` CLI: inventory, stitch, CVAT export, planar measurements, closed route. |
| `models/` | YOLO11 and SAM stubs. Train on Riseholme and DroneWaste, not on Sireț3 labels drawn outside Marcaj. |
| `web/` | Next.js + MapLibre on port 43173. Sample layers are synthetic until the Marcaj export. |
| `route.geojson`, `measurements.csv` | Sample until replaced by the Marcaj export. |
| `data/tiles/` | Unzipped challenge tiles. Empty in git. |

## Do not

- Draw Sireț3 labels anywhere except Marcaj.
- Use AGRIDS or the Kaggle Riseholme mirror (NC / ND).
- Commit `data/challenge/01_tiles/*.zip`, `data/challenge/04_source/*.tif`, `data/tiles/*.tif`, or `models/weights/`.
- Treat the root `route.geojson` start as official. The official start is `data/challenge/02_route/start.geojson`.
