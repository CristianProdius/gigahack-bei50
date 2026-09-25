# Vineyard Inspector

Next.js, TypeScript, and Tailwind implementation of the supplied Vineyard Inspector screen. The aerial image is intentionally replaced by a white canvas. Its vector overlays and metrics are demonstrative; the interface labels them **DEMO DATA**.

## Run

```bash
npm install
npm run dev
```

Open `http://localhost:3000`. The app uses a local preview dataset until a processing API is connected.

## Current controls

- **Upload GeoTIFF** accepts `.tif` or `.tiff` and starts a progress display. In demo mode, this progress previews the UI; the file is **not analyzed**. An API URL enables upload and job polling.
- The top round buttons hide/show the panels and toggle browser full screen.
- Layer checkboxes change annotation visibility only. They do not alter metrics.
- Clicking a visible demo annotation changes the selected-feature details.
- **Plan Route** opens the planner above the button. **Select Starting Point** and **Select End Point** each enable a click anywhere on the canvas. Until an end is chosen, it follows the start so the preview returns there.
- **Build Optimal Route** visits every selected demo inspection or waste target using a short computed path and avoids the marked forbidden zone. It is a visual preview; real passable-area routing requires georeferenced backend data.
- Zoom buttons change the vector canvas scale. The arrow moves the view to the selected start point.

## Backend connection

Set `NEXT_PUBLIC_VINEYARD_API_URL` in `.env.local`. The adapter in `src/lib/vineyard-api.ts` currently expects:

- `GET /vineyard` → `VineyardData` as defined in `src/lib/vineyard-data.ts`.
- `POST /analyses` with a multipart `file` → `{ "id": "job-id" }`.
- `GET /analyses/:id` → `{ "id", "status", "progress", "result" }`, where status is `queued`, `processing`, `complete`, or `failed` and `result` is `VineyardData` when complete.

The service contract is a frontend integration point, not an existing server. A real map renderer must display georeferenced imagery and features returned by that service; the current SVG is only a demo of the reference layout. Route calculations and GeoTIFF processing must come from the backend before the application can report real results. The project-specific domain and visual requirements are in `.agents/skills/vineyard-inspector/`.
