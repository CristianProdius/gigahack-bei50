# Data layout

Official Marcaj pack: [`challenge/README.md`](challenge/README.md). Agent orientation: [`../AGENTS.md`](../AGENTS.md).

| Path | What |
| --- | --- |
| `data/challenge/01_tiles/*.zip` | 311 challenge GeoTIFFs, five parts (gitignored). EPSG:32635, 0.025 m/px, 2048×2048. |
| `data/challenge/01_tiles/overview.png` | Tile grid and START marker. |
| `data/challenge/02_route/*.geojson` | Start, passages, forbidden zones, study area. All EPSG:32635. |
| `data/challenge/03_docs/*.pdf` | Challenge description, annotation rules, Marcaj quick start, Sireț3 dataset brief. |
| `data/challenge/04_source/*.tif` | Source orthomosaic, EPSG:4326 (gitignored, 658.6 MB on the official brief). |
| `data/challenge/05_examples/` | Two scored-format example tiles plus previews. Not scored. |
| `data/tiles/siret3_rXXX_cYYY.tif` | Unzipped tiles for `siret3 inventory` (gitignored). |
| `data/tile_index.csv` | Written by `siret3 inventory`. |
| `route.geojson` | Closed walk (EPSG:4326 geometry, lengths in 32635). |
| `measurements.csv` | Planar metres / square metres. |

Unzip before inventory:

```bash
unzip 'data/challenge/01_tiles/siret3_challenge_tiles_part*.zip' -d data/tiles
```

Official start (also in `data/challenge/02_route/start.geojson`): lon 28.7073776, lat 47.1230335, UTM X 629504.70, Y 5220250.75, tile `siret3_r018_c010.tif`.

Sample `route.geojson` and `measurements.csv` at the repo root are **SAMPLE** geometry near the Sireț3 bbox. Replace after the Marcaj export.

Sireț3 source: OpenAerialMap item `683060c4025981aa411253c8`, CC BY 4.0, 3DATA COLLECT, 20 May 2025. Challenge tiles are that mosaic reprojected to EPSG:32635 and cut. Route layers also use OpenStreetMap (ODbL).
