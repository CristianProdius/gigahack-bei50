import json
from pathlib import Path

import pytest

from siret3.georef import pixels_to_xy_once
from siret3.project import project_inputs

REPO = Path(__file__).resolve().parents[2]
TILE = REPO / "data/tiles/siret3_r021_c012.tif"


@pytest.mark.skipif(not TILE.is_file(), reason="challenge tile not unzipped")
def test_pixels_to_xy_once_matches_raster_corners():
    import rasterio

    with rasterio.open(TILE) as src:
        west, south, east, north = src.bounds
        width, height = src.width, src.height
    pts = pixels_to_xy_once(TILE, [(0.0, 0.0), (float(width), float(height))])
    assert pts[0][0] == pytest.approx(west, abs=1e-6)
    assert pts[0][1] == pytest.approx(north, abs=1e-6)
    assert pts[1][0] == pytest.approx(east, abs=1e-6)
    assert pts[1][1] == pytest.approx(south, abs=1e-6)


@pytest.mark.skipif(not TILE.is_file(), reason="challenge tile not unzipped")
def test_project_inputs_merges_two_pixel_files(tmp_path: Path):
    canopy = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"kind": "vineyard", "tile": TILE.name, "score": 0.9},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[10.0, 10.0], [20.0, 10.0], [20.0, 20.0], [10.0, 20.0], [10.0, 10.0]]],
                },
            }
        ],
    }
    waste = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"kind": "waste", "tile": TILE.name, "score": 0.8},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[30.0, 30.0], [40.0, 30.0], [40.0, 40.0], [30.0, 40.0], [30.0, 30.0]]],
                },
            }
        ],
    }
    a = tmp_path / "canopy"
    b = tmp_path / "waste"
    a.mkdir()
    b.mkdir()
    (a / f"{TILE.stem}.geojson").write_text(json.dumps(canopy), encoding="utf-8")
    (b / f"{TILE.stem}.geojson").write_text(json.dumps(waste), encoding="utf-8")
    fc = project_inputs([a, b], TILE.parent)
    kinds = {f["properties"]["kind"] for f in fc["features"]}
    assert kinds == {"vineyard", "waste"}
    assert "32635" in fc["crs"]["properties"]["name"]
    ring = fc["features"][0]["geometry"]["coordinates"][0]
    assert ring[0][0] > 1000  # metres, not pixel col
