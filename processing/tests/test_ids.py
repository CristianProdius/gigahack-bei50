from siret3.ids import (
    ProjectedPoly,
    assign_block_ids,
    assign_row_ids,
    bbox_iou,
    endpoint_gap,
    stable_hash_id,
)


def test_bbox_iou_identical():
    sq = [(0, 0), (10, 0), (10, 10), (0, 10)]
    assert bbox_iou(sq, sq) == 1.0


def test_endpoint_gap_join():
    a = [(0, 0), (4, 0)]
    b = [(4.4, 0), (8, 0)]
    assert abs(endpoint_gap(a, b) - 0.4) < 1e-9


def test_stable_hash_is_stable():
    assert stable_hash_id("V", 100.2, 50.4) == stable_hash_id("V", 100.2, 50.4)
    assert stable_hash_id("V", 100.2, 50.4) != stable_hash_id("V", 900.0, 50.4)


def test_assign_block_ids_does_not_merge_polygons():
    left = ProjectedPoly(
        kind="vineyard",
        coords=[(0, 0), (8, 0), (8, 4), (0, 4)],
        tile="siret3_r001_c001.tif",
    )
    right = ProjectedPoly(
        kind="vineyard",
        coords=[(5, 0), (12, 0), (12, 4), (5, 4)],
        tile="siret3_r001_c002.tif",
    )
    far = ProjectedPoly(
        kind="vineyard",
        coords=[(80, 80), (90, 80), (90, 88), (80, 88)],
        tile="siret3_r002_c009.tif",
    )
    out = assign_block_ids([left, right, far])
    vines = [p for p in out if p.kind == "vineyard"]
    assert len(vines) == 3
    ids = {v.vineyard_id for v in vines}
    assert ids == {"V01", "V02"}
    near = {v.vineyard_id for v in vines if v.tile != "siret3_r002_c009.tif"}
    assert len(near) == 1


def test_row_ids_join_across_seam():
    vine = ProjectedPoly(
        kind="vineyard",
        vineyard_id="V01",
        coords=[(0, 0), (20, 0), (20, 6), (0, 6)],
        tile="siret3_r001_c001.tif",
    )
    r1 = ProjectedPoly(kind="row", coords=[(1, 2), (9.2, 2)], tile="siret3_r001_c001.tif")
    r2 = ProjectedPoly(kind="row", coords=[(10.0, 2), (18, 2)], tile="siret3_r001_c002.tif")
    r3 = ProjectedPoly(kind="row", coords=[(1, 4), (18, 4)], tile="siret3_r001_c001.tif")
    out = assign_row_ids([vine, r1, r2, r3], join_m=1.0)
    rows = [p for p in out if p.kind == "row"]
    assert len(rows) == 3
    assert {r.row_id for r in rows} == {"V01-R01", "V01-R02"}
    assert {r.tile for r in rows} == {"siret3_r001_c001.tif", "siret3_r001_c002.tif"}
