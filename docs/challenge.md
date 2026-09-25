# Vineyard AI Field Challenge — official brief

Source of truth for **what this repo must ship**. Transcribed from `data/challenge/03_docs/Vineyard_AI_Field_Challenge_description.pdf` (Deeptech GigaHack 2026, Marcaj, 25–27 September 2026). Scoring lives in [`scoring.md`](scoring.md). How to draw labels lives in [`annotation-rules.md`](annotation-rules.md). What is still missing in this repo lives in [`must-implement.md`](must-implement.md).

**Deadline:** 15:00 Sunday 27 September 2026, Europe/Chisinau. Repository link **and** Marcaj project. Marcaj is frozen at the deadline; organizers export annotations.

**Prize:** MDL 30,000 cash, one winning team.

**Admission (must pass or you are not scored):** working web interface, published Marcaj project with submitted jobs, correct formats and georeferencing.

---

## Problem

Vineyard operators need maps of planting, row structure, visible waste, and locations that need inspection. Aerial images alone do not give measured areas or an efficient walk through the planting.

Moldova agriculture ministry estimate for 2026 vineyard maintenance: MDL 52,000–80,000 per hectare (including depreciation). A 20 ha holding: MDL 1.04–1.60 million per year.

Expected benefit: less preparation and walking time while covering the planting, including subsidy-area audits. Example: shorten 6 km to 4.2 km = 30% less walking, 27 minutes at 4 km/h.

## Challenge brief

Build an end-to-end application that turns **Sireț3** (open, unannotated RGB orthomosaic, Moldova) into an annotated vineyard map and a walking route that can be used in the field.

Allowed approach: train or adapt models on open labelled vineyard datasets, mix AI/ML with classical CV and GIS post-processing, import pre-annotations into Marcaj, correct by hand there.

Final deliverable = neural-network model + Marcaj annotations + measurements + route + working web interface.

## Must-have features

| # | Feature | What “done” means for scoring |
| --- | --- | --- |
| 1 | **Canopies** | Segment top-down grapevine canopies as polygons, label `vineyard`. Exclude inter-row ground. Split adjoining canopies so individual vines can be counted. |
| 2 | **Waste** | Axis-aligned boxes, label `waste`, on vineyard land and the surrounding zone. Separate boxes for distinguishable items; one box for an inseparable cluster. Box area is **not** waste area. |
| 3 | **Row axes** | One polyline per vine-row axis, label `row`, attribute `row_id`. Do **not** annotate inter-row axes. Gaps do **not** create new row IDs. |
| 4 | **Inter-row areas** | Polygons, label `interrow_area`: ground between canopies of adjacent rows. Exclude canopies, roads, headlands, exterior land. No overlap with canopy polygons. |
| 5 | **Attributes** | `row_structure` = `regular` / `disrupted` / `unassessable`. `interrow_cover` = `bare_soil` / `vegetation` / `mixed` / `unassessable`. If you cannot tell, use `unassessable` — it is scored like any other answer. |
| 6 | **Blocks** | Every object has `vineyard_id`. A block is a connected planting. Same ID across tile edges. Remove duplicates. |
| 7 | **Inspection locations** | Visible row gaps / missing planting, each with an ID, coordinates, and links to `vineyard_id` / `row_id`. Together with waste, these are the **route targets**. They go in the **application output**, not into Marcaj. |
| 8 | **Counts and measurements** | Unique blocks and rows. Individual and total row lengths. Canopy area = union of canopy polygons. Inter-row area. Areas in m² **and** hectares, lengths in metres, **EPSG:32635**, horizontal only (no DEM). |
| 9 | **Annotation in Marcaj** | Upload supplied tiles + AI pre-annotations. Correct geometry and attributes **only** in Marcaj. |
| 10 | **Walking route** | From the official start, visit inspection + waste targets, stay on passable inter-rows + authorised passages, never through canopies / fences / forbidden zones, minimise length, **return to start**. |
| 11 | **Web interface** | Routes as polylines with lengths; `vineyard_id` / `row_id`; canopy and inter-row areas; block and row counts; individual and total row lengths. |
| 12 | **Submission** | Georeferenced route, measurement tables, application and processing code, repro instructions, model weights or a way to obtain them. Annotations are taken from Marcaj, not from a file we upload at the deadline. |

## Annotation conventions (names must match exactly)

| Object | Label | Geometry | Attributes |
| --- | --- | --- | --- |
| Grapevine canopy | `vineyard` | polygon | `vineyard_id` |
| Waste | `waste` | bounding box | `vineyard_id` |
| Vine-row axis | `row` | polyline | `vineyard_id`, `row_id`, `row_structure` |
| Inter-row area | `interrow_area` | polygon | `vineyard_id`, `interrow_cover` |

`row_structure` = `regular` / `disrupted` / `unassessable`

`interrow_cover` = `bare_soil` / `vegetation` / `mixed` / `unassessable`

Full drawing rules: [`annotation-rules.md`](annotation-rules.md) and `data/challenge/03_docs/Vineyard_AI_annotation_rules.pdf`.

## Technical stack (expected)

- Any stack.
- Georeferenced GeoTIFF, spatial processing, machine-readable geometry and measurement exports.
- **All submitted geometries, the route, and measurement tables are EPSG:32635.** GeoJSON coordinates in that system (metres, UTM 35N).
- Suggested interchange: GeoJSON, CSV/JSON, CVAT for images 1.1 for Marcaj import.
- AI/ML: any segmentation, detection, line extraction, classification, including classical CV.
- Backend: spatial post-processing and route optimisation.
- Frontend: interactive web map plus measurement and route views.
- Manual Sireț3 labels: Marcaj only. Converters are allowed.

## Data

Primary: Sireț3 / Siret3, OpenAerialMap, 3DATA COLLECT. Unannotated RGB GeoTIFF orthomosaic, 20 May 2025, UAV, 3.52 cm/px, ~145 ha. Challenge tiles are that mosaic reprojected to EPSG:32635 and cut. CC BY 4.0.

Suggested open training data (verify licences):

- Riseholme: 855 UAV RGB images, 40,215 COCO segmentations (canopy and row).
- UOPNOA: ~34,000 RGB aerial images and land-use masks. Vineyard-block labels are **not** individual-canopy ground truth.
- DroneWaste: open aerial waste boxes.

Adapt for scale, season, and appearance.

### Assets (already in `data/challenge/`)

| Material | Format | Path |
| --- | --- | --- |
| 311 study-area tiles | GeoTIFF, EPSG:32635, five ZIPs | `data/challenge/01_tiles/` |
| Starting point | GeoJSON Point, EPSG:32635 | `data/challenge/02_route/start.geojson` |
| Passages and forbidden | GeoJSON MultiPolygon, `type` = `passage` / `forbidden` | `data/challenge/02_route/` |
| Annotation rules | PDF | `data/challenge/03_docs/Vineyard_AI_annotation_rules.pdf` |
| Example tiles (not scored) + upload template | CVAT 1.1 | `data/challenge/05_examples/` |
| Marcaj quick start | PDF | `data/challenge/03_docs/Marcaj_quick_start_for_teams.pdf` |
| Full source orthomosaic | GeoTIFF, EPSG:4326 | `data/challenge/04_source/` |

Official start: X 629504.70, Y 5220250.75 (47.1230335 N, 28.7073776 E), tile `siret3_r018_c010.tif`.

## Working in Marcaj

Accounts are emailed Friday evening. One project per team, labels already configured. Anyone on the team can import, annotate, review, export.

Upload CVAT for images 1.1:

```
team_upload.zip
├── annotations.xml     model pre-annotations
└── images/
    └── siret3_r012_c034.tif … supplied tiles, unchanged names
```

Tiles only (no `annotations.xml`) is allowed if there is no model yet. JPEG/PNG are rejected (no georeferencing).

Hard rules:

1. Pre-annotations import **only before publish**, and **only together with the tiles**.
2. Finish the model, import **once**, then publish. Until publish you may delete files and import again.
3. Upload **all 311 tiles unchanged**. Missing tile = unannotated. After publish: do not delete/add tiles, do not change labels.
4. **Only submitted jobs are scored.** Unsubmitted frames = unannotated. Unpublished project = no jobs.
5. Upload **all five parts**, confirm 311 files, **then** publish.
6. Agree IDs before splitting work. A block or row that crosses a tile edge keeps one `vineyard_id` / `row_id`.

Quick start: `data/challenge/03_docs/Marcaj_quick_start_for_teams.pdf`.

## Submission (repo root)

Single repository link. Root **must** contain:

| File | Requirement |
| --- | --- |
| `route.geojson` | One **LineString in EPSG:32635** that starts and ends at the official start (5 m tolerance), property `length_m`. |
| `measurements.csv` | Block and row counts, row lengths and areas by `vineyard_id` / `row_id`. |
| `README.md` | Install and run from supplied tiles → `route.geojson` + `measurements.csv`. Pinned dependencies (Dockerfile is a plus). Where to get weights. Full-tile-set processing time and hardware. Any paid APIs or LLMs. Link to the working web interface. |
| Code | Application + processing. Weights or a reproducible download. |

Annotations are **not** submitted as a file. Organizers export Marcaj at 15:00.

## Rules

- No compute provided. Own laptops or cloud. No model-size limit. Weights may be a link.
- Allowed: open pretrained models (SAM, YOLO, …), open datasets with verified licences, libraries, classical CV. Paid APIs / LLMs if reproducible and listed in the README.
- Sireț3 drawing: Marcaj only. Other data for training: unrestricted. You may retile the ortho for training; submission annotations are on the **supplied** tiles.
- Not allowed: another team’s annotations.
- Pitch: 5 min + 5 min questions. Show the working web interface (map, objects, IDs, measurements, route). Laptop demo is accepted; deployed URL goes in the README.
- Support: GigaHack Slack challenge channel, Marcaj team 09:00–23:00. Pinned clarifications apply to all teams.

## Current repo gaps vs this brief

The scaffold still has a **sample** `route.geojson` in EPSG:4326 (not 32635) and a **sample** `measurements.csv`. The CVAT writer still emits old attribute values. Inspection-target export is not built. See [`must-implement.md`](must-implement.md).
