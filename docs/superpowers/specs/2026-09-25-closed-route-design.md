# Closed route, inspections, measurements

**Date:** 2026-09-25  
**Status:** Approved in chat (“go ahead”) — implement while waste train holds the H100.

## Problem

The 25% walking-route slice is zero if the file is illegal or not closed. The repo sample `route.geojson` is EPSG:4326 and does not use the official start. Inspection targets are not exported. `measurements.csv` lacks the jury unions.

## Rules (official PDF)

- Coordinates **EPSG:32635**. One LineString. Property `length_m`.
- First and last vertex within **5 m** of `data/challenge/02_route/start.geojson` (629504.70, 5220250.75).
- Passable = inter-row polygons ∪ `passages.geojson` − `forbidden.geojson`. Do not walk canopies.
- Instant 0 if **> 2%** of length is outside passable.
- A target is visited if the route is within **2 m**. Targets = waste centroids + gap / missing-planting midpoints (not a Marcaj label).
- Prefer a longer legal walk over a short illegal shortcut.

## Design

**Passable geometry.** Shapely union of inter-row rings and passage rings, difference forbidden (buffer 0 if invalid).

**Legal path.** If the straight segment between two points lies inside passable (small buffer), use it. Else shortest path on a graph of polygon vertices plus the two endpoints; drop edges whose segment leaves passable.

**Tour.** Snap official start onto passable (fail if > 5 m). TSP / nearest-neighbour on targets, then replace each hop with a legal path. Close at start. Fail loud if illegal length fraction > 0.02.

**Writer.** `write_route_geojson` emits a FeatureCollection CRS EPSG:32635, one LineString, `length_m`. No lon/lat.

**Two walks (26 Sep).** Inspector file `route.geojson` uses inspection + waste targets (25% score). Farmer file `route_farmer.geojson` uses waste only. Same writer, same legal/closed rules. Do not merge both LineStrings into one FeatureCollection.

**Inspections.** For each row, sort plants of that `row_id` along the row heading. Any consecutive gap ≥ 5 m → point at the midpoint, `id` = `INS-{row_id}-{n}`, plus `vineyard_id` / `row_id`. Waste centroids are route targets but stay `kind=waste`.

**Measurements.** Keep per-feature rows. Add summary rows: `n_blocks`, `n_rows`, canopy union m²/ha, inter-row union m²/ha, total stitched row length.

**Out of scope.** 311-tile infer, Marcaj publish, web layers, GPU jobs.

## Test

Synthetic corridor + official start snap; illegal diagonal fails; gap ≥ 5 m emits one inspection; union area is not the overlapping sum.
