# Scoring — what is worth points

Transcribed from the official challenge PDF. **85% automatic output metrics, 15% expert engineering.** Scoring uses a **hidden subset** of the 311 tiles. Annotate all of them. The subset includes tiles with **no vineyards**; canopy polygons there are penalised as false positives.

Matching is **one-to-one**. Duplicates = false positives. Missed objects stay errors.

IoU = intersection over union. F1 = precision/recall combination.

Admission first: working web UI, published Marcaj with submitted jobs, correct formats and georeferencing. Fail admission → no prize.

Ties: walking-route score, then canopy segmentation, then jury vote.

---

## Score card

| Weight | Criterion | What they measure | Where the numbers come from |
| --- | --- | --- | --- |
| **25%** | Canopy segmentation | Class IoU + per-plant F1 | Marcaj `vineyard` polygons |
| **10%** | Waste detection | Box F1 | Marcaj `waste` rectangles |
| **15%** | Axes and attributes | Row F1 + attribute scores + ID grouping | Marcaj `row` / `interrow_area` |
| **10%** | Counts and measurements | Block/row counts, canopy area, inter-row area, total row length | Computed **from Marcaj**, same way for every team. `measurements.csv` is shown to the jury, not used as the metric source. |
| **25%** | Walking route (inspector) | Target coverage + efficiency | Repo **`route.geojson`** (inspector: gaps + waste) vs hidden targets + passable geometry. **`route_farmer.geojson` is required** but is not this 25% source unless a later official PDF splits the points. |
| **15%** | Engineering quality | Architecture, robustness, scalability, measured performance | Repo, README timings, live demo |

Total 100%.

---

## 25% — Vineyard canopy segmentation

```
0.6 × (canopy-class IoU)
+ 0.4 × (F1 of individual canopies, one-to-one match at IoU ≥ 0.5)
```

on the hidden reference tiles.

**Empty-tile penalty:** false canopies on tiles without vineyards cost `0.5 × (share of the tile they cover)`.

Implications:

- One polygon per plant. A whole-row blob kills F1 even if class IoU looks fine.
- Do not invent canopies on empty / orchard / village tiles.
- Prefer missing a tiny weed over drawing a false vine.

## 10% — Waste detection

Bounding-box F1, one-to-one, **IoU ≥ 0.3**.

Misses, false positives, and duplicates all reduce the score.

Implications:

- When in doubt, **leave it out** (official annotation rule). A false box costs as much as a miss.
- Vine tubes, stakes, trellis, irrigation, stones, pale soil, pruning piles, vehicles = **not waste**.
- Separate items = separate boxes. Overlapping inseparable pile = one box.

## 15% — Axes and attributes

| Slice | Weight | Metric |
| --- | --- | --- |
| Row-axis F1 | **8%** | A predicted axis matches a reference axis when **each** lies at least **80%** within **0.4 m** of the other. |
| Attributes | **5%** | Mean of **accuracy** and **macro-F1** on `row_structure` and `interrow_cover`, over **every reference object**. Missing objects count as attribute **errors**, not as “excluded”. |
| `vineyard_id` grouping | **2%** | Objects of one block share an ID; objects of different blocks do not. **Values need not match** the reference (`V03` vs `north` is fine). |

Implications:

- Keep the polyline within ~0.2 m of vine centres (rules). Two points for a straight row.
- Gaps do not split the line or the `row_id`.
- Empty `row_structure` / `interrow_cover` is a wrong answer.
- Renumbering rows per tile (`R01` again on the next tile) doubles the row count and breaks axis matching.

## 10% — Counts and measurements

Five equal slices of **2%** each:

1. Number of vineyard blocks (distinct `vineyard_id`)
2. Number of rows (distinct `row_id`)
3. Canopy area (union of canopy polygons)
4. Inter-row area
5. Total row length

Each value:

```
score = max(0, 1 − relative_error / tolerance)
```

| Quantity | Tolerance |
| --- | --- |
| Counts and areas | **15%** |
| Length | **10%** |

Values are computed from the team’s **Marcaj annotations**, the same way for every team. `measurements.csv` is shown to the jury.

Implications:

- ID mistakes (new `vineyard_id` / `row_id` per tile) move the count outside the 15% band → that 2% goes to zero.
- Canopy area is the **union**, not the sum of overlapping blobs.
- Inter-row polygons that overlap canopies or spill onto roads inflate area.
- Row length is the sum of physical rows (stitch by `row_id`), not six tile fragments counted as six rows.

## 25% — Walking route (inspector file)

**26 Sep:** the challenge requires **two** closed walks. This 25% is still computed on **`route.geojson` only** (inspector). The farmer file is a required second deliverable (web + admission completeness).

| Slice | Cap | Metric |
| --- | --- | --- |
| Coverage | **15%** | Organizers’ **hidden** list of inspection locations **and** waste. A target is visited if the **inspector** route passes within **2 m**. |
| Efficiency | **10%** | `L_ref / L`, awarded only from **90% coverage** and then scaled by coverage. `L_ref` = shorter of the organizers’ route and the shortest **admitted** team inspector route. |

**Instant 0 on this entire 25%** if either:

- more than **2%** of **inspector** route length is outside passable inter-row areas ∪ authorised passages, or
- the **inspector** route does not return to the official start within **5 m**.

The farmer walk (`route_farmer.geojson`) must use the same legal graph and official start, targets = **waste only**. Show it on the web (red). Do not put it inside `route.geojson`.

Implications:

- Both walks: closed loop at `data/challenge/02_route/start.geojson` (5 m).
- Stay inside `interrow_area` polygons + `passages.geojson`. Never clip `forbidden.geojson` or walk through canopies.
- Inspector visits **our** inspection points (gaps / missing planting) **and** waste. Farmer visits waste only. Hidden reference for the 25% will be similar to the inspector target set.
- A short illegal shortcut on the inspector file zeros the whole 25%. Prefer a longer legal walk.
- Efficiency is only in play after ~90% inspector coverage. Do not optimise inspector length before coverage.

## 15% — Engineering quality (jury)

| Subscore | Points | They look at |
| --- | --- | --- |
| Architecture | 5 | Model → GIS stitch → CVAT → Marcaj → measurements → two routes → web |
| Robustness | 4 | Empty tiles, CRS, failed snaps, bad ZIPs, ID collisions |
| Scalability | 3 | 311 tiles, 90 MB ZIP parts, ID stitch across the ortho |
| Measured performance | 3 | README wall time + hardware; jury may ask for a re-run |

Need a working, reproducible demo. Performance is judged from the README; list time and hardware honestly.

---

## How to spend the weekend (score-first)

1. **Do not fail admission or the route-zero rules.** Publish 311, submit every job, legal closed route in EPSG:32635.
2. **Protect the 25% canopy + 15% axes.** Per-plant polygons, one polyline per row per tile, stable IDs.
3. **Protect the 25% inspector route.** Legal graph, 2 m visit of gaps + waste, then shorten. Also ship a legal farmer waste-only walk.
4. **Attributes and waste are 15% + 10%.** Exact enum strings; conservative waste.
5. **Counts ride on ID discipline.** One `vineyard_id` / `row_id` across tile edges.
6. **Engineering 15%** is the README, Docker, timings, and a map that shows IDs, areas, and the route.

## What is **not** scored as a Marcaj label

Inspection targets (gaps, missing planting) are **application output**, not Marcaj objects. Roads, passages, forbidden zones, and the start are organizer GeoJSON. Inter-row **axes** are not drawn.
