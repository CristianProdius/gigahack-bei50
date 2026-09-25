# Vineyard Inspector: product and data requirements

This reference captures the supplied GigaHack challenge brief for building the Vineyard Inspector application. Challenge process requirements below are context for product behavior; they do not authorize Codex to upload data, publish an annotation project, contact organizers, or submit deliverables.

## Problem and intended outcome

Vineyard operators need a measurable map of planting, row structure, visible waste, and places needing inspection. The app should turn the supplied Sireț3 RGB orthomosaic and derived annotations into an interactive map, accurate area/length summaries, and a practical walking route. The expected value is better inspection coverage with less preparation and walking. The brief’s example compares a 6 km walk to 4.2 km (30% less, 27 minutes saved at an assumed 4 km/h); do not state this as a measured result for a particular vineyard unless verified.

## Data model

| Feature | Geometry | Required properties / meaning |
| --- | --- | --- |
| Grapevine canopy (`vineyard`) | Polygon | `vineyard_id`; each vine canopy individually delineated, not a whole row/block mask |
| Waste (`waste`) | Bounding box | `vineyard_id`; distinguish separate items; a visually inseparable cluster may be one object. Box size is not actual waste area. |
| Vine-row axis (`row`) | Polyline | `vineyard_id`, stable `row_id`, `row_structure` |
| Inter-row area (`interrow_area`) | Polygon | `vineyard_id`, `interrow_cover`; ground between adjacent rows, excluding canopy, road, headland, and outside land |
| Inspection location | Point | Stable ID/coordinates and links to `vineyard_id` and, when identifiable, `row_id` |
| Authorized passage / forbidden zone | Polygon or multipolygon | `type = passage` or `forbidden`; constrains route passability |
| Walking route | LineString | Ordered path starting/ending at the supplied origin; publish `length_m` |

Attribute values:

- `row_structure`: `regular`, `disrupted`, or `unassessable`.
- `interrow_cover`: `bare_soil`, `vegetation`, `mixed`, or `unassessable`.
- Use `unassessable` when imagery does not support a reliable classification; do not guess.
- Connect features to vineyard blocks with `vineyard_id`. A block is one connected planting area. Preserve IDs across tile seams and remove duplicates.

## Measurements and coordinate system

- Input basis: georeferenced RGB GeoTIFF orthomosaic for Sireț3/Siret3, collected 20 May 2025 at about 3.52 cm/px, covering approximately 145 ha; supplied tiles are GeoTIFF and already georeferenced.
- All final geometries, route coordinates, and measurement tables use EPSG:32635 (WGS 84 / UTM zone 35N) in metres. GeoJSON coordinates must remain in that CRS as specified by the challenge.
- Measurements are horizontal, without terrain correction.
- Report area in m² and hectares, and length in metres (UI may additionally show km). Include unique block count, unique row count, individual and total row lengths, unioned canopy area, and inter-row area.
- Canopy union prevents overlapping polygons from inflating area. Canopy and inter-row areas are disjoint by definition.
- Keep calculations traceable to source geometries; label whether a value is measured, estimated, missing, or illustrative.

## Route planning

The planner accepts the organizer-supplied start point and a target selection: inspection locations, waste, or both. Find a short route that visits every reachable target and returns to the start. Walkable space consists of passable inter-row areas plus authorized passages. Never route through a canopy, fence, or forbidden zone.

Show the route as a georeferenced polyline and report its length. Make target coverage inspectable: distinguish visited/reachable/unreachable targets and allow a user to understand route segments on the map. If a route cannot satisfy the constraints, expose the cause instead of drawing an invalid path. Submission criteria in the brief require the route to return within 5 m of the supplied origin, cover targets within 2 m, and keep the route almost entirely within passable areas/passages (a route with over 2% outside scores zero for that criterion); keep this challenge-specific threshold configurable if the application serves other sites.

## Data processing and annotation boundary

The intended upstream pipeline can combine a neural model with classical computer vision and spatial post-processing for canopy segmentation, waste detection, row-axis extraction, inter-row derivation, and attributes. Open reference datasets mentioned in the brief include Riseholme, UOPNOA, and DroneWaste; check each dataset’s current license and domain fit before adopting it. The Sireț3 source is described as CC BY 4.0; preserve required attribution when redistributing it.

The challenge’s manual creation, validation, and correction of Sireț3 annotations is only in the team’s Marcaj project. The supplied import is CVAT for Images 1.1 in a ZIP containing `annotations.xml` and the unchanged original-name GeoTIFF tiles under `images/`. Tile names and all five tile parts matter; IDs crossing tile edges must stay consistent. The brief says pre-annotations must be imported before publishing, together with all tiles, and the project should contain 311 files before publication. Treat these as organizer workflow facts that may change or be superseded by current instructions; do not attempt this workflow unless the user explicitly asks and the necessary account/platform access is available.

## Expected deliverables

The repository root is expected to provide `route.geojson` (one returning LineString in EPSG:32635 with `length_m`), `measurements.csv` (block/row counts, row lengths, and areas by block/row), `README.md` with reproducible setup/run instructions, pinned dependencies, model weights/access, full-tile processing time and hardware, paid APIs/LLMs, application/processing code, and a working deployed-interface link. Keep generated deliverables reproducible and consistent with the map UI. Do not claim a deliverable exists until it is generated and checked.

The challenge evaluates canopy segmentation, waste detection, row axes and attributes, counts/measurements, and walking-route coverage/efficiency. The brief’s tolerances are 15% for counts/areas and 10% for total row length. Use these as project evaluation context, not as permission to trade away route safety or hide uncertainty.

## Source data provenance

The supplied brief says Sireț3 is an open RGB orthomosaic provided by 3DATA COLLECT via OpenAerialMap, and describes CC BY 4.0 terms. Confirm actual input metadata and applicable license files before implementing import/export or redistribution. The challenge brief is the source for expected schema and evaluation requirements; it is not proof that the repository already contains source imagery, trained weights, annotation exports, or organizer assets.
