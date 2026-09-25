# Data layout

Root of the git repo is ready for the scored artefacts:

| Path | What |
| --- | --- |
| `data/tiles/siret3_rXXX_cYYY.tif` | 311 unchanged GeoTIFF tiles (gitignored) |
| `data/tile_index.csv` | written by `siret3 inventory` |
| `route.geojson` | closed walk (EPSG:4326 geometry, lengths in 32635) |
| `measurements.csv` | planar metres / square metres |

Sample `route.geojson` and `measurements.csv` at the repo root are **SAMPLE** geometry near the Sireț3 bbox. Replace after the Marcaj export.

Sireț3 source: OpenAerialMap item `683060c4025981aa411253c8`, CC BY 4.0, 3DATA COLLECT, 20 May 2025, 3.52 cm/px.
