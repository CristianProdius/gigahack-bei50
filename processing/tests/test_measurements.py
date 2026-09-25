from siret3.ids import ProjectedPoly
from siret3.measurements import summary_rows, write_csv


def _sq(x0, y0, x1, y1, kind="vineyard", vid="V01") -> ProjectedPoly:
    return ProjectedPoly(
        kind=kind,
        vineyard_id=vid,
        row_id="V01-R01" if kind == "row" else None,
        coords=[(x0, y0), (x1, y0), (x1, y1), (x0, y1)],
        tile="siret3_r001_c001.tif",
    )


def test_summary_union_not_sum_of_overlaps():
    a = _sq(0, 0, 10, 10)
    b = _sq(5, 0, 15, 10)
    rows = {r["kind"]: r for r in summary_rows([a, b])}
    assert float(rows["canopy_union"].get("area_m2")) == 150.0
    assert float(rows["canopy_union"].get("area_ha")) == 0.015
    assert int(rows["n_blocks"]["n_parts"]) == 1


def test_summary_row_count_and_length():
    r1 = ProjectedPoly(
        kind="row",
        vineyard_id="V01",
        row_id="V01-R01",
        coords=[(0, 0), (10, 0)],
        tile="t1.tif",
    )
    r2 = ProjectedPoly(
        kind="row",
        vineyard_id="V01",
        row_id="V01-R01",
        coords=[(10, 0), (20, 0)],
        tile="t2.tif",
    )
    r3 = ProjectedPoly(
        kind="row",
        vineyard_id="V01",
        row_id="V01-R02",
        coords=[(0, 3), (8, 3)],
        tile="t1.tif",
    )
    rows = {r["kind"]: r for r in summary_rows([r1, r2, r3])}
    assert int(rows["n_rows"]["n_parts"]) == 2
    assert float(rows["total_row_length"]["length_m"]) == 28.0
