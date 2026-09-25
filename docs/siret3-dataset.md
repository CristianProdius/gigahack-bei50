# Sireț3 dataset brief

Transcribed from `data/challenge/03_docs/Marcaj_Siret3_Dataset_Brief_EN.pdf` (GigaHack 2026 organising committee / dataset brief). This file is **imagery metadata**, not the score card. Tasks and judging stay in [`challenge.md`](challenge.md) and [`scoring.md`](scoring.md). STAC cross-check: [`vineyard-research.md`](vineyard-research.md).

Source metadata on the PDF was checked **17 September 2026**.

## What it is

Open, **unannotated** RGB orthomosaic of a local area in Moldova. Shared geographical workspace for teams. No object labels or segmentation masks come with the imagery. Original survey purpose is not in the public metadata.

Challenge use named on the brief: AI-assisted vineyard and row mapping, manual refinement in Marcaj, geometric measurements, walking-route planning.

## Headline numbers

| Field | Official brief |
| --- | --- |
| Imaged area | **~1.45 km²** (~145 ha). Estimated from the OAM preview **alpha mask** and WGS 84 bounds |
| Bounding rectangle | **3.32 km²** — includes **empty margins**. Do not treat this as planted area |
| Reported GSD | **3.52 cm/px** — spatial **resolution, not accuracy**. No independent RMSE is published |
| Source file | **658.6 MB**, one RGB GeoTIFF |
| Raster | **70,246 × 81,986** px, 3 bands |
| Native CRS | WGS 84 / **EPSG:4326** |
| Map centre | **47.122392° N, 28.712051° E** (survey centre, **not** the route start) |
| Place | Sireți, Strășeni district, northwest of Chișinău. Local survey, not nationwide |
| Acquisition | **20 May 2025 (UTC)** |
| Provider | **3DATA COLLECT** |
| Platform | UAV / **Mavic 3E** |
| Licence | **CC BY 4.0**. Credit 3DATA COLLECT / OpenAerialMap, Open Imagery Network. Retain attribution and identify changes |

Published on OpenAerialMap. Challenge tiles in this repo are that mosaic **reprojected to EPSG:32635** and cut (0.025 m/px, 2048×2048). Measurements and routes stay in 32635.

## Do not mix these two points

| Point | Coordinates | What it is |
| --- | --- | --- |
| Dataset map centre (this brief) | 47.122392 N, 28.712051 E | Preview / survey centre |
| Official route start | 47.1230335 N, 28.7073776 E · 629504.70, 5220250.75 (EPSG:32635) | `data/challenge/02_route/start.geojson`, tile `siret3_r018_c010.tif` |

## Implications for this repo

- ~145 ha is the **flown / masked** AOI, not the 3.32 km² bbox and not width×height×GSD².
- GSD 3.52 cm on the source ortho ≠ 2.5 cm on the challenge tiles. Read the GeoTIFF; do not assume 3 cm for inventory or IoU.
- No published horizontal accuracy. Do not claim centimetre geolocation quality in the README.
- Credit line for the web map and README: **3DATA COLLECT / OpenAerialMap**, CC BY 4.0.
