from siret3.ids import (
    ProjectedPoly,
    assign_row_ids,
    bbox_iou,
    endpoint_gap,
    stable_hash_id,
    stitch_vineyards,
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


def test_stitch_merges_overlapping_tiles():
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
    out = stitch_vineyards([left, right, far])
    vines = [p for p in out if p.kind == "vineyard"]
    assert len(vines) == 2
    ids = {v.vineyard_id for v in vines}
    assert ids == {"V-0001", "V-0002"}
    merged = next(v for v in vines if "c001" in v.tile)
    assert "siret3_r001_c002.tif" in merged.tile


def test_row_ids_join_across_seam():
    vine = ProjectedPoly(
        kind="vineyard",
        vineyard_id="V-0001",
        coords=[(0, 0), (20, 0), (20, 6), (0, 6)],
        tile="siret3_r001_c001.tif",
    )
    r1 = ProjectedPoly(kind="row", coords=[(1, 2), (9.2, 2)], tile="siret3_r001_c001.tif")
    r2 = ProjectedPoly(kind="row", coords=[(10.0, 2), (18, 2)], tile="siret3_r001_c002.tif")
    r3 = ProjectedPoly(kind="row", coords=[(1, 4), (18, 4)], tile="siret3_r001_c001.tif")
    out = assign_row_ids([vine, r1, r2, r3], join_m=1.0)
    rows = [p for p in out if p.kind == "row"]
    assert len(rows) == 2
    assert {r.row_id for r in rows} == {"R-V-0001-01", "R-V-0001-02"}
