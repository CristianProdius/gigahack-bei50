import json
from pathlib import Path

import pytest

from siret3.route import (
    closed_walk,
    illegal_length_fraction,
    is_passable,
    passable_union,
    snap_start,
    write_route_geojson,
)


OFFICIAL_START = (629504.70, 5220250.75)


def test_snap_start_within_five_metres():
    nodes = [(0.0, 0.0), (10.0, 0.0)]
    assert snap_start((3.0, 0.0), nodes) == (0.0, 0.0)


def test_snap_start_rejects_far_point():
    try:
        snap_start((40.0, 0.0), [(0.0, 0.0)])
    except ValueError as exc:
        assert "5" in str(exc) or "limit" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_forbidden_zone_not_passable():
    inter = [[(0, 0), (10, 0), (10, 10), (0, 10)]]
    forbidden = [[(4, 4), (6, 4), (6, 6), (4, 6)]]
    assert is_passable((1, 1), inter, [], forbidden) is True
    assert is_passable((5, 5), inter, [], forbidden) is False


def test_closed_walk_returns_to_start():
    pts = [(0.0, 0.0), (8.0, 0.0), (8.0, 6.0), (0.0, 6.0)]
    tour = closed_walk(pts, (0.1, 0.0))
    assert tour[0] == tour[-1]
    assert len(tour) >= 2


def test_illegal_fraction_zero_on_corridor():
    corridor = [(0, 0), (20, 0), (20, 4), (0, 4)]
    poly = passable_union([corridor], [], [])
    coords = [(1, 2), (19, 2)]
    assert illegal_length_fraction(coords, poly) < 0.01


def test_diagonal_through_hole_is_illegal():
    from shapely.geometry import Polygon

    donut = Polygon(
        [(0, 0), (20, 0), (20, 20), (0, 20)],
        [[(6, 6), (14, 6), (14, 14), (6, 14)]],
    )
    assert illegal_length_fraction([(2, 2), (18, 2)], donut) < 0.02
    assert illegal_length_fraction([(2, 2), (18, 18)], donut) > 0.2


def test_illegal_fraction_high_on_shortcut():
    corridor = [(0, 0), (20, 0), (20, 2), (0, 2)]
    poly = passable_union([corridor], [], [])
    coords = [(1, 1), (10, 40)]
    assert illegal_length_fraction(coords, poly) > 0.5


def test_closed_walk_stays_in_l_corridor():
    # L-shaped passage: east then north. Straight (1,1)->(18,18) is illegal.
    passage = [(0, 0), (20, 0), (20, 4), (4, 4), (4, 20), (0, 20)]
    start = (1.0, 2.0)
    target = (2.0, 18.0)
    tour = closed_walk(
        [target],
        start,
        interrows=[],
        passages=[passage],
        forbidden=[],
        require_legal=True,
    )
    assert tour[0] == tour[-1]
    poly = passable_union([], [passage], [])
    assert illegal_length_fraction(tour, poly) <= 0.02
    assert any(abs(p[1] - 18) < 2.0 and abs(p[0] - 2) < 2.0 for p in tour)


def test_write_route_geojson_is_32635(tmp_path: Path):
    out = tmp_path / "route.geojson"
    coords = [OFFICIAL_START, (OFFICIAL_START[0] + 10, OFFICIAL_START[1]), OFFICIAL_START]
    write_route_geojson(coords, out, start=OFFICIAL_START)
    data = json.loads(out.read_text())
    crs = data.get("crs", {}).get("properties", {}).get("name", "")
    assert "32635" in crs
    geom = data["features"][0]["geometry"]
    assert geom["type"] == "LineString"
    first = tuple(geom["coordinates"][0])
    last = tuple(geom["coordinates"][-1])
    assert abs(first[0] - OFFICIAL_START[0]) < 5
    assert abs(last[0] - OFFICIAL_START[0]) < 5
    assert first[0] > 1000  # metres, not lon
    assert "length_m" in data["features"][0]["properties"]
    assert len(data["features"]) == 1
    assert {f["geometry"]["type"] for f in data["features"]} == {"LineString"}


def test_write_route_geojson_role_farmer(tmp_path: Path):
    out = tmp_path / "route_farmer.geojson"
    coords = [OFFICIAL_START, (OFFICIAL_START[0] + 10, OFFICIAL_START[1]), OFFICIAL_START]
    write_route_geojson(coords, out, start=OFFICIAL_START, role="farmer")
    data = json.loads(out.read_text())
    assert len(data["features"]) == 1
    assert data["features"][0]["properties"]["role"] == "farmer"


def test_closed_walk_rejects_illegal_when_required():
    left = [(0, 0), (4, 0), (4, 2), (0, 2)]
    right = [(20, 0), (24, 0), (24, 2), (20, 2)]
    with pytest.raises(ValueError, match="legal path|2%"):
        closed_walk(
            [(22.0, 1.0)],
            (1.0, 1.0),
            interrows=[left, right],
            require_legal=True,
        )
