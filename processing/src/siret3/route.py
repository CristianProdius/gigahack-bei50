"""Closed inspection walk on a passable graph (inter-row + authorised passages)."""

from __future__ import annotations

import json
from pathlib import Path

from . import START_TOLERANCE_M
from .ids import centroid


def _dist(a: tuple[float, float], b: tuple[float, float]) -> float:
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def _point_in_ring(pt: tuple[float, float], ring: list[tuple[float, float]]) -> bool:
    """Ray-cast even-odd. ring in EPSG:32635."""
    x, y = pt
    inside = False
    pts = ring if ring[0] == ring[-1] else ring + [ring[0]]
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        if (y1 > y) != (y2 > y):
            xing = (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1
            if x < xing:
                inside = not inside
    return inside


def is_passable(
    pt: tuple[float, float],
    interrows: list[list[tuple[float, float]]],
    passages: list[list[tuple[float, float]]],
    forbidden: list[list[tuple[float, float]]],
) -> bool:
    if any(_point_in_ring(pt, z) for z in forbidden):
        return False
    return any(_point_in_ring(pt, p) for p in interrows + passages)


def snap_start(
    start: tuple[float, float],
    nodes: list[tuple[float, float]],
    tolerance_m: float = START_TOLERANCE_M,
) -> tuple[float, float]:
    if not nodes:
        raise ValueError("Passable graph has no nodes")
    nearest = min(nodes, key=lambda n: _dist(start, n))
    gap = _dist(start, nearest)
    if gap > tolerance_m:
        raise ValueError(
            f"Start is {gap:.2f} m from the passable graph (limit {tolerance_m} m)"
        )
    return nearest


def _nearest_neighbor_tour(nodes: list[tuple[float, float]], start: tuple[float, float]) -> list[tuple[float, float]]:
    remaining = list(nodes)
    remaining.remove(start)
    tour = [start]
    cur = start
    while remaining:
        nxt = min(remaining, key=lambda n: _dist(cur, n))
        remaining.remove(nxt)
        tour.append(nxt)
        cur = nxt
    tour.append(start)
    return tour


def closed_walk(
    waypoints: list[tuple[float, float]],
    start: tuple[float, float],
    *,
    interrows: list[list[tuple[float, float]]] | None = None,
    passages: list[list[tuple[float, float]]] | None = None,
    forbidden: list[list[tuple[float, float]]] | None = None,
    tolerance_m: float = START_TOLERANCE_M,
) -> list[tuple[float, float]]:
    """
    Closed walk through waypoints.

    When networkx is installed we build an all-pairs shortest-path metric
    on a complete graph of waypoints (edge = Euclidean, later replace with
    lattice shortest paths). Fallback is nearest-neighbour.
    """
    interrows = interrows or []
    passages = passages or []
    forbidden = forbidden or []
    nodes = list(waypoints)
    if start not in nodes:
        nodes.append(start)
    depot = snap_start(start, nodes, tolerance_m)

    # Reject waypoints inside forbidden zones.
    kept = []
    for n in nodes:
        if forbidden and any(_point_in_ring(n, z) for z in forbidden):
            continue
        kept.append(n)
    if depot not in kept:
        kept.append(depot)

    try:
        import networkx as nx
        from networkx.algorithms.approximation import traveling_salesman_problem

        g = nx.Graph()
        for i, a in enumerate(kept):
            for j, b in enumerate(kept):
                if i < j:
                    g.add_edge(a, b, weight=_dist(a, b))
        tour = traveling_salesman_problem(g, cycle=True, weight="weight")
        # rotate to depot
        if depot in tour:
            k = tour.index(depot)
            tour = tour[k:] + tour[1:k] + [depot]
        if tour[0] != tour[-1]:
            tour = list(tour) + [tour[0]]
        return [(float(x), float(y)) for x, y in tour]
    except Exception:
        return _nearest_neighbor_tour(kept, depot)


def write_route_geojson(
    coords_32635: list[tuple[float, float]],
    out_path: Path,
    *,
    start: tuple[float, float] | None = None,
) -> None:
    """Write WGS84 LineString. Input coords are EPSG:32635."""
    from .crs import from_work_xy

    lonlat = [from_work_xy(x, y) for x, y in coords_32635]
    length = 0.0
    for a, b in zip(coords_32635, coords_32635[1:]):
        length += ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5
    start_ll = from_work_xy(*(start or coords_32635[0]))
    fc = {
        "type": "FeatureCollection",
        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "kind": "route",
                    "closed": True,
                    "length_m": round(length, 3),
                    "crs_measured": "EPSG:32635",
                    "start_tolerance_m": START_TOLERANCE_M,
                },
                "geometry": {"type": "LineString", "coordinates": [list(p) for p in lonlat]},
            },
            {
                "type": "Feature",
                "properties": {"kind": "start"},
                "geometry": {"type": "Point", "coordinates": list(start_ll)},
            },
        ],
    }
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(fc, indent=2), encoding="utf-8")


def sample_waypoints_from_centroids(polys: list[list[tuple[float, float]]]) -> list[tuple[float, float]]:
    return [centroid(p) for p in polys if p]
