# Sireț3 map (`web/`)

Next.js + MapLibre viewer for the scored demo. **Port 43173**, not 3000.

```bash
cd web
npm install
npm run dev
```

Open [http://127.0.0.1:43173](http://127.0.0.1:43173).

## Layers

| File | What |
| --- | --- |
| `public/layers/sample.geojson` | Synthetic plants (SAMPLE badge). Used until a Marcaj pack has `vineyard` polygons. |
| `public/layers/layers.geojson` | Packed WGS84: Marcaj canopies/rows/inter-rows/waste plus official forbidden + passages. |
| `public/layers/route.geojson` | Inspector walk (blue). Display CRS is lon/lat; `length_m` is planar EPSG:32635. |
| `public/layers/route-farmer.geojson` | Farmer walk (red). |
| `public/layers/measurements.csv` | Jury CSV. |

After the team exports from Marcaj:

```bash
siret3 marcaj-import data/marcaj_export --tiles data/tiles --out data/marcaj_32635.geojson
siret3 inspect data/marcaj_32635.geojson --out inspections.geojson
siret3 measurements data/marcaj_32635.geojson --out measurements.csv
siret3 route data/marcaj_32635.geojson --targets inspections,waste --out route.geojson
siret3 route data/marcaj_32635.geojson --targets waste --out route_farmer.geojson
siret3 web-layers --layers data/marcaj_32635.geojson \
  --inspector route.geojson --farmer route_farmer.geojson \
  --measurements measurements.csv --inspections inspections.geojson \
  --forbidden data/challenge/02_route/forbidden.geojson \
  --passages data/challenge/02_route/passages.geojson \
  --out-dir web/public/layers
```

Reload the map. Badge switches from SAMPLE to Marcaj.

Do **not** merge git branch `frontend` into `main`. That app is a different Next.js tree on :3000.
