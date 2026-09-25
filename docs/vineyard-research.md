# Sireț3 vineyard research

Verified sources for the GigaHack vineyard / Marcaj track. Deadline Sunday 27 Sep 2026, 15:00 Chișinău. Marcaj annotations are the scored source. Training on other public data is allowed. Manual Sireț3 labelling stays inside Marcaj. Measurements are planar in EPSG:32635 with no terrain correction.

This file is the evidence pack. The weekend sequence lives in [vineyard-plan.md](./vineyard-plan.md). What to train this weekend: [sota-research.md](./sota-research.md). Verbal briefing vs PDF: [provider-briefing.md](./provider-briefing.md). The official Marcaj download is in [`data/challenge/`](../data/challenge/) (tiles, route GeoJSON, PDFs, examples, source orthomosaic). What each file is: [`AGENTS.md`](../AGENTS.md) and [`data/challenge/README.md`](../data/challenge/README.md).

## 1. Sireț3 on OpenAerialMap

Queried live on 25 Sep 2026 against the HOT OpenAerialMap STAC API (`https://api.imagery.hotosm.org/stac/search`). Title filter `ilike %sireț%` returns four Moldova UAV items from producer **3DATA COLLECT** (Tasca Ivan). The challenge mosaic is **Sireț3**.

| Field | Verified value |
| --- | --- |
| Title | Sireț3 |
| STAC item ID | `683060c4025981aa411253c8` |
| Collection | `openaerialmap` |
| Capture window | `2025-05-20T21:00:00Z` to `2025-05-20T22:00:00Z` (20 May 2025) |
| GSD | 0.035191 m/px = **3.519 cm/px** |
| Licence | **CC-BY-4.0** |
| Platform | UAV, DJI Mavic 3E |
| Producer / licensor | 3DATA COLLECT |
| Raster shape | 81986 rows × 70246 cols (STAC `proj:shape`) |
| Visual COG | 628.6 MB (`file:size` 658583344) |
| Bbox (EPSG:4326) | `[28.700935, 47.113536, 28.723167, 47.131247]` |
| Native STAC CRS on the visual asset | EPSG:4326 (lon/lat geotransform). Work measurements in **EPSG:32635**. |

STAC item: [https://api.imagery.hotosm.org/stac/collections/openaerialmap/items/683060c4025981aa411253c8](https://api.imagery.hotosm.org/stac/collections/openaerialmap/items/683060c4025981aa411253c8)

COG (HTTPS): [https://oin-hotosm-temp.s3.us-east-1.amazonaws.com/68305aa2025981aa41124bc7/0/68305aa2025981aa41124bc8.tif](https://oin-hotosm-temp.s3.us-east-1.amazonaws.com/68305aa2025981aa41124bc7/0/68305aa2025981aa41124bc8.tif)

S3: `s3://oin-hotosm-temp/68305aa2025981aa41124bc7/0/68305aa2025981aa41124bc8.tif`

Thumbnail: [https://oin-hotosm-temp.s3.us-east-1.amazonaws.com/68305aa2025981aa41124bc7/0/68305aa2025981aa41124bc8.png](https://oin-hotosm-temp.s3.us-east-1.amazonaws.com/68305aa2025981aa41124bc7/0/68305aa2025981aa41124bc8.png)

Browser: [https://map.openaerialmap.org/](https://map.openaerialmap.org/) then search **Sireț3**, or pin the item in STAC Browser.

### How to get tiles

Three legal paths, all CC BY 4.0 with attribution to 3DATA COLLECT / Open Imagery Network:

1. **Challenge pack (preferred for Marcaj).** Use the 311 unchanged GeoTIFF tiles the organisers already cut, named `siret3_rXXX_cYYY.tif`. Do not retile or rename before the one-shot import.
2. **Full COG download.** `curl` / `aws s3 cp` the visual asset above. Then `gdalwarp -t_srs EPSG:32635` for work copies. Keep a sidecar that maps each challenge tile name to the source window.
3. **XYZ tiles for the web map (preview only, not for scoring).** HOT TiTiler, documented at [https://docs.imagery.hotosm.org/usage/using-imagery/](https://docs.imagery.hotosm.org/usage/using-imagery/):

```
https://api.imagery.hotosm.org/raster/collections/openaerialmap/items/683060c4025981aa411253c8/tiles/WebMercatorQuad/{z}/{x}/{y}?assets=visual
```

Old `tiles.openaerialmap.org` is deprecated (no CORS on redirect). Do not use it.

### Area note (do not invent 145 ha from the bbox)

The official dataset brief ([`siret3-dataset.md`](siret3-dataset.md)) says **~1.45 km² / 145 ha** from the OAM preview **alpha mask**, and that the **3.32 km²** bounding rectangle includes empty margins. The full raster canvas (width × height × GSD²) is about **713 ha**, mostly nodata around a rotated flight. Use valid-pixel area from the tiles, not the bbox. Survey map centre on the brief is 47.122392 N, 28.712051 E — not the route start.

Neighbour items from the same producer (do not mix into the scored set):

| Title | ID | GSD | Date |
| --- | --- | --- | --- |
| Sireț2 | `682f4997f02395f60d786397` | 3.519 cm | 20 May 2025 |
| Sireț | `682f43bcf02395f60d785b1c` | 0.841 cm | 20 May 2025 |
| Sireț | `682f3f9ff02395f60d785450` | 0.841 cm | 20 May 2025 |
| siret (April test) | `6800d9d60859d5432c0616c6` | 2.29 cm | 16–17 Apr 2025 |

## 2. Riseholme UAV vineyard COCO and YOLOv11

**Use this as the canopy / row pretrain set.** Official COCO dump (queried Zenodo API 25 Sep 2026):

- Record: [https://zenodo.org/records/19234907](https://zenodo.org/records/19234907)
- DOI: [https://doi.org/10.5281/zenodo.19234907](https://doi.org/10.5281/zenodo.19234907)
- Concept DOI: [https://doi.org/10.5281/zenodo.19234906](https://doi.org/10.5281/zenodo.19234906)
- Licence: **CC-BY-4.0** (Zenodo `metadata.license.id`)
- Authors: Cox, Heselden, de Silva, Hanheide, Polvara (University of Lincoln / LCAS)
- Funding: Innovate UK VISTA 10073653
- File: `riseholme-vineyard.zip`, 3.3 GB

Counts from the record abstract (do not invent extra classes):

| Subset | Images | Annotations |
| --- | --- | --- |
| Riseholme August 2024 | 285 | 11,285 |
| Riseholme March 2025 | 287 | 18,199 |
| Riseholme July 2025 | 283 | 10,731 |
| **Total** | **855** | **40,215** |

Instance classes: `pole`, `trunk`, `vine_row`, `vineyard` (canopy). That maps cleanly to Marcaj **vineyard polygon** and **row polyline**. `vine_row` is a mask, not a centreline: we still write a skeleton / least-squares centreline for the polyline label.

Related YOLOv11-format dump covering Lincoln + Oxfordshire at 12 / 20 / 30 / 40 m:

- [https://doi.org/10.5281/zenodo.15211733](https://doi.org/10.5281/zenodo.15211733) (AGRIDS)
- Licence: **CC-BY-NC-ND-4.0** (Zenodo API). No derivatives, non-commercial. Prefer the CC-BY Riseholme COCO and convert ourselves with Ultralytics `convert_coco(use_segments=True)`.
- Paper to cite if we touch AGRIDS: Cox, Hanheide, Polvara, *AGRIDS: an Advanced Multi-Modal Mapping Architecture for Robotics and Agriculture*, IEEE CASE 2024, [https://ieeexplore.ieee.org/abstract/document/10711678/](https://ieeexplore.ieee.org/abstract/document/10711678/)

Kaggle mirror ([https://www.kaggle.com/datasets/jondave/riseholme-vineyard-uav-rgb-segmentation-dataset](https://www.kaggle.com/datasets/jondave/riseholme-vineyard-uav-rgb-segmentation-dataset)) is labelled **CC BY-NC 4.0** and packaged as `vineyard_segmentation_paper.yolov11`. Different licence than the Zenodo COCO. Use Zenodo CC-BY-4.0.

**LCAS mapping code (found on the second search pass, 25 Sep 2026):** [https://github.com/LCAS/uav-vineyard-mapping](https://github.com/LCAS/uav-vineyard-mapping) (Apache-2.0, created 26 Mar 2026, same day as the Riseholme COCO record). Publication export of the aerial-ground vineyard mapping workspace. Ships `poles_to_rows.py`, `mid_row_lines.py`, `generate_topological_map.py`, interactive `generate_topo_map/`, and a ResNet heatmap path. Optional `scripts/roboflow_rfdetr/` (RF-DETR, not YOLO11). README is explicit: **no model weights, no Roboflow keys, no raw training imagery**. Use it for pole→row and mid-row GIS, not as a drop-in YOLO trainer.

**YOLOv11 training code:** still no public Cox/LCAS Ultralytics train script. The dataset card says they trained YOLOv11 instance segmentation. The runnable path remains Ultralytics (`yolo11n-seg.pt` / `yolo11s-seg.pt` / `yolo11m-seg.pt`) plus our stub in `models/train_yolo.py`. Other LCAS public code: [https://github.com/LCAS/KSI](https://github.com/LCAS/KSI) (Apache-2.0, seasonal semantic keypoints). VISTA project page: [https://lcas.lincoln.ac.uk/wp/research/projects/vista-vineyard-information-system-for-technology-and-automation/](https://lcas.lincoln.ac.uk/wp/research/projects/vista-vineyard-information-system-for-technology-and-automation/).

## 3. UOPNOA (block masks, not instance canopies)

UOPNOA is **Universidad de Oviedo + PNOA** (Spanish national orthophoto), not a Moldova vineyard instance set.

- Dataset: [https://doi.org/10.5281/zenodo.4648002](https://doi.org/10.5281/zenodo.4648002) (CC-BY-4.0)
- Paper: Pedrayes et al., *Evaluation of Semantic Segmentation Methods for Land Use with Spectral Imaging Using Sentinel-2 and PNOA Imagery*, Remote Sensing 13(12):2292, 2021, [https://doi.org/10.3390/rs13122292](https://doi.org/10.3390/rs13122292) (MDPI open access)
- Imagery: PNOA aircraft RGB, ~34,000 chips of 256×256
- Labels: SIGPAC land-use polygons rasterised to semantic masks. Vineyard is class **VI**. Plots with the same use are merged.

**Limit (must respect):** these are **cadastral block / land-use masks**, not vine-canopy instances and not row polylines. Useful only as a coarse "is this a vineyard block" prior. Do not treat UOPNOA IoU as canopy quality. No separate official training repo beyond the paper's UNet / DeepLabv3+ description.

Companion dataset on the same record: **UOS2** (Sentinel-2, 13 bands, ~2,000 images). Too coarse for 3.5 cm rows.

## 4. DroneWaste

For the Marcaj **waste bbox** class.

- Dataset record: [https://zenodo.org/records/17045559](https://zenodo.org/records/17045559) / [https://doi.org/10.5281/zenodo.17045559](https://doi.org/10.5281/zenodo.17045559)
- Licence: **CC-BY-4.0**
- 4,993 images, 5,135 instances, 20 materials, each mapped to a European Waste Code
- COCO JSON with **masks and boxes**
- Code: [https://github.com/lucamora/dronewaste](https://github.com/lucamora/dronewaste) (MIT). YOLOv8, YOLOv12, Faster R-CNN, k-fold scripts.
- Paper: Morandini et al., *DroneWaste dataset for waste recognition in drone imagery*, Scientific Data, [https://www.nature.com/articles/s41597-026-07970-1](https://www.nature.com/articles/s41597-026-07970-1) / [https://doi.org/10.1038/s41597-026-07970-1](https://doi.org/10.1038/s41597-026-07970-1). Article text is **CC BY-NC-ND 4.0**. The dataset remains CC-BY-4.0.
- Lab summary: [https://aura-lab.org/datasets/](https://aura-lab.org/datasets/)

Marcaj only scores a waste **bbox**, not material class. Train a single `waste` detector (or collapse the 20 EWC classes). Orthomosaic GSD in DroneWaste is coarser than 3.5 cm; expect a domain gap. Still the best public aerial-waste box set found.

## 5. GRowSeg, OrthoSeg, ICAERUS, SAM, YOLO

### GRowSeg

- Model card: [https://huggingface.co/links-ads/gaia-growseg](https://huggingface.co/links-ads/gaia-growseg)
- Licence: **MIT**
- Architecture: SegFormer-B5, 84.6M params, binary row vs background
- GSD range: about 0.75–10 cm/px; authors recommend 1–1.5 cm/px (`scaling_factor ≈ GSD / 1.5`)
- Official run repo on the card: `git clone git@hf.co:links-ads/vitigeoss-growseg` then `python main.py input.tif output.tif`
- Related dataset: [https://huggingface.co/datasets/links-ads/gaia-vineyard-uav-dataset](https://huggingface.co/datasets/links-ads/gaia-vineyard-uav-dataset) (4.29 GB; card empty as of fetch)

GRowSeg is **semantic rows**, not canopy instances. Good fallback / row prior on the 3.52 cm ortho. Not a replacement for Riseholme instance heads.

### OrthoSeg (Cybonic)

- Code + data layout: [https://github.com/Cybonic/DL_vineyard_segmentation_study](https://github.com/Cybonic/DL_vineyard_segmentation_study)
- Paper: Barros et al., *Multispectral vineyard segmentation: A deep learning comparison study*, Computers and Electronics in Agriculture 195:106782, 2022, [https://doi.org/10.1016/j.compag.2022.106782](https://doi.org/10.1016/j.compag.2022.106782), preprint [https://arxiv.org/abs/2108.01200](https://arxiv.org/abs/2108.01200)
- Hugging Face paper page: [https://huggingface.co/papers/2108.01200](https://huggingface.co/papers/2108.01200)
- GitHub licence field is empty. The arXiv HTML page marks the study **MIT**. Confirm `LICENSE` in the clone before reuse.
- Binary vine pixels on Portuguese UAV orthos (Esac fully labelled; Valdoeiro and Quinta de Baixo partial). Pipeline: split ortho → CNN → stitch mask. That is the pattern we copy for 311 tiles, not the weights.

### ICAERUS crop monitoring

- Code: [https://github.com/ICAERUS-EU/UC1_Crop_Monitoring](https://github.com/ICAERUS-EU/UC1_Crop_Monitoring)
- Use-case page: [https://icaerus.eu/use-cases/crop-monitoring-uc/](https://icaerus.eu/use-cases/crop-monitoring-uc/)
- Dataset index: [https://github.com/ICAERUS-EU/Zenodo_Datasets](https://github.com/ICAERUS-EU/Zenodo_Datasets)
- Useful pieces: `create_grid` / `create_grid_aligned` (rows and parcels on an ortho), vegetation indices, **path generator between rows**, YOLOv8 row-view plant health, YOLOv12 leaf disease (healthy / mildew / low-iron). GitHub licence field empty; read the clone.
- Canyelles vineyard UAV packages (RGB / MS / DEM / shapefiles) are listed on that Zenodo index. Disease classes are out of scope for Marcaj labels but the row-grid and inter-row path code is directly reusable.

### SAM / SAM2 / Ultralytics YOLO

- SAM: [https://github.com/facebookresearch/segment-anything](https://github.com/facebookresearch/segment-anything), Apache-2.0, paper [https://arxiv.org/abs/2304.02643](https://arxiv.org/abs/2304.02643)
- SAM2: [https://github.com/facebookresearch/sam2](https://github.com/facebookresearch/sam2), Apache-2.0
- Ultralytics instance seg: [https://docs.ultralytics.com/tasks/segment/](https://docs.ultralytics.com/tasks/segment/), code [https://github.com/ultralytics/ultralytics](https://github.com/ultralytics/ultralytics), **AGPL-3.0**. YOLO11 `-seg` weights still exist (`yolo11n-seg.pt` …). Docs now also advertise YOLO26-seg. Riseholme was trained as YOLOv11; start there.
- Ultralytics software DOI: [https://doi.org/10.5281/zenodo.13858602](https://doi.org/10.5281/zenodo.13858602) (v8.3.0, YOLO11 introduction)
- MobileSAM: [https://github.com/ChaoningZhang/MobileSAM](https://github.com/ChaoningZhang/MobileSAM), Apache-2.0
- FastSAM: [https://github.com/CASIA-LMC-Lab/FastSAM](https://github.com/CASIA-LMC-Lab/FastSAM) (current; `CASIA-IVA-Lab/FastSAM` 404s), AGPL-3.0

**AGPL note:** shipping a modified Ultralytics train/infer script in this repo is fine if the repo stays public. A closed binary of YOLO would need a Ultralytics enterprise licence. Paid APIs (Roboflow train, Ultralytics Platform, Replicate) are allowed by the brief if listed in the README. Prefer local AGPL + open weights.

SAM use: prompt from YOLO boxes / row seeds to clean canopy polygons on the 3.5 cm tiles when the instance head frays. SAM2 image predictor is enough; we do not need video.

## 6. CVAT for images 1.1 and `team_upload.zip`

Official spec: [https://docs.cvat.ai/docs/dataset_management/formats/format-cvat/](https://docs.cvat.ai/docs/dataset_management/formats/format-cvat/)

Marcaj import speaks this dump. Export ZIP layout:

```
team_upload.zip
├── annotations.xml
└── images/
    ├── siret3_r001_c001.tif
    ├── siret3_r001_c002.tif
    └── … 311 files, original names unchanged
```

`annotations.xml` is version **1.1**. Each image:

```xml
<image id="0" name="siret3_r001_c001.tif" width="4096" height="4096">
  <polygon label="vineyard" points="x0,y0;x1,y1;..." occluded="0">
    <attribute name="vineyard_id">V-0001</attribute>
  </polygon>
  <polyline label="row" points="x0,y0;x1,y1;..." occluded="0">
    <attribute name="row_id">R-0001-01</attribute>
    <attribute name="vineyard_id">V-0001</attribute>
    <attribute name="row_structure">trellis</attribute>
  </polyline>
  <polygon label="interrow_area" points="..." occluded="0">
    <attribute name="vineyard_id">V-0001</attribute>
    <attribute name="interrow_cover">grass</attribute>
  </polygon>
  <box label="waste" xtl="10.0" ytl="20.0" xbr="40.0" ybr="55.0" occluded="0"/>
</image>
```

Points are **pixel coordinates in that tile**, semicolon-separated `x,y`. Boxes use `xtl, ytl, xbr, ybr`. Attributes are child `<attribute name="...">value</attribute>` nodes. Label types in `<meta><task><labels>`: `polygon`, `polyline`, `bbox`.

Build rules:

1. `name` on `<image>` **must** equal the GeoTIFF file name the organisers shipped. No `images/` prefix unless Marcaj's importer expects it. Dry-run both `siret3_r001_c001.tif` and `images/siret3_r001_c001.tif` on 3 tiles before the 311-file zip.
2. Include **all 311** image files in the zip, even tiles with zero shapes. Empty `<image ...></image>` is valid and keeps the task complete.
3. Do not recompress, reproject, or rename TIFFs. Copy bytes.
4. Import **once**, then publish. Further Sireț3 drawing is only inside Marcaj.
5. `id` on `<image>` is the 0-based lexical index of the 311 names.

Our writer: `processing/src/siret3/cvat11.py`. It is glue, not a fork of CVAT.

## 7. Cross-tile IDs for 311 tiles (`siret3_rXXX_cYYY`)

Never emit a per-tile `vineyard_id` that changes when the same canopy crosses a seam.

1. Infer per tile in pixel space. Project polygons / polylines to **EPSG:32635** with each tile's GeoTransform (`rasterio`).
2. Buffer-overlap merge: vineyard polygons with IoU ≥ 0.2 or overlap area ≥ 8 m² become one instance. Rows whose Hausdorff distance on a 1.5 m buffer is small, or whose endpoints fall within 1.0 m, concatenate.
3. Stable IDs after merge, not before:
   - `vineyard_id` = `V-` + 4-digit order of increasing centroid easting, then northing.
   - `row_id` = `R-{vineyard_id}-{seq}` along the row-direction axis of that vineyard (PCA of the merged line).
4. Optional stability hash (if we re-run inference): `V-` + first 8 hex of SHA1 of quantized centroid `(round(x/0.5), round(y/0.5))`. Write both; Marcaj uses the short `V-NNNN`.
5. Inter-row polygons inherit the parent `vineyard_id`. Waste boxes stay local (no cross-tile ID) unless two boxes overlap after projection, then keep the larger.
6. Manifest `data/tile_index.csv`: `name,row,col,west,south,east,north,width_px,height_px,epsg`.

Tile size is not published. 4096 px on a 70246×81986 canvas is 21×18 = 378 windows; 311 is consistent with dropping empty / nodata-only tiles. Read sizes from the files. Do not assume a square grid.

## 8. Closed inspection walk

Constraints: closed walk, start snapped within **5 m**, only **inter-row polygons + authorised passages**, forbidden zones excluded, planar metres in EPSG:32635.

1. Passable polygon = `(interrow_area ∪ authorised_passages) − forbidden_zones`, then buffer 0.15 m and simplify.
2. Skeleton or 1.0 m hexagonal lattice clipped to passable. Build a NetworkX graph, edge weight = length.
3. Waypoints: vineyard centroids, waste boxes, and row ends that must be visited (orienteering prizes). If the brief only needs a covering walk of every inter-row, drop prizes and solve a covering closed walk on the graph.
4. Solver: NetworkX `approximation.traveling_salesperson` / Christofides on a distance matrix of shortest paths, or OR-Tools Routing with a start=end depot. Depot = given start if a node is within 5 m, else the nearest passable node (reject if > 5 m).
5. Export `route.geojson` LineString (and matching start/end points). Length is the 2D path length, no DEM.

`osmnx` is **not** the road graph here. OSM streets are not the vineyard. Use it only if we ever need a public-road approach to the farm gate.

ICAERUS `Path generator for drone between rows` is a useful reference for GPS tracks down inter-rows. We still own the closed-walk + 5 m start constraint.

## 9. Weekend sequence (summary)

Full timing is in the plan. Order is locked:

1. Model (Riseholme canopy/row + DroneWaste boxes) on H100.
2. Dry-run CVAT 1.1 on 3 tiles.
3. Infer all 311, stitch IDs, **one** `team_upload.zip`, publish in Marcaj.
4. Team correction only in Marcaj.
5. Export → `measurements.csv` + `route.geojson`.
6. Web map.
7. README with weights link and H100 / 16 GB numbers.

## 10. What we will not invent vs glue we write

**Will not invent**

- A new foundation model or a from-scratch YOLO backbone.
- Sireț3 labels outside Marcaj, or any other team's annotations.
- Papers, DOIs, GSD, area, or licence strings that were not fetched.
- Terrain-corrected (3D) lengths or areas.
- Material-level waste taxonomy in the scored dump (unless Marcaj adds it).
- A fake official LCAS YOLOv11 trainer. `LCAS/uav-vineyard-mapping` is real and useful, but it does not ship YOLO11 train code or weights.

**Glue we must write** (this repo)

- Tile index, CRS check, EPSG:32635 projection.
- Ultralytics / SAM fine-tune and tiled infer stubs.
- Cross-tile merge and stable IDs.
- CVAT 1.1 `annotations.xml` + zip with original `.tif` names.
- Planar measurements.
- Passable graph and closed route.
- MapLibre viewer for route + IDs + measurements.

## Catalog of open repositories and resources

Full inventory, not a shortlist. Every row has a URL, the licence advertised on 25 Sep 2026 (GitHub SPDX, Zenodo `license.id`, Hugging Face card, or host docs), and one line on how we would use it. `unspecified` means the API had no SPDX; open the clone before shipping derived weights. Searches: GitHub REST search, Hugging Face cards, Zenodo API, HOT OAM STAC.

### Sireț3 / OpenAerialMap source page

| Resource | URL | Licence | How we use it |
| --- | --- | --- | --- |
| OpenAerialMap browser (Sireț3 source page) | https://map.openaerialmap.org/ | CC-BY-4.0 per item | Search **Sireț3**; preview the mosaic; copy TMS/WMTS. |
| HOT OAM product page | https://www.hotosm.org/tech-suite/open-aerial-map/ | CC-BY-4.0 commons | Attribution wording (OIN / HOT / 3DATA COLLECT). |
| HOT OAM service repo | https://github.com/hotosm/openaerialmap | AGPL-3.0 | How the commons / STAC stack is built; do not fork. |
| OAM imagery browser (legacy) | https://github.com/hotosm/oam-browser | BSD-3-Clause | Older front-end; use map.openaerialmap.org instead. |
| HOT OAM STAC search | https://api.imagery.hotosm.org/stac/search | n/a (API) | Resolve item IDs, GSD, licence, asset hrefs. |
| Sireț3 STAC item | https://api.imagery.hotosm.org/stac/collections/openaerialmap/items/683060c4025981aa411253c8 | CC-BY-4.0 | Canonical metadata for the scored mosaic. |
| Sireț3 visual COG | https://oin-hotosm-temp.s3.us-east-1.amazonaws.com/68305aa2025981aa41124bc7/0/68305aa2025981aa41124bc8.tif | CC-BY-4.0 | Download full ortho if the 311-tile pack is missing. |
| Using OAM imagery (TMS / TiTiler) | https://docs.imagery.hotosm.org/usage/using-imagery/ | docs | Web-map raster tiles for item `683060c4025981aa411253c8`. |
| OAM user guide | https://docs.openaerialmap.org/browser/user-guide/ | docs | QGIS XYZ / JOSM / iD handoff. |
| TorchGeo OpenAerialMap dataset | https://docs.torchgeo.org/en/stable/api/datasets/openaerialmap.html | MIT (TorchGeo) | Optional STAC+TMS downloader if we script chips. |
| torchgeo/torchgeo | https://github.com/torchgeo/torchgeo | MIT | Same library; geospatial samplers if we chip the COG. |

### Riseholme / LCAS / VISTA / YOLOv11

| Resource | URL | Licence | How we use it |
| --- | --- | --- | --- |
| Riseholme COCO (855 / 40,215) | https://doi.org/10.5281/zenodo.19234907 | CC-BY-4.0 | Primary canopy + `vine_row` instance pretrain. |
| Riseholme Zenodo record | https://zenodo.org/records/19234907 | CC-BY-4.0 | Same dump; file `riseholme-vineyard.zip`. |
| Riseholme concept DOI | https://doi.org/10.5281/zenodo.19234906 | CC-BY-4.0 | Cite-all-versions badge. |
| LCAS/uav-vineyard-mapping | https://github.com/LCAS/uav-vineyard-mapping | Apache-2.0 | Official Riseholme mapping workspace: `poles_to_rows.py`, `mid_row_lines.py`, topological map export. No YOLO11 train script, no weights. |
| LCAS mapping scripts guide | https://github.com/LCAS/uav-vineyard-mapping/blob/main/scripts/README.md | Apache-2.0 | Index of active vs optional (`roboflow_rfdetr`) vs archive. |
| LCAS/KSI | https://github.com/LCAS/KSI | Apache-2.0 | Seasonal vineyard matching; not the YOLO trainer. |
| LCAS VISTA project | https://lcas.lincoln.ac.uk/wp/research/projects/vista-vineyard-information-system-for-technology-and-automation/ | project page | Context for row/vine maps and GeoJSON exports. |
| AGRIDS YOLO-format UAV set | https://doi.org/10.5281/zenodo.15211733 | CC-BY-NC-ND-4.0 | Altitude variety only if we accept ND/NC. Prefer COCO convert. |
| AGRIDS concept DOI | https://doi.org/10.5281/zenodo.15211732 | CC-BY-NC-ND-4.0 | Cite-all-versions of the NC/ND dump. |
| AGRIDS IEEE CASE 2024 | https://ieeexplore.ieee.org/abstract/document/10711678/ | IEEE (paper) | Citation if AGRIDS data is used. |
| Kaggle Riseholme YOLOv11 zip | https://www.kaggle.com/datasets/jondave/riseholme-vineyard-uav-rgb-segmentation-dataset | CC BY-NC 4.0 | Avoid; licence tighter than Zenodo COCO. |
| Ultralytics convert_coco | https://docs.ultralytics.com/datasets/convert/ | AGPL-3.0 | COCO → YOLO-seg for Riseholme. |
| Ultralytics YOLO11 docs | https://docs.ultralytics.com/models/yolo11/ | AGPL-3.0 | Train/predict API the Riseholme card implies. |

No public `*yolov11*riseholme*` training repository was found. Fine-tune via Ultralytics in `models/`. `LCAS/uav-vineyard-mapping` is the official GIS/mapping export, not a YOLO trainer.

### GRowSeg (Hugging Face + official code)

Official **code is a separate Hugging Face git**, not a GitHub repo. The weight card tells you to clone `links-ads/vitigeoss-growseg`.

| Resource | URL | Licence | How we use it |
| --- | --- | --- | --- |
| GRowSeg weights + card | https://huggingface.co/links-ads/gaia-growseg | MIT | Zero-shot binary row mask on Sireț3 tiles (SegFormer-B5). |
| GRowSeg official code (HF git) | https://huggingface.co/links-ads/vitigeoss-growseg | MIT (card) | `git lfs clone` then `python main.py input.tif output.tif`. No separate GitHub. |
| GRowSeg SSH clone | `git@hf.co:links-ads/vitigeoss-growseg` | MIT | Same repo as the HTTPS card above. |
| GAIA vineyard UAV dataset | https://huggingface.co/datasets/links-ads/gaia-vineyard-uav-dataset | unspecified on card | Extra row-mask training if we accept the empty card. |
| VitiGEOSS CORDIS | https://cordis.europa.eu/project/id/869565 | n/a | Project that funded GRowSeg; context only. |

### OrthoSeg (Cybonic)

| Resource | URL | Licence | How we use it |
| --- | --- | --- | --- |
| OrthoSeg study repo | https://github.com/Cybonic/DL_vineyard_segmentation_study | unspecified (paper says MIT) | Copy split/stitch; optional SegNet/U-Net baselines. |
| OrthoSeg journal paper | https://doi.org/10.1016/j.compag.2022.106782 | Elsevier | Cite if we use the Portuguese orthos. |
| OrthoSeg arXiv | https://arxiv.org/abs/2108.01200 | arXiv | Open PDF + MIT mention. |
| OrthoSeg HF paper page | https://huggingface.co/papers/2108.01200 | n/a | Same study; points back at the Cybonic repo. |

### ICAERUS-EU crop monitoring

| Resource | URL | Licence | How we use it |
| --- | --- | --- | --- |
| ICAERUS UC1 code | https://github.com/ICAERUS-EU/UC1_Crop_Monitoring | unspecified | Row/parcel grid, inter-row drone path, YOLO health models. |
| ICAERUS UC1 page | https://icaerus.eu/use-cases/crop-monitoring-uc/ | n/a | Scope: disease, 3D canopy, dashboard (we take grid + path only). |
| ICAERUS workflow write-up | https://icaerus.eu/from-ndvi-to-computer-vision-building-a-crop-monitoring-workflow-with-drones/ | n/a | Dual-scale ortho + row-view pattern. |
| ICAERUS Zenodo dataset list | https://github.com/ICAERUS-EU/Zenodo_Datasets | unspecified | Canyelles UAV packs; YOLOv9 vine-seg cells; YOLOv12 disease set. |
| ICAERUS-EU/AgroTwin | https://github.com/ICAERUS-EU/AgroTwin | Apache-2.0 | 3D canopy biometrics from RGB drone clouds; not the scored 2D path. |
| Agrobitsrl/canopy-biometrics | https://github.com/Agrobitsrl/canopy-biometrics | Apache-2.0 | Standalone LAI/TRV/LWA from a point cloud; skip for planar Marcaj. |

### Waste / aerial detection

| Resource | URL | Licence | How we use it |
| --- | --- | --- | --- |
| DroneWaste code | https://github.com/lucamora/dronewaste | MIT | Train/eval scripts for aerial waste boxes. |
| DroneWaste Zenodo | https://doi.org/10.5281/zenodo.17045559 | CC-BY-4.0 | Fine-tune the waste bbox head (4,993 images). |
| DroneWaste Zenodo record | https://zenodo.org/records/17045559 | CC-BY-4.0 | Same dataset files. |
| DroneWaste paper | https://doi.org/10.1038/s41597-026-07970-1 | CC BY-NC-ND 4.0 (article) | Cite; do not republish article text. |
| AURA Lab dataset page | https://aura-lab.org/datasets/ | CC-BY-4.0 (dataset) | Short public summary. |
| TACO toolkit | https://github.com/pedropro/TACO | MIT (toolkit; images have their own terms) | Ground-level litter only; last-resort extra boxes. |
| Drone waste dataset index | https://github.com/kaushalkumar94/drone-waste-detection-datasets | CC0-1.0 | Curated list of open aerial-waste sets. |
| VisDrone dataset index | https://github.com/VisDrone/VisDrone-Dataset | unspecified | Aerial objects, not waste-specific; skip unless desperate. |

### UOPNOA / land-use vineyard blocks

No separate official UOPNOA training repo. The paper used stock UNet + Google DeepLabv3+.

| Resource | URL | Licence | How we use it |
| --- | --- | --- | --- |
| UOPNOA + UOS2 | https://doi.org/10.5281/zenodo.4648002 | CC-BY-4.0 | Coarse VI vineyard-block prior only. |
| UOPNOA concept DOI | https://doi.org/10.5281/zenodo.4648001 | CC-BY-4.0 | Cite-all-versions. |
| Pedrayes et al. 2021 | https://doi.org/10.3390/rs13122292 | CC-BY (MDPI) | Documents SIGPAC plot masks, not canopies. |
| MDPI HTML | https://www.mdpi.com/2072-4292/13/12/2292 | CC-BY | Same paper, full text. |
| TensorFlow Model Garden (DeepLab) | https://github.com/tensorflow/models | Apache-2.0 (LICENSE; GitHub SPDX NOASSERTION) | Architecture the UOPNOA paper cites; we do not train it. |

### Instance / prompt segmentation toolkits

| Resource | URL | Licence | How we use it |
| --- | --- | --- | --- |
| Ultralytics YOLO | https://github.com/ultralytics/ultralytics | AGPL-3.0 | Fine-tune YOLO11-seg / detect; public repo keeps AGPL ok. |
| Ultralytics segment docs | https://docs.ultralytics.com/tasks/segment/ | docs | Train / val / predict / export API. |
| SAM | https://github.com/facebookresearch/segment-anything | Apache-2.0 | Box-prompt canopy cleanup. |
| SAM paper | https://arxiv.org/abs/2304.02643 | arXiv | Cite if we use SAM. |
| SAM2 | https://github.com/facebookresearch/sam2 | Apache-2.0 | Preferred promptable segmenter on tiles. |
| MobileSAM | https://github.com/ChaoningZhang/MobileSAM | Apache-2.0 | 16 GB / CPU fallback for prompts. |
| FastSAM (current) | https://github.com/CASIA-LMC-Lab/FastSAM | AGPL-3.0 | Fast everything-seg if we need a proposal layer. |

### Spatial Python

| Resource | URL | Licence | How we use it |
| --- | --- | --- | --- |
| rasterio | https://github.com/rasterio/rasterio | BSD (LICENSE in repo; GitHub SPDX NOASSERTION) | Read 311 GeoTIFFs, windows, warps. |
| geopandas | https://github.com/geopandas/geopandas | BSD-3-Clause | Tile merge, measurements, GeoJSON I/O. |
| shapely | https://github.com/shapely/shapely | BSD-3-Clause | Buffers, overlays, skeletons inputs. |
| leafmap | https://github.com/opengeos/leafmap | MIT | Optional Jupyter QA of COG + vectors. |
| raster-vision | https://github.com/azavea/raster-vision | Apache-2.0 | Optional tiled infer framework; we stay on rasterio+YOLO. |
| opengeos/geospatial | https://github.com/opengeos/geospatial | MIT | Convenience install set if a laptop is bare. |
| pyproj / EPSG:32635 | https://epsg.io/32635 | n/a | WGS 84 / UTM zone 35N for Moldova. |

### CVAT and XML writers

`opencv/cvat` now redirects to `cvat-ai/cvat`. Marcaj speaks **CVAT for images 1.1**. Our writer is `processing/src/siret3/cvat11.py`.

| Resource | URL | Licence | How we use it |
| --- | --- | --- | --- |
| CVAT (cvat-ai/cvat; opencv/cvat redirect) | https://github.com/cvat-ai/cvat | MIT | Schema source; we do not self-host unless Marcaj fails a dry-run. |
| CVAT for images 1.1 docs | https://docs.cvat.ai/docs/dataset_management/formats/format-cvat/ | docs | ZIP layout + XML 1.1. |
| CVAT XML writer in-tree | https://github.com/cvat-ai/cvat/blob/develop/cvat/apps/dataset_manager/formats/cvat.py | MIT | Reference `XmlAnnotationWriter` for element names. |
| Historic opencv/cvat writer blob | https://github.com/opencv/cvat/blob/d497bb6a90dd3c9625c3c8e8f73278019e21983d/cvat/apps/dataset_manager/formats/cvat.py | MIT | Same writer at the opencv-era SHA. |
| Datumaro (CVAT ecosystem) | https://github.com/cvat-ai/datumaro | MIT | Optional converter if we ever need COCO↔CVAT. |
| Datumaro CVAT format docs | https://open-edge-platform.github.io/datumaro/stable/docs/data-formats/formats/cvat.html | docs | CLI `datum convert --output-format cvat`. |
| next-cvat | https://github.com/nextml-code/next-cvat | unspecified | Reads/writes CVAT for images 1.1; optional check of our XML. |
| next-cvat PyPI | https://pypi.org/project/next-cvat/ | unspecified | Same SDK. |

### Routing / graphs

| Resource | URL | Licence | How we use it |
| --- | --- | --- | --- |
| NetworkX | https://github.com/networkx/networkx | BSD (SPDX NOASSERTION) | Passable graph, shortest paths, TSP approximation. |
| OR-Tools | https://github.com/google/or-tools | Apache-2.0 | Routing model if NetworkX TSP is weak on 200+ waypoints. |
| OSMnx | https://github.com/gboeing/osmnx | MIT | Only for public-road context; **not** inter-row geometry. |
| Drone-ACO-ACPP | https://github.com/saidlab-team/Drone-ACO-ACPP | BSD-2-Clause | UAV coverage planning in woody crops; not the scored closed walk. |

### Web map (GeoTIFF + GeoJSON)

| Resource | URL | Licence | How we use it |
| --- | --- | --- | --- |
| MapLibre GL JS | https://github.com/maplibre/maplibre-gl-js | BSD-style (SPDX NOASSERTION) | Primary viewer: OAM raster + GeoJSON overlays. |
| MapLibre official COG example | https://maplibre.org/maplibre-gl-js/docs/examples/add-a-cog-raster-source/ | docs | Drop-in `cog://` source if TiTiler is blocked. |
| maplibre-cog-protocol | https://github.com/geomatico/maplibre-cog-protocol | MIT | Client COG protocol used by that example; can mask with GeoJSON. |
| maplibre-gl-raster | https://github.com/opengeos/maplibre-gl-raster | MIT | MapLibre + deck.gl GPU pipeline for local / remote GeoTIFF. |
| Leaflet | https://github.com/Leaflet/Leaflet | BSD-2-Clause | Fallback if MapLibre WebGL fails in the jury browser. |
| deck.gl | https://github.com/visgl/deck.gl | MIT | Optional large-path / picking layer. |
| geotiff.js | https://github.com/geotiffjs/geotiff.js | MIT | Client COG window if we cannot hit TiTiler. |
| PMTiles | https://github.com/protomaps/PMTiles | BSD-style (SPDX NOASSERTION) | Package a small preview mosaic if XYZ is blocked. |
| TiTiler | https://github.com/developmentseed/titiler | MIT | Self-host tile endpoint for local GeoTIFFs (optional Dockerfile). |
| OAM per-item XYZ | https://docs.imagery.hotosm.org/usage/using-imagery/ | docs | Production basemap for Sireț3 in the web app. |

### Other vineyard row / canopy / waste / orthomosaic repos found in search

Nadir / ortho / row geometry first. Ground-level bunch detectors are listed so we do not rediscover them later.

| Resource | URL | Licence | How we use it |
| --- | --- | --- | --- |
| gbatsis/VYSegML | https://github.com/gbatsis/VYSegML | unspecified | Multispectral UAV vineyard segmentation; compare if GRowSeg is weak. |
| wilgomoreira/multispectral-vineyard-segmentation | https://github.com/wilgomoreira/multispectral-vineyard-segmentation | unspecified | ROBOT24 MS UAV vine-seg eval; methods only (RGB-only Sireț3). |
| dataset-ninja/vineyard-rows | https://github.com/dataset-ninja/vineyard-rows | NOASSERTION | Semantic row dataset card; check image licence before train. |
| aelsaer/UAVINE | https://github.com/aelsaer/UAVINE | BSD-3-Clause | Greek vineyard HS+RGB UAV set; domain extra, not instance labels. |
| ivatavuk/vineyard_midrow_detection | https://github.com/ivatavuk/vineyard_midrow_detection | unspecified | ROS LiDAR mid-row line; idea for inter-row centreline, not tiles. |
| EnricoMendez/lines_vineyard | https://github.com/EnricoMendez/lines_vineyard | unspecified | ROS 2D camera crop-row nav; ground robot, not ortho. |
| Javier-P-C/lines_vineyard | https://github.com/Javier-P-C/lines_vineyard | unspecified | Related ROS row-detection research fork. |
| aaronzberger/CMU_Vineyard_Driving | https://github.com/aaronzberger/CMU_Vineyard_Driving | unspecified | DL row detection + EKF + PID; ground robot. |
| MrD1360/deep_segmentation_vineyards_navigation | https://github.com/MrD1360/deep_segmentation_vineyards_navigation | unspecified | Semantic-seg drive-along-row controller; not Marcaj labels. |
| abdulkadiryildirim/Vineyard-Row-Detection-and-Empty-Area-Analysis-with-SAM3-Model | https://github.com/abdulkadiryildirim/Vineyard-Row-Detection-and-Empty-Area-Analysis-with-SAM3-Model | unspecified | SAM3 row + gap analysis; look at prompts, not weights. |
| Ibra9551/fIPAR-Pix | https://github.com/Ibra9551/fIPAR-Pix | MIT | Camera fIPAR in orchard/vineyard canopies; out of scope. |
| AlfonsoLRz/VineyardUAVClassification | https://github.com/AlfonsoLRz/VineyardUAVClassification | GPL-3.0 | Hyperspectral UAV CNN; we have RGB only. |
| Mahyarona/VSSIXA | https://github.com/Mahyarona/VSSIXA | unspecified | Spectral-structural extraction on vineyard point clouds. |
| molnarszilard/canopy_segmentation | https://github.com/molnarszilard/canopy_segmentation | unspecified | Side-view FPN canopy; not ortho rows. |
| EOA-team/VegSeg | https://github.com/EOA-team/VegSeg | unspecified | RGB ortho canopy cover (corn/beet/sunflower). Weak vineyard prior. |
| tong-xz/GrapeSAM | https://github.com/tong-xz/GrapeSAM | Apache-2.0 | Cluster/berry SAM; ground imagery, not rows. |
| YiyuanLinXX/SAM-CLIP | https://github.com/YiyuanLinXX/SAM-CLIP | unspecified | Powdery mildew + canopy on a ground robot. Out of scope. |
| ispstiima/ECSDVineyardDataset | https://github.com/ispstiima/ECSDVineyardDataset | unspecified | Front-on RGB-D canopy/grape masks. Not nadir. |
| ai-agriculture-circuits-and-systems/embrapa_wgisd_grape_detection | https://github.com/ai-agriculture-circuits-and-systems/embrapa_wgisd_grape_detection | NOASSERTION | WGISD grape instances; ground, not tiles. |
| Grapevine-Seg (OENO One) | https://doi.org/10.20870/oeno-one.2026.60.1.9628 | journal | Improved YOLACT for cordons; ground, not tiles. |
| AI4Agriculture grape boxes | https://doi.org/10.5281/zenodo.5660081 | check record | Bunch boxes, not rows. |
| wGrapeUNIPD-DL | https://doi.org/10.5281/zenodo.4066730 | check record | White-grape YOLO bunches. |
| Grapevine bunch detection | https://zenodo.org/records/7717055 | check record | 720×540 bunch YOLO. |
| PMC UAV→phone grape framework | https://pmc.ncbi.nlm.nih.gov/articles/PMC11869025/ | journal | YOLOv8-seg bunches; citation only. |
| Nolan et al. 2015 row skeletonisation | https://doi.org/10.36334/modsim.2015.f12.nolan | journal | Classical UAS row skeleton; method idea if DL frays. |

---

## Licence cheat-sheet for training

| Asset | Train commercially / hackathon? |
| --- | --- |
| Sireț3 imagery | Yes, with CC BY 4.0 attribution. Do not relabel outside Marcaj. |
| Riseholme COCO Zenodo | Yes, CC-BY-4.0. |
| LCAS/uav-vineyard-mapping code | Yes, Apache-2.0. Weights are not in the repo. |
| AGRIDS YOLO zip | No derivatives / NC. Avoid. |
| Kaggle Riseholme | NC. Avoid. |
| DroneWaste images | Yes, CC-BY-4.0. Paper is NC-ND (cite only). |
| UOPNOA | Yes, CC-BY-4.0, block masks only. |
| GRowSeg weights + vitigeoss-growseg | Yes, MIT. |
| Ultralytics code | Yes if this repo stays public (AGPL-3.0). |
| SAM / SAM2 / MobileSAM | Yes, Apache-2.0. |
| FastSAM (`CASIA-LMC-Lab/FastSAM`) | AGPL-3.0, same rule as Ultralytics. |
| UAVINE | Yes, BSD-3-Clause (no instance labels). |

## Paid APIs (allowed if listed)

None required. If used, name them in the README: Ultralytics Platform, Roboflow train, Replicate GPU, Hugging Face Inference. Default path is local H100 + open weights.

## Verification log

- STAC and Zenodo JSON pulled 25 Sep 2026. Item IDs, GSD, file size, and licence IDs are from those payloads, not memory.
- GitHub SPDX pulled via `api.github.com/repos/...` the same day. Search queries: `vineyard segmentation`, `vineyard row detection`, `vineyard UAV`, `vineyard canopy`, `drone waste detection`, `org:LCAS vineyard`, plus named-repo GETs.
- Hugging Face GRowSeg card fetched 25 Sep 2026. Official code is `links-ads/vitigeoss-growseg` on the Hub, not GitHub.
- FastSAM current home is `CASIA-LMC-Lab/FastSAM` (AGPL-3.0). `CASIA-IVA-Lab/FastSAM` 404s.
- `opencv/cvat` redirects to `cvat-ai/cvat` (MIT).
- `LCAS/uav-vineyard-mapping` was found on the second pass (Apache-2.0). It is the official Riseholme mapping export. It still does **not** contain a YOLO11 trainer or weights. That absence is recorded, not filled with a guessed URL.
