# Annotation rules — Sireț3

Source of truth for **how to draw and attribute**. Transcribed from `data/challenge/03_docs/Vineyard_AI_annotation_rules.pdf` v1.0 (25 September 2026). The hidden reference follows **exactly** these rules.

Official examples (not scored): `data/challenge/05_examples/`. Open `siret3_examples_cvat.zip` in Marcaj or read `annotations.xml`.

---

## At a glance

| Label | Geometry | What it is | Attributes |
| --- | --- | --- | --- |
| `vineyard` | polygon | Canopy of **one** grapevine plant, from above | `vineyard_id` |
| `waste` | bounding box | One piece of litter, or one inseparable cluster | `vineyard_id` |
| `row` | polyline | Centre line of one vine row | `vineyard_id`, `row_id`, `row_structure` |
| `interrow_area` | polygon | Ground between the canopies of two neighbouring rows | `vineyard_id`, `interrow_cover` |

Names and values are **lower case, exact strings**. `Regular`, `bare soil`, `grass` are wrong answers.

`row_structure` = `regular` / `disrupted` / `unassessable`

`interrow_cover` = `bare_soil` / `vegetation` / `mixed` / `unassessable`

Tiles: 2048×2048 px GeoTIFF, **2.5 cm/px** (51.2 m), EPSG:32635. Draw in **pixels** in Marcaj. Scoring converts to metres.

---

## Golden rules

1. **One canopy = one plant.** Never one polygon over a whole row.
2. **Grapevines only.** Fruit trees, shrubs, weeds, grass are not `vineyard`.
3. **A row is one line per tile**, first vine to last vine, **through** any gaps.
4. **Canopies and inter-row areas never overlap.** Inter-row runs canopy-edge to canopy-edge, not axis to axis.
5. **IDs survive tile edges.** Same block / same row keep the same `vineyard_id` / `row_id` in every tile.
6. **Every tile gets an answer.** Annotate it, or tick **No objects in this frame**, and **submit the job**.

ID values are ours. `V03`, `north`, or `7` are all fine. Scored is grouping, not the string. Recommend `V01`, `V02`, … and `V03-R017`.

---

## What each attribute is for

| Attribute | On | Meaning | Why it is scored |
| --- | --- | --- | --- |
| `vineyard_id` | every object | Which block, e.g. `V03` | Distinct values = block count. Same-block / different-block grouping = 2% of the total score. |
| `row_id` | `row` | Which physical row, e.g. `V03-R02` | Distinct values = row count. Stitches tile fragments of one row. |
| `row_structure` | `row` | Continuous (`regular`), gap ≥ 5 m (`disrupted`), or cannot tell (`unassessable`) | Accuracy + macro-F1 vs reference. |
| `interrow_cover` | `interrow_area` | Ground cover in this tile | Same. Tells the grower what to mow or till. |

An empty attribute is a wrong answer. An object without `vineyard_id` belongs to no block. Attributes on the wrong label are ignored (`interrow_cover` on a row does nothing).

### Worked example (official)

Block `V03` crosses `siret3_r021_c012` and `siret3_r021_c013`. Three rows, each drawn twice with the **same** `row_id`. `V03-R02` has a 7 m gap **only** on the right tile → `regular` on the left, `disrupted` on the right.

Result: **1** block, **3** rows (six polylines), 45 canopies. If the right tile were named `R04`–`R06`, the count would read **6 rows** and that slice of the measurement score dies.

Pre-annotation fragment:

```xml
<polyline label="row" points="112.0,1830.5;1990.4,402.7" occluded="0">
  <attribute name="vineyard_id">V03</attribute>
  <attribute name="row_id">V03-R02</attribute>
  <attribute name="row_structure">disrupted</attribute>
</polyline>
```

### Common attribute mistakes

| Mistake | Cost |
| --- | --- |
| Rows renumbered from 1 in every tile | Row count explodes; axis F1 breaks |
| New `vineyard_id` per tile for the same block | Block count wrong; grouping score drops |
| Attribute left empty | Wrong answer |
| `Regular`, `bare soil`, `grass` | Not in the allowed list |
| `interrow_cover` on a row | Ignored |

---

## 1. Before you start

- Annotate **every** supplied tile. Hidden subset includes empty tiles.
- Empty tile: tick **No objects in this frame**. A job with a silent tile cannot be submitted.
- Only **submitted** jobs are scored. Saved ≠ submitted.
- Upload all five parts **before** publish. After publish, no more pre-annotations.
- Let the model assign IDs over the whole mosaic, then correct by hand.
- File names are `siret3_r<row>_c<column>`. Neighbouring tiles sit next to each other in a ZIP. Annotate patches, not random tiles.

## 2. Grapevine canopies — `vineyard`

Polygon around the foliage of one plant. Trace leaves within about **10 cm**. Leave out bare soil, the plant’s shadow, weeds, grass.

### 2.1 Young vines on bare soil

Rows ~2.7 m apart on tilled soil. Each plant is its own small polygon, however small. Leaf clumps **&lt; ~0.2 m²** that are not a plant (weeds) are not annotated.

**White protective tubes and stakes are part of the planting. They are neither canopy nor waste.**

### 2.2 Older vines with touching canopies

Split at the visible narrowing. If the canopy is continuous, split at the in-row planting distance (trunks, stakes, or other gaps in the same row; typically **1.0–1.5 m**).

Never one polygon over a whole row or block. Canopy **count** is scored (F1).

### 2.3 Trees, orchards, other vegetation

**Not vineyard:** fruit trees (crowns 2–4 m wide, 4–6 m apart), forest trees, shrubs, hedges, weeds, grass, other crops, vines on fences / arbours / houses.

A tree standing **inside** a vineyard is not a canopy. Annotate the vines around it. Where it hides the row, see `row_structure`.

Garden vineyards on village outskirts: annotate if vines stand in **at least three rows**. A single vine or an arbour in a yard is not.

Orchards look like rows. Vines are under 1 m wide and planted every 1–1.5 m.

### 2.4 Shadows, tile edges, missing plants

- Trace leaves, not shadow. A plant entirely in deep shadow, unseen, is not drawn.
- Plant cut by a tile edge: trace to the edge; the other half is a **separate** polygon on the neighbour tile.
- Missing or dead plant: **draw nothing**. The gap is `row_structure` (section 4.3).

## 3. Waste — `waste`

Tight **axis-aligned** box around clearly visible litter, anywhere on the tile (vineyards and land around them). Box area is **not** waste area.

| Waste | Not waste |
| --- | --- |
| Bags, plastic sheets and film, bottles, cans, packaging, tyres, construction debris, heaps of rubbish | Vine tubes, stakes, trellis posts and wires, irrigation hoses, stones, bare or pale soil, flowering shrubs, pruning residue and cut branches, vehicles and machinery |

Separate objects → separate boxes. Inseparable pile → one box.

`vineyard_id`: the block the object lies in, or the nearest block within **10 m**. Farther away, leave empty.

When in doubt, leave it out. False box = miss.

## 4. Row axes — `row`

Polyline along the centre line. Scored with **0.4 m** tolerance and **80%** mutual coverage.

### 4.1 How to draw

- One polyline per physical row **per tile**, first vine to last vine in this tile, or to the tile edge.
- Stay within **0.2 m** of vine centres. Straight row: two points. Curved: add a vertex at the bend.
- **Gaps do not split a row.** Line runs straight through missing plants. Same `row_id`.
- Outermost rows of a block are drawn like any other.

### 4.2 `row_id`

Unique within its block, same in every tile the row crosses. Recommend `<vineyard_id>-R<nn>`. Distinct `row_id` count = scored row count.

### 4.3 `row_structure` (this tile only)

| Value | When |
| --- | --- |
| `regular` | No gap of **5 m** or more in this tile |
| `disrupted` | Visible gap ≥ 5 m in this tile (missing/dead vines, or a tree/obstacle in the row) |
| `unassessable` | Row cannot be made out over most of its length (deep shadow, overexposure, weeds taller than the vines) |

Same physical row may be `regular` in one tile and `disrupted` in the next.

### 4.4 Where rows end

Dirt road: the road is **not** part of the block. Rows and inter-rows stop at the planting edge, not the road centre.

Block against scrub: last row is annotated; **no** inter-row outside it.

## 5. Inter-row areas — `interrow_area`

Walkable ground between two neighbouring rows of the **same** block. Area is scored. Route must stay on these polygons plus official passages.

### 5.1 How to draw

- Long sides: **canopy edges** of the two rows (not the axes). Canopies are not part of it.
- Short sides: where the rows end. Headland, roads, exterior land are out. If one row is shorter, end at the shorter one.
- Holes: cut out trees and buildings in the inter-row.
- One polygon per inter-row **per tile**, cut at the tile edge.
- None outside the outermost rows.

Row spacing (axis to axis) is **not** the inter-row width.

### 5.2 `interrow_cover` (this tile, this inter-row)

| Value | When |
| --- | --- |
| `bare_soil` | Vegetation covers less than about **¼** |
| `mixed` | About **¼ to ¾** covered (grass/weed strips + bare soil) |
| `vegetation` | Grass or weeds cover more than about **¾** |
| `unassessable` | Ground cannot be seen (deep shadow, or canopy closed over the inter-row) |

## 6. Blocks — `vineyard_id`

A block is a **connected planting**. Two plantings are the same block if they touch or are separated by **less than 5 m** of non-vineyard ground. A **road or track always separates blocks**.

Every object — canopy, row, inter-row, and waste within 10 m of a block — carries that block’s `vineyard_id`. Same string in every tile. Distinct values = block count.

## 7. What you do **not** annotate in Marcaj

- Inter-row **axes** (only inter-row **areas**)
- Roads, tracks, passages, forbidden zones, the start — organizer GeoJSON
- Inspection targets — application output (`inspections` / route targets), not Marcaj
- Orchards, trees, shrubs, buildings, fences, non-grape crops
- Black nodata outside imagery on edge tiles

## 8. Checklist before submit

- [ ] No polygon covers more than one plant; no canopy on trees or orchard crowns
- [ ] Every row: one polyline per tile, through gaps, same `row_id` on both sides of each edge
- [ ] No inter-row overlaps a canopy or extends past row ends
- [ ] Every object has `vineyard_id`; every row has `row_id` + `row_structure`; every inter-row has `interrow_cover`
- [ ] Every tile annotated or “No objects”; every job **submitted**

---

## Appendix A — upload ZIP

CVAT for images 1.1, **&lt; 90 MB** per ZIP. One ZIP per official tile part. Tiles = supplied files, original names. No JPEG/PNG.

```
team_upload.zip
├── annotations.xml
└── images/
    └── siret3_r021_c012.tif …
```

Label block to copy (also in the example ZIP):

```xml
<label><name>vineyard</name><type>polygon</type><attributes>
  <attribute><name>vineyard_id</name><input_type>text</input_type></attribute>
</attributes></label>
<label><name>waste</name><type>rectangle</type><attributes>
  <attribute><name>vineyard_id</name><input_type>text</input_type></attribute>
</attributes></label>
<label><name>row</name><type>polyline</type><attributes>
  <attribute><name>vineyard_id</name><input_type>text</input_type></attribute>
  <attribute><name>row_id</name><input_type>text</input_type></attribute>
  <attribute><name>row_structure</name><input_type>select</input_type>
    <values>regular
disrupted
unassessable</values>
  </attribute>
</attributes></label>
<label><name>interrow_area</name><type>polygon</type><attributes>
  <attribute><name>vineyard_id</name><input_type>text</input_type></attribute>
  <attribute><name>interrow_cover</name><input_type>select</input_type>
    <values>bare_soil
vegetation
mixed
unassessable</values>
  </attribute>
</attributes></label>
```

The stub `processing/src/siret3/cvat11.py` still lists `trellis` / `guyot` and `grass` / `soil` / `cover_crop`. **Do not upload those.**
