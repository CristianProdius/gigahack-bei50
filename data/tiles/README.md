# data/tiles

Drop the organiser 311 GeoTIFFs here, **unchanged names and bytes**:

```
data/tiles/siret3_rXXX_cYYY.tif
```

Then:

```bash
siret3 inventory data/tiles --out data/tile_index.csv
```

The inventory command fails if the count is not 311 or a name does not match `siret3_rXXX_cYYY.tif`. Use `--allow-partial` only for a COG-chip dry-run.

If the 311 pack is not on disk, chip the public Sireț3 COG (CC BY 4.0, 3DATA COLLECT):

```
https://oin-hotosm-temp.s3.us-east-1.amazonaws.com/68305aa2025981aa41124bc7/0/68305aa2025981aa41124bc8.tif
```

```bash
python models/chip_siret3_cog.py --cog data/source/siret3_visual.tif --out data/tiles
```

Those chips are samples for software tests. They are **not** the scored Marcaj set. Do not publish a zip that mixes COG chips with organiser names unless the bytes came from the pack.
