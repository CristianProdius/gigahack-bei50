"""Marcaj / CVAT export → EPSG:32635 without re-deriving rows or plants."""

from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from siret3.cvat11 import render_annotations
from siret3.cvat_parse import parse_cvat11
from siret3.marcaj import (
    collect_cvat_images,
    dump_projected_geojson,
    projected_from_cvat,
    to_wgs84_collection,
)

WEST, NORTH = 629000.0, 5_220_000.0
GSD = 0.025


def _write_tile(path: Path) -> None:
    transform = from_origin(WEST, NORTH, GSD, GSD)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=64,
        width=64,
        count=1,
        dtype="uint8",
        crs="EPSG:32635",
        transform=transform,
    ) as dst:
        dst.write(np.zeros((1, 64, 64), dtype="uint8"))


def _xml() -> str:
    return """<?xml version="1.0" encoding="utf-8"?>
<annotations>
  <version>1.1</version>
  <image id="0" name="siret3_r001_c001.tif" width="64" height="64">
    <polygon label="vineyard" occluded="0" points="10.0,20.0;14.0,20.0;14.0,24.0;10.0,24.0">
      <attribute name="vineyard_id">V09</attribute>
    </polygon>
    <polyline label="row" occluded="0" points="8.0,22.0;20.0,22.0">
      <attribute name="vineyard_id">V09</attribute>
      <attribute name="row_id">V09-R03</attribute>
      <attribute name="row_structure">disrupted</attribute>
    </polyline>
    <polygon label="interrow_area" points="8.0,26.0;20.0,26.0;20.0,30.0;8.0,30.0">
      <attribute name="vineyard_id">V09</attribute>
      <attribute name="interrow_cover">mixed</attribute>
    </polygon>
    <box label="waste" xtl="40.0" ytl="40.0" xbr="44.0" ybr="48.0" occluded="0">
      <attribute name="vineyard_id">V09</attribute>
    </box>
  </image>
  <image id="1" name="siret3_r001_c002.tif" width="64" height="64"/>
</annotations>
"""


def test_projected_from_cvat_keeps_human_rows_and_ids(tmp_path: Path):
    tiles = tmp_path / "tiles"
    tiles.mkdir()
    _write_tile(tiles / "siret3_r001_c001.tif")
    images = parse_cvat11(_xml())
    items = projected_from_cvat(images, tiles)
    kinds = {p.kind for p in items}
    assert kinds == {"vineyard", "row", "interrow_area", "waste"}
    assert all(p.vineyard_id == "V09" for p in items)
    row = next(p for p in items if p.kind == "row")
    assert row.row_id == "V09-R03"
    assert row.row_structure == "disrupted"
    assert len(row.coords) == 2
    vine = next(p for p in items if p.kind == "vineyard")
    assert vine.coords[0][0] == pytest.approx(WEST + 10 * GSD)
    assert vine.coords[0][1] == pytest.approx(NORTH - 20 * GSD)
    inter = next(p for p in items if p.kind == "interrow_area")
    assert inter.interrow_cover == "mixed"
    waste = next(p for p in items if p.kind == "waste")
    xs = [c[0] for c in waste.coords]
    ys = [c[1] for c in waste.coords]
    assert min(xs) == pytest.approx(WEST + 40 * GSD)
    assert max(ys) == pytest.approx(NORTH - 40 * GSD)


def test_does_not_invent_rows_when_export_has_plants_only(tmp_path: Path):
    tiles = tmp_path / "tiles"
    tiles.mkdir()
    _write_tile(tiles / "siret3_r001_c001.tif")
    xml = """<?xml version="1.0" encoding="utf-8"?>
<annotations>
  <image id="0" name="siret3_r001_c001.tif" width="64" height="64">
    <polygon label="vineyard" points="10.0,20.0;14.0,20.0;14.0,24.0;10.0,24.0">
      <attribute name="vineyard_id">V01</attribute>
    </polygon>
  </image>
</annotations>
"""
    items = projected_from_cvat(parse_cvat11(xml), tiles)
    assert [p.kind for p in items] == ["vineyard"]


def test_collect_from_zip_and_json_simple(tmp_path: Path):
    import json
    import zipfile

    xml_path = tmp_path / "annotations.xml"
    xml_path.write_text(render_annotations(parse_cvat11(_xml())), encoding="utf-8")
    zpath = tmp_path / "part1.zip"
    with zipfile.ZipFile(zpath, "w") as zf:
        zf.write(xml_path, "annotations.xml")
    from_zip = collect_cvat_images(zpath)
    assert from_zip[0].name == "siret3_r001_c001.tif"
    assert any(s.label == "row" for s in from_zip[0].shapes)

    simple = [
        {
            "name": "siret3_r001_c001.tif",
            "width": 64,
            "height": 64,
            "shapes": [
                {
                    "type": "polygon",
                    "label": "vineyard",
                    "points": [10.0, 20.0, 14.0, 20.0, 14.0, 24.0, 10.0, 24.0],
                    "attributes": {"vineyard_id": "V09"},
                }
            ],
        }
    ]
    jpath = tmp_path / "dump.json"
    jpath.write_text(json.dumps(simple), encoding="utf-8")
    from_json = collect_cvat_images(jpath)
    assert from_json[0].shapes[0].label == "vineyard"
    assert from_json[0].shapes[0].attributes["vineyard_id"] == "V09"


def test_dump_waste_is_polygon_not_linestring(tmp_path: Path):
    tiles = tmp_path / "tiles"
    tiles.mkdir()
    _write_tile(tiles / "siret3_r001_c001.tif")
    items = projected_from_cvat(parse_cvat11(_xml()), tiles)
    out = tmp_path / "out.geojson"
    dump_projected_geojson(items, out)
    data = __import__("json").loads(out.read_text(encoding="utf-8"))
    waste = next(f for f in data["features"] if f["properties"]["kind"] == "waste")
    assert waste["geometry"]["type"] == "Polygon"


def test_web_layers_reprojects_utm35_to_lonlat():
    fc = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"kind": "row", "row_id": "V01-R01"},
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[629504.70, 5220250.75], [629510.70, 5220250.75]],
                },
            }
        ],
    }
    out = to_wgs84_collection(fc)
    lon, lat = out["features"][0]["geometry"]["coordinates"][0]
    assert 28.70 < lon < 28.72
    assert 47.12 < lat < 47.13
    assert "crs" not in out or "4326" in str(out.get("crs", "")).lower()
