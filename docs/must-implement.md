# What this repo must implement

Maps the official brief ([`challenge.md`](challenge.md)) and score card ([`scoring.md`](scoring.md)) onto **this** codebase. Use this file when you pick the next coding task. Do not invent extra products. What to train: [`sota-research.md`](sota-research.md). Verbal briefing vs PDF: [`provider-briefing.md`](provider-briefing.md).

**Deadline:** Sunday 27 Sep 2026, 15:00 Europe/Chisinau.

**Admission (binary):** published Marcaj + all jobs submitted + `route.geojson` + `route_farmer.geojson` / `measurements.csv` in the required formats + working web UI (both walks).

---

## Deliverable matrix

| Official must-have | Score | Repo surface today | Still to build |
| --- | --- | --- | --- |
| Per-plant `vineyard` polygons | 25% canopy | YOLO-seg stub `models/train_yolo.py`, `models/infer_yolo.py` | Train YOLO11m-seg on Riseholme (optional YOLO26-seg / RF-DETR-Seg A/B). Infer 311 tiles, split touching canopies, no labels on empty tiles. See [`sota-research.md`](sota-research.md). |
| `waste` boxes | 10% | YOLO-det stub + `models/configs/waste.yaml` | Train YOLO12/26 detect on DroneWaste, one class, high precision, drop tubes/stakes |
| `row` polylines + `row_id` | 8% of 15% axes | `processing/src/siret3/ids.py` stitch stub | Derive axes from canopies / GRowSeg / LCAS helpers; one line per row per tile through gaps |
| `row_structure` | part of 5% attributes | Wrong enums in `cvat11.py` | Gap ≥ 5 m → `disrupted`; else `regular` / `unassessable` |
| `interrow_area` polygons | used by route + 2% area | Not derived | Canopy-edge corridors, no overlap with canopies, clip to row ends |
| `interrow_cover` | part of 5% attributes | Wrong enums in `cvat11.py` | Colour / vegetation fraction → `bare_soil` / `vegetation` / `mixed` / `unassessable` |
| `vineyard_id` grouping | 2% + count 2% | ID stitch stub | Connected plantings; road/track splits; same ID across tiles; waste within 10 m |
| Inspection locations | feed 15% route coverage | Missing | Gaps / missing planting: `id`, x/y in 32635, `vineyard_id`, `row_id`. **Not** a Marcaj label |
| Counts + measurements | 10% (from Marcaj) | `siret3 measurements` writes a sample schema | Union canopy area, ha + m², per-`row_id` lengths, block/row counts. Jury also sees the CSV |
| Marcaj import | admission | `siret3 cvat-export` | Fix label XML to official enums; 5 ZIPs ≤ 90 MB; original TIFF names |
| Walking routes (two) | 25% on inspector file | `siret3 route` + sample 4326 geojson | **Inspector** `route.geojson`: legal graph; visit waste + inspections within 2 m; closed at official start ± 5 m; `length_m`; EPSG:32635. **Farmer** `route_farmer.geojson`: same graph/start, waste only. Web: blue + red. |
| Web interface | admission + 15% engineering | Next.js MapLibre on :43173, synthetic layers | Real layers: blocks, rows, inter-rows, waste, inspections, **both** routes, lengths, counts |
| README repro + weights + timing | 15% engineering | Scaffold README | Pins, Dockerfile (exists), weight URL, 311-tile wall time + hardware, paid APIs, deployed UI link |

---

## Submission files (repo root)

Must match the brief **exactly** at freeze.

### `route.geojson` (inspector — the 25% file)

- One **LineString**. Do not put the farmer walk in this file.
- Coordinates **EPSG:32635** (metres), not lon/lat. Current sample is EPSG:4326 and **wrong for submission**.
- First and last vertex within **5 m** of `data/challenge/02_route/start.geojson` (629504.70, 5220250.75).
- Property `length_m` (planar). Optional `role=inspector`.
- Targets = gap / missing-planting midpoints **and** waste.
- ≤ 2% of length outside passable inter-rows ∪ authorised passages, or this whole 25% is zero.

### `route_farmer.geojson` (farmer — required, not the 25% source)

- Same schema as the inspector file: one LineString, EPSG:32635, `length_m`, closed at official start ± 5 m, legal graph.
- Targets = **waste only**.
- Property `role=farmer`.
- Show on the web in red. Same instant-0 hygiene (illegal / not closed) so a juror can trust it.

### `measurements.csv`

Must let a juror read, per `vineyard_id` / `row_id`:

- block count (distinct `vineyard_id`)
- row count (distinct `row_id`)
- individual and total row lengths (m)
- canopy area (union, m² and ha)
- inter-row area (m² and ha)

Scaffold columns today: `kind,id,vineyard_id,area_m2,length_m,n_parts,tile_names,centroid_x,centroid_y`. Extend; do not drop the official numbers. Organizers **recompute** the 10% from Marcaj, but the CSV is shown.

### `README.md`

Install → tiles → model → CVAT ZIPs → Marcaj note → export → `measurements.csv` + `route.geojson` + `route_farmer.geojson`. Pinned deps. Dockerfile plus. Weight URL. Full-set time + hardware. Paid APIs/LLMs. Web URL.

### Weights

Link or reproducible command. Not in git (`models/weights/`).

---

## Pipeline the code must actually run

```
data/challenge/01_tiles/*.zip
        │ unzip
        ▼
data/tiles/*.tif  (311)
        │ models/infer_yolo.py + row/interrow GIS
        ▼
data/predictions/  (per-tile geometry, pixel + 32635)
        │ siret3 stitch  (vineyard_id / row_id across tiles)
        ▼
data/stitched.geojson
        │ siret3 cvat-export  (official enums, 5× ≤90 MB)
        ▼
Marcaj  (import → check 311 → publish → correct → submit every job)
        │ team export (json_simple or CVAT XML)
        ▼
siret3 measurements  →  measurements.csv
siret3 inspect       →  inspections.geojson   (gaps; waste stays on stitched features)
siret3 route --targets inspections,waste →  route.geojson         (inspector, 25%)
siret3 route --targets waste             →  route_farmer.geojson  (farmer)
        │
        ▼
web/  layers + counts + lengths
```

`siret3 inspect` exists. Route must consume official start, passages, forbidden, and emit **both** walks.

---

## Implementation checklist (agents)

### A. Do not lose the 50% that is geometry-in-Marcaj

- [ ] Fix `processing/src/siret3/cvat11.py` to official labels/enums (`rectangle` not `bbox`; `regular`/`disrupted`/`unassessable`; `bare_soil`/`vegetation`/`mixed`/`unassessable`)
- [ ] Inventory 311 names `siret3_rXXX_cYYY.tif`
- [ ] Infer canopies; split at 1.0–1.5 m when fused
- [ ] Infer waste; high precision
- [ ] Build row axes through gaps; `row_structure` from ≥ 5 m gaps
- [ ] Build inter-row polygons from canopy edges; `interrow_cover` from vegetation fraction
- [ ] Stitch IDs; road/track splits blocks; waste inherits nearest block ≤ 10 m
- [ ] Write five CVAT ZIPs; dry-run the example tiles first
- [ ] Publish only at 311 files; submit every job

### B. Do not lose the 25% route

- [ ] Parse `start.geojson`, `passages.geojson`, `forbidden.geojson`
- [ ] Passable = inter-row ∪ passages − forbidden − canopy
- [ ] Inspector targets = waste centroids + gap/missing-planting points (`id`, coords, `vineyard_id`, `row_id`)
- [ ] Farmer targets = waste centroids only
- [ ] Both: closed walk, start snap ≤ 5 m, visit within 2 m, minimise length after coverage
- [ ] Reject (fail loud) if &gt; 2% length is illegal
- [ ] Write `route.geojson` (inspector) and `route_farmer.geojson` (farmer), each one LineString in **EPSG:32635** with `length_m`

### C. Do not lose the 10% measurements + jury CSV

- [ ] From Marcaj export (not raw model) compute union canopy area, inter-row area, per-row length, distinct IDs
- [ ] Report m² and ha
- [ ] Keep `measurements.csv` at repo root

### D. Do not lose admission + 15% engineering

- [ ] Web: official start, real layers, IDs, areas, row lengths, totals, **blue inspector + red farmer** polylines + each `length_m`
- [ ] README: repro, weights, time, hardware, API list, UI link
- [ ] Dockerfile stays working
- [ ] Sample layers stay marked SAMPLE until replaced

---

## Hard constraints (never “fix later”)

- Manual Sireț3 labels: **Marcaj only**.
- Do not use AGRIDS or the Kaggle Riseholme mirror (NC / ND).
- Do not commit tile ZIPs, source ortho, unzipped tiles, or weights.
- Do not treat root sample `route.geojson` as official (wrong CRS and start).
- Do not publish Marcaj before all five parts are in.
- Do not send a job back near the deadline and leave it unsubmitted.

## Official PDFs (if these notes and the PDF disagree, the PDF wins)

- `data/challenge/03_docs/Vineyard_AI_Field_Challenge_description.pdf`
- `data/challenge/03_docs/Vineyard_AI_annotation_rules.pdf`
- `data/challenge/03_docs/Marcaj_quick_start_for_teams.pdf`
- `data/challenge/03_docs/Marcaj_Siret3_Dataset_Brief_EN.pdf` (imagery card; [`siret3-dataset.md`](siret3-dataset.md))
