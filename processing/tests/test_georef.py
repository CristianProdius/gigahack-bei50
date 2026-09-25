from pathlib import Path

import pytest

from siret3.georef import pixel_to_xy, xy_to_pixel

REPO = Path(__file__).resolve().parents[2]
TILE = REPO / "data/tiles/siret3_r021_c012.tif"


@pytest.mark.skipif(not TILE.is_file(), reason="challenge tile not unzipped")
def test_pixel_corners_match_raster_bounds():
    import rasterio

    with rasterio.open(TILE) as src:
        west, south, east, north = src.bounds
        width, height = src.width, src.height

    x0, y0 = pixel_to_xy(TILE, 0.0, 0.0)
    assert x0 == pytest.approx(west, abs=1e-6)
    assert y0 == pytest.approx(north, abs=1e-6)

    x1, y1 = pixel_to_xy(TILE, float(width), float(height))
    assert x1 == pytest.approx(east, abs=1e-6)
    assert y1 == pytest.approx(south, abs=1e-6)


@pytest.mark.skipif(not TILE.is_file(), reason="challenge tile not unzipped")
def test_xy_to_pixel_roundtrip():
    x, y = pixel_to_xy(TILE, 512.25, 1024.75)
    col, row = xy_to_pixel(TILE, x, y)
    assert col == pytest.approx(512.25, abs=1e-6)
    assert row == pytest.approx(1024.75, abs=1e-6)


@pytest.mark.skipif(not TILE.is_file(), reason="challenge tile not unzipped")
def test_pixel_step_is_2_5_cm():
    x0, y0 = pixel_to_xy(TILE, 0.0, 0.0)
    x1, y1 = pixel_to_xy(TILE, 1.0, 0.0)
    x2, y2 = pixel_to_xy(TILE, 0.0, 1.0)
    assert abs(x1 - x0) == pytest.approx(0.025, abs=1e-9)
    assert abs(y2 - y0) == pytest.approx(0.025, abs=1e-9)
