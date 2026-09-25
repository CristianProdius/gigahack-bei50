from siret3.ids import ProjectedPoly, _as_polygon, assign_row_ids
from siret3.interrow import colour_cover_guess, derive_interrows


def test_as_polygon_closes_ring():
    poly = _as_polygon([(0, 0), (10, 0), (10, 4), (0, 4)])
    assert not poly.is_empty
    assert poly.area == 40.0


def test_derive_interrows_from_two_rows():
    vine = ProjectedPoly(
        kind="vineyard",
        vineyard_id="V-0001",
        coords=[(0, 0), (20, 0), (20, 8), (0, 8), (0, 0)],
        tile="siret3_r001_c001.tif",
    )
    r1 = ProjectedPoly(kind="row", vineyard_id="V-0001", coords=[(1, 2), (19, 2)], tile="siret3_r001_c001.tif")
    r2 = ProjectedPoly(kind="row", vineyard_id="V-0001", coords=[(1, 6), (19, 6)], tile="siret3_r001_c001.tif")
    out = derive_interrows(assign_row_ids([vine, r1, r2]))
    inter = [p for p in out if p.kind == "interrow_area"]
    assert inter
    assert all(p.vineyard_id == "V-0001" for p in inter)
    assert all((p.extras or {}).get("interrow_cover") == "unknown" for p in inter)


def test_colour_cover_guess():
    assert colour_cover_guess((40, 120, 40)) == "grass"
    assert colour_cover_guess((140, 110, 50)) == "soil"
    assert colour_cover_guess((10, 10, 10)) == "unknown"
