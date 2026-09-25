# Vineyard Inspector: map interface direction

The supplied screenshot is a product mockup/reference, not live data. Follow its information architecture and visual tone while adapting to the project’s existing design system and real data.

## Visual direction

- Make the georeferenced vineyard map the primary full-window surface. Use aerial imagery as the canvas, with crisp, high-contrast vector overlays and restrained dark translucent panels so the terrain remains visible.
- Use a deep charcoal/slate UI, pale text, lime green for primary actions and selected/authorized states, blue for the planned route, orange for inspection points, and red for waste/forbidden areas. Use patterns as well as color to distinguish forbidden polygons.
- Keep typography compact and legible over imagery. Use consistent spacing, fine dividers, modest radii, and restrained shadows. Avoid excessive blur/glass effects or decorative components that obscure map data.
- Keep the map responsive and usable on phone screens: panels should collapse into drawers/sheets or a clear compact layout, with map controls reachable and no overlay blocking all map interaction.

## Reference layout and controls

Desktop reference composition:

1. A slim map header with the product name, current layer/view selector, pause/live state when applicable, full-screen control, and `Upload GeoTIFF` action.
2. A left-side Layers panel with toggle rows for Canopies, Rows, Inter-row Areas, Waste, Inspection Points, Walking Route, Forbidden Zones, and Authorized Passages. Each toggle includes a stable visual legend distinct in shape/pattern as needed.
3. A right-side Vineyard Summary panel for unique blocks/rows, canopy area, inter-row area, total row length, and route length.
4. A right-side Selected Feature panel showing the selected row/block/target’s IDs, measured length or attributes, and a clear missing/unassessable state.
5. A Route Planner panel where the user chooses the start source (organizer start or map selection), target types (inspection, waste, both), then builds the route. Show the target count and return-to-start status near the action.
6. Map controls for zoom, locating/resetting view, scale, and a compact persistent legend where room permits.

The mockup shows a possible example: Sireț Vineyard, 12 blocks, 248 rows, 19.8 ha canopy, 14.2 ha inter-row, 18.4 km total row length, and 4.2 km route. These are sample-only values and must never be presented as current analysis unless loaded data confirms them. A selected-row example includes row length and a `disrupted` structure status.

## Interaction behavior

- Layer toggles change map visibility immediately and keep each legend synchronized. Hiding a layer must not silently delete or change its data.
- Selecting a feature on the map highlights it and updates the details panel; selecting a row/block in any future table/list should do the same and pan/zoom appropriately.
- Show identity and provenance for selected features: feature class, `vineyard_id`, `row_id` where applicable, attributes, units, and source/status if known.
- Provide a deliberate route-planning state: start choice, target types, progress/error feedback, route line, length, target coverage, and return-to-origin indication. Keep the previous route clearly marked if a recalculation fails.
- Upload/import UI should explain supported georeferenced formats and the coordinate-system expectations. Do not imply a GeoTIFF was successfully parsed until validation completes; show actionable errors for unsupported files, missing CRS, or malformed geometry.
- Full-screen, zoom, locate, and scale controls should remain understandable with tooltips or accessible labels.

## States and accessibility

Design explicit states for no dataset, loading imagery, partial layer availability, empty result, unsupported CRS, missing attributes, unassessable classifications, route computation, route success, unreachable targets, and route error. Keep summaries tied to available data and indicate when values are partial.

Use semantic buttons/inputs, visible keyboard focus, accessible names, adequate text/control contrast over imagery, and non-color cues for feature types and selection. On narrow screens, preserve access to layer toggles, selected-feature details, and route planning without requiring precision-only map gestures.
