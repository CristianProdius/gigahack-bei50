# Project + export Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Pixel GeoJSON → EPSG:32635, 90 MB-safe part ZIPs, two legal walks, H100 infer script, MapLibre blue/red routes.

**Architecture:** New `project.py` (one affine per tile). ZIP_STORED rasters. `select_waypoints` for inspector vs farmer. Shell gate on GPU train. Web fetches two layer files + measurements + official start.

**Tech Stack:** rasterio, shapely, pytest, Next.js MapLibre.

---

### Task 1: `siret3 project`

- Create: `processing/src/siret3/project.py`, `processing/tests/test_project.py`
- Modify: `processing/src/siret3/georef.py`, `processing/src/siret3/cli.py`

- [ ] Failing tests: pixel (0,0)/(2048,2048) match rasterio bounds; two input files merge; one open per tile.
- [ ] Implement `pixels_to_xy_once` + `project_inputs`.
- [ ] pytest green.

### Task 2: ZIP_STORED tifs

- Modify: `processing/src/siret3/cvat11.py`, `processing/tests/test_cvat_export.py`

- [ ] Assert TIFF entries are `ZIP_STORED`, XML deflated; still fail `>= MAX_ZIP_BYTES`.
- [ ] Dry-run official parts if tiles exist.

### Task 3: `--targets`

- Modify: `processing/src/siret3/inspect.py`, `cli.py`, `route.py`, `processing/tests/test_route.py`

- [ ] Inspector visits gap + waste; farmer visits waste only; both close.

### Task 4: `infer_311.sh`

- Create: `models/remote/infer_311.sh`
- Gate: exit 2 if waste train is running.

### Task 5: Dry-run 5 ZIPs

- Run empty-shape `cvat-export --parts`. Record sizes. Marcaj publish/submit is human.

### Task 6: Web layers

- Modify: `web/src/components/vineyard-map.tsx`, `web/public/layers/`
- Official start WGS84, farmer SAMPLE layer, measurements.csv, blue + red.
