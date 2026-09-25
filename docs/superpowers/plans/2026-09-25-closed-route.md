# Closed Route Implementation Plan

> **For agentic workers:** Use executing-plans. TDD on every function.

**Goal:** Legal closed `route.geojson` in EPSG:32635, inspections from 5 m gaps, jury measurement unions.

**Architecture:** Shapely passable union + networkx legal hops. CLI `inspect` / `route` / `measurements` read GeoJSON already used by stitch.

**Tech Stack:** shapely, networkx, pytest (already in `processing/`).

---

### Task 1: Legal fraction + 32635 writer

**Files:** `processing/tests/test_route.py`, `processing/src/siret3/route.py`

- [ ] Failing tests: `illegal_length_fraction` on a diagonal across a corridor; `write_route_geojson` CRS is 32635 and first/last near start.
- [ ] Implement `passable_union`, `illegal_length_fraction`, rewrite writer.
- [ ] pytest green.

### Task 2: Legal closed walk

**Files:** same

- [ ] Failing test: two waypoints in an L-shaped corridor; tour stays inside and returns to start; far start raises.
- [ ] Implement `legal_path` + `closed_walk` using passable graph.
- [ ] pytest green.

### Task 3: Inspections

**Files:** `processing/src/siret3/inspect.py`, `processing/tests/test_inspect.py`

- [ ] Failing test: two plants 6 m apart on one row → one inspection midpoint.
- [ ] Implement `inspections_from_canopies`.
- [ ] pytest green.

### Task 4: Measurement unions

**Files:** `processing/src/siret3/measurements.py`, `processing/tests/test_measurements.py`

- [ ] Failing test: two overlapping 10×10 squares → union 100 not 200; ha = m²/10000.
- [ ] Implement `summary_rows`.
- [ ] pytest green.

### Task 5: CLI

**Files:** `processing/src/siret3/cli.py`

- [ ] `siret3 inspect`, `siret3 route --start-file`, default official start.
- [ ] Existing route/measurements tests still pass.
