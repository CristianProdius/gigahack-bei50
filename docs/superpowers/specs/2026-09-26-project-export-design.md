# Project, ZIP cap, two walks, infer

**Date:** 2026-09-26  
**Status:** Approved via attached pipeline plan.

## Problem

Infer writes per-tile **pixel** GeoJSON. Stitch expects one EPSG:32635 FeatureCollection. Official part-4 TIFFs sit near 90 MB. The challenge now requires **two** closed walks. Waste train holds the H100.

## Design

**Project.** `siret3 project` reads one or more files/dirs of pixel GeoJSON, opens each tile **once**, applies the GeoTIFF affine, writes one FeatureCollection CRS EPSG:32635. Preserve `kind`, `tile`, `score`.

**ZIP.** `build_team_upload_zip` stores GeoTIFFs with `ZIP_STORED` and deflates `annotations.xml` only. Still fail if any part `>= 90 MB`.

**Two walks.** `siret3 route --targets inspections,waste` (default) → `route.geojson` (inspector, 25%). `--targets waste` → `route_farmer.geojson`. Same legal graph and official start. Writer stays one LineString; `role` property.

**Infer.** `models/remote/infer_311.sh` runs only when no waste `train_yolo.py` is alive. Copies `best.pt` → `waste.pt`, infers canopy then waste.

**Web.** Main `web/` loads official start (28.7073776, 47.1230335), measurements summary, blue inspector + red farmer. SAMPLE badge until real files replace layers.

## Out of scope

Mobbin, merging `frontend`, Marcaj click-ops (human), retraining.
