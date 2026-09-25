# Siret3 processing

Python spatial pipeline. All lengths and areas are planar in **EPSG:32635**. No terrain correction.

```bash
cd processing
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
siret3 --help
```

## Commands

```bash
# Inventory 311 GeoTIFFs (fail if names or count are wrong)
siret3 inventory ../data/tiles --out ../data/tile_index.csv

# Merge per-tile GeoJSON and assign vineyard_id / row_id
siret3 stitch ../data/predictions --out ../data/stitched.gpkg

# Write CVAT for images 1.1 zip (original .tif names)
siret3 cvat-export ../data/stitched.gpkg ../data/tiles --out ../team_upload.zip

# Planar measurements from a Marcaj / CVAT export
siret3 measurements ../export.xml --tiles ../data/tiles --out ../measurements.csv

# Closed walk on inter-row + passages, start snap 5 m
siret3 route ../data/stitched.gpkg --start 28.7120,47.1224 --out ../route.geojson
```

`route` accepts `--start` in lon,lat (4326) or x,y if you pass `--start-crs EPSG:32635`.
