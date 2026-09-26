from pathlib import Path

import pytest

from siret3.cvat_parse import parse_cvat_zip
from siret3.derive import (
    derive_from_canopies,
    interrows_from_rows,
    rows_from_canopies,
)
from siret3.georef import pixels_to_xy
from siret3.ids import ProjectedPoly, assign_block_ids, assign_row_ids

REPO = Path(__file__).resolve().parents[2]
EXAMPLE_ZIP = REPO / "data/challenge/05_examples/siret3_examples_cvat.zip"
TILES = REPO / "data/tiles"


def _plant(x: float, y: float, tile: str = "siret3_r001_c001.tif") -> ProjectedPoly:
    return ProjectedPoly(
        kind="vineyard",
        coords=[(x - 0.1, y - 0.1), (x + 0.1, y - 0.1), (x + 0.1, y + 0.1), (x - 0.1, y + 0.1)],
        tile=tile,
    )


def test_assign_block_ids_keeps_one_polygon_per_plant():
    near = [_plant(i * 1.2, 0.0) for i in range(4)]
    far = [_plant(80 + i * 1.2, 80.0, tile="siret3_r002_c009.tif") for i in range(3)]
    out = assign_block_ids(near + far)
    vines = [p for p in out if p.kind == "vineyard"]
    assert len(vines) == 7
    ids = {p.vineyard_id for p in vines}
    assert ids == {"V01", "V02"}
    assert {p.coords[0] for p in vines} == {p.coords[0] for p in near + far}


def test_load_official_passages_multipolygon():
    from siret3.cli import _load_projected

    path = REPO / "data/challenge/02_route/passages.geojson"
    if not path.is_file():
        pytest.skip("official passages missing")
    items = _load_projected(path)
    assert len(items) >= 1
    assert all(p.kind == "passage" for p in items)
    assert all(len(p.coords) >= 4 for p in items)
    assert any((p.extras or {}).get("holes") for p in items)


def test_rows_from_elongated_canopy_uses_major_axis():
    strip = ProjectedPoly(
        kind="vineyard",
        vineyard_id="V01",
        coords=[(0.0, 0.0), (20.0, 0.0), (20.0, 1.0), (0.0, 1.0), (0.0, 0.0)],
        tile="siret3_r001_c001.tif",
        extras={"label": "vine_row"},
    )
    rows = rows_from_canopies([strip])
    assert len(rows) == 1
    length = ((rows[0].coords[0][0] - rows[0].coords[1][0]) ** 2 + (rows[0].coords[0][1] - rows[0].coords[1][1]) ** 2) ** 0.5
    assert length == pytest.approx(20.0, abs=1.0)


def test_interrows_pair_adjacent_diagonal_rows():
    rows = [
        ProjectedPoly(kind="row", coords=[(0, 0), (10, 10)], tile="t.tif", vineyard_id="V01"),
        ProjectedPoly(kind="row", coords=[(2.0, 0), (12, 10)], tile="t.tif", vineyard_id="V01"),
        ProjectedPoly(kind="row", coords=[(4.0, 0), (14, 10)], tile="t.tif", vineyard_id="V01"),
    ]
    inter = interrows_from_rows(rows, [])
    assert len(inter) == 2
    first = inter[0].coords
    xs = [p[0] for p in first]
    assert min(xs) < 3.5


def test_interrow_stays_on_overlapping_stretch():
    long = ProjectedPoly(kind="row", coords=[(0.0, 0.0), (20.0, 0.0)], tile="t.tif", vineyard_id="V01")
    short = ProjectedPoly(kind="row", coords=[(8.0, 2.0), (12.0, 2.0)], tile="t.tif", vineyard_id="V01")
    inter = interrows_from_rows([long, short], [])
    assert len(inter) == 1
    xs = [p[0] for p in inter[0].coords]
    assert min(xs) >= 6.0
    assert max(xs) <= 14.0


def test_row_ids_join_aligned_rows_across_large_seam_gap():
    vines = [
        ProjectedPoly(
            kind="vineyard",
            vineyard_id="V01",
            coords=[(0, 0), (1, 0), (1, 1), (0, 1)],
            tile="siret3_r001_c001.tif",
        )
    ]
    r1 = ProjectedPoly(kind="row", coords=[(0, 2), (8, 2)], tile="siret3_r001_c001.tif")
    r2 = ProjectedPoly(kind="row", coords=[(15, 2), (22, 2)], tile="siret3_r001_c002.tif")
    out = assign_row_ids(vines + [r1, r2], join_m=1.0)
    rows = [p for p in out if p.kind == "row"]
    assert {r.row_id for r in rows} == {"V01-R01"}


def test_assign_block_ids_road_splits_clusters():
    left = _plant(0.0, 0.0)
    right = _plant(3.0, 0.0)
    road = [[(1.4, -2), (1.6, -2), (1.6, 2), (1.4, 2)]]
    out = assign_block_ids([left, right], passages=road)
    assert {p.vineyard_id for p in out} == {"V01", "V02"}


def test_assign_row_ids_keeps_per_tile_geometry():
    vines = [
        ProjectedPoly(
            kind="vineyard",
            vineyard_id="V01",
            coords=[(0, 0), (1, 0), (1, 1), (0, 1)],
            tile="siret3_r001_c001.tif",
        )
    ]
    r1 = ProjectedPoly(kind="row", coords=[(1, 2), (9.2, 2)], tile="siret3_r001_c001.tif")
    r2 = ProjectedPoly(kind="row", coords=[(10.0, 2), (18, 2)], tile="siret3_r001_c002.tif")
    r3 = ProjectedPoly(kind="row", coords=[(1, 4.7), (18, 4.7)], tile="siret3_r001_c001.tif")
    out = assign_row_ids(vines + [r1, r2, r3], join_m=1.0)
    rows = [p for p in out if p.kind == "row"]
    assert len(rows) == 3
    assert {r.tile for r in rows} == {"siret3_r001_c001.tif", "siret3_r001_c002.tif"}
    shared = {r.row_id for r in rows if abs(r.coords[0][1] - 2) < 0.2}
    assert len(shared) == 1
    assert all(r.row_id.startswith("V01-R") for r in rows)


def test_rows_and_gap_structure_on_synthetic_grid():
    row_a = [_plant(i * 1.2, 0.0) for i in range(6)]
    row_b = [_plant(0.0, 2.7), _plant(1.2, 2.7), _plant(8.0, 2.7), _plant(9.2, 2.7)]
    vines = assign_block_ids(row_a + row_b)
    rows = rows_from_canopies(vines)
    assert len(rows) == 2
    structs = sorted(r.row_structure for r in rows)
    assert structs == ["disrupted", "regular"]
    inter = interrows_from_rows(rows, vines)
    assert len(inter) == 1
    assert inter[0].kind == "interrow_area"


def test_derive_does_not_merge_canopies():
    vines = assign_block_ids([_plant(i * 1.2, 0.0) for i in range(5)])
    out = derive_from_canopies(vines)
    assert sum(1 for p in out if p.kind == "vineyard") == 5


def test_derive_join_m_bridges_detection_gap_but_not_roads():
    left = _plant(0.0, 0.0)
    right = _plant(10.5, 0.0)
    default = [p for p in derive_from_canopies([left, right]) if p.kind == "vineyard"]
    assert len({p.vineyard_id for p in default}) == 2
    merged = [p for p in derive_from_canopies([left, right], join_m=12.0) if p.kind == "vineyard"]
    assert len({p.vineyard_id for p in merged}) == 1
    road = [[(5.0, -8.0), (6.0, -8.0), (6.0, 8.0), (5.0, 8.0), (5.0, -8.0)]]
    split = [
        p
        for p in derive_from_canopies([left, right], join_m=15.0, passages=road)
        if p.kind == "vineyard"
    ]
    assert len({p.vineyard_id for p in split}) == 2


@pytest.mark.skipif(not EXAMPLE_ZIP.is_file(), reason="official example ZIP missing")
def test_derive_on_official_example_canopies():
    images = parse_cvat_zip(EXAMPLE_ZIP)
    canopies: list[ProjectedPoly] = []
    for im in images:
        tile = TILES / im.name
        if not tile.is_file():
            pytest.skip(f"missing tile {im.name}")
        for shape in im.shapes:
            if shape.label != "vineyard":
                continue
            canopies.append(
                ProjectedPoly(
                    kind="vineyard",
                    coords=pixels_to_xy(tile, shape.points),
                    tile=im.name,
                )
            )
    out = derive_from_canopies(canopies, tiles_dir=TILES)
    vines = [p for p in out if p.kind == "vineyard"]
    assert len(vines) == 650
    by_tile: dict[str, list[ProjectedPoly]] = {}
    for p in out:
        by_tile.setdefault(p.tile, []).append(p)

    t01 = by_tile["siret3_r021_c012.tif"]
    t02 = by_tile["siret3_r006_c004.tif"]
    assert sum(1 for p in t01 if p.kind == "vineyard") == 399
    assert sum(1 for p in t02 if p.kind == "vineyard") == 251
    assert sum(1 for p in t01 if p.kind == "row") == 25
    assert sum(1 for p in t02 if p.kind == "row") == 26
    assert sum(1 for p in t01 if p.kind == "interrow_area") == 24
    assert sum(1 for p in t02 if p.kind == "interrow_area") == 25
    assert len({p.vineyard_id for p in t01}) == 1
    assert len({p.vineyard_id for p in t02}) == 1
    assert len({p.vineyard_id for p in vines}) == 2
    # Official 5 m rule on centroids; the example ZIP uses extra human judgment.
    assert any(p.row_structure == "disrupted" for p in t02 if p.kind == "row")
    covers_01 = {p.interrow_cover for p in t01 if p.kind == "interrow_area"}
    assert covers_01 <= {"bare_soil", "mixed", "vegetation", "unassessable"}
    assert "bare_soil" in covers_01
    covers_02 = {p.interrow_cover for p in t02 if p.kind == "interrow_area"}
    assert covers_02 & {"bare_soil", "mixed"}

    from shapely.geometry import Polygon

    for tile_items in (t01, t02):
        for p in tile_items:
            if p.kind != "interrow_area":
                continue
            poly = Polygon(p.coords)
            assert poly.area > 1.0
            assert poly.is_valid or poly.buffer(0).is_valid
