# STOP — orphan `frontend` branch (DEMO only)

**This is not the GigaHack submission app.**

It is a one-commit **unrelated-history** Next.js mock: white SVG canvas, **DEMO DATA**, port **3000**. Merging it into `main` overwrites `web/`, `processing/`, and the official Marcaj pack.

Read [`STOP.md`](STOP.md) first.

## Where to work

| Want | Do this |
| --- | --- |
| Scored / admission map | `git checkout main` then `cd web && npm run dev` (:43173, MapLibre) |
| Copy lime / layer-toggle IA | Look here, implement on `main` `web/` |
| Labels | Marcaj only |

## This mock (do not submit)

```bash
npm install
npm run dev
```

Opens `http://localhost:3000`. Upload GeoTIFF does **not** analyse a file. Routes are a visual preview, not `route.geojson`.

GitHub will **fail** any PR from `frontend` → `main`.
