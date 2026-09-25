"""Closed inspection walk on a passable graph (inter-row + authorised passages)."""

from __future__ import annotations

import json
from pathlib import Path

from shapely.geometry import LineString, MultiPolygon, Point, Polygon
from shapely.ops import unary_union

from . import START_TOLERANCE_M
from .ids import centroid

OFFICIAL_START = (629504.70, 5220250.75)
VISIT_M = 2.0
ILLEGAL_MAX = 0.02


def _dist(a: tuple[float, float], b: tuple[float, float]) -> float:
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def _as_poly(
    ring: list[tuple[float, float]],
    holes: list[list[tuple[float, float]]] | None = None,
) -> Polygon | None:
    if len(ring) < 3:
        return None
    poly = Polygon(ring, holes or [])
    if not poly.is_valid:
        poly = poly.buffer(0)
    if poly.is_empty:
        return None
    return poly


def _as_ring(ring: list[tuple[float, float]]) -> Polygon | None:
    return _as_poly(ring)


def _point_in_ring(pt: tuple[float, float], ring: list[tuple[float, float]]) -> bool:
    poly = _as_ring(ring)
    if poly is None:
        return False
    return bool(poly.covers(Point(pt)))


def is_passable(
    pt: tuple[float, float],
    interrows: list[list[tuple[float, float]]],
    passages: list[list[tuple[float, float]]],
    forbidden: list[list[tuple[float, float]]],
) -> bool:
    if any(_point_in_ring(pt, z) for z in forbidden):
        return False
    return any(_point_in_ring(pt, p) for p in interrows + passages)


def passable_union(
    interrows: list[list[tuple[float, float]]],
    passages: list[list[tuple[float, float]]],
    forbidden: list[list[tuple[float, float]]],
):
    goods = [_as_ring(r) for r in interrows + passages]
    goods = [g for g in goods if g is not None]
    if not goods:
        return Polygon()
    ok = unary_union(goods)
    bads = [_as_ring(r) for r in forbidden]
    bads = [b for b in bads if b is not None]
    if bads:
        ok = ok.difference(unary_union(bads))
    if not ok.is_valid:
        ok = ok.buffer(0)
    return ok


def passable_from_items(items) -> Polygon:
    goods = []
    bads = []
    for p in items:
        holes = (p.extras or {}).get("holes") if getattr(p, "extras", None) else None
        geom = _as_poly(p.coords, holes)
        if geom is None:
            continue
        if p.kind in {"interrow_area", "passage"}:
            goods.append(geom)
        elif p.kind == "forbidden":
            bads.append(geom)
    if not goods:
        return Polygon()
    ok = unary_union(goods)
    if bads:
        ok = ok.difference(unary_union(bads))
    if not ok.is_valid:
        ok = ok.buffer(0)
    return ok


def illegal_length_fraction(
    coords: list[tuple[float, float]],
    passable,
    *,
    slop_m: float = 0.05,
) -> float:
    if len(coords) < 2:
        return 0.0
    if passable is None or passable.is_empty:
        return 1.0
    padded = passable.buffer(slop_m)
    total = 0.0
    illegal = 0.0
    for a, b in zip(coords, coords[1:]):
        hop = LineString([a, b])
        if hop.length <= 0:
            continue
        total += hop.length
        inside = hop.intersection(padded)
        legal = inside.length if not inside.is_empty else 0.0
        illegal += max(0.0, hop.length - legal)
    if total <= 0:
        return 0.0
    return max(0.0, min(1.0, illegal / total))


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
    if start in remaining:
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


def _graph_nodes(passable) -> list[tuple[float, float]]:
    geoms = list(passable.geoms) if isinstance(passable, MultiPolygon) else [passable]
    nodes: list[tuple[float, float]] = []
    for geom in geoms:
        if geom.is_empty:
            continue
        if hasattr(geom, "representative_point"):
            rp = geom.representative_point()
            nodes.append((float(rp.x), float(rp.y)))
        if hasattr(geom, "centroid"):
            c = geom.centroid
            nodes.append((float(c.x), float(c.y)))
        rings = []
        if hasattr(geom, "exterior"):
            rings.append(geom.exterior)
        if hasattr(geom, "interiors"):
            rings.extend(geom.interiors)
        for line in rings:
            n = max(int(line.length / 2.0), 4)
            for i in range(n):
                p = line.interpolate(i / n, normalized=True)
                nodes.append((float(p.x), float(p.y)))
    return nodes


def legal_path(
    a: tuple[float, float],
    b: tuple[float, float],
    passable,
) -> list[tuple[float, float]]:
    if a == b:
        return [a]
    if passable is None or passable.is_empty:
        return [a, b]
    if Point(a).distance(passable) <= VISIT_M:
        a = _project_onto_passable(a, passable)
    if Point(b).distance(passable) <= VISIT_M:
        b = _project_onto_passable(b, passable)
    padded = passable.buffer(0.35)
    seg = LineString([a, b])
    if padded.covers(seg):
        return [a, b]
    import networkx as nx

    nodes = [a, b] + _graph_nodes(passable)
    # unique-ish
    uniq: list[tuple[float, float]] = []
    seen = set()
    for n in nodes:
        key = (round(n[0], 2), round(n[1], 2))
        if key in seen:
            continue
        seen.add(key)
        uniq.append((float(n[0]), float(n[1])))
    g = nx.Graph()
    g.add_nodes_from(uniq)
    for i, p in enumerate(uniq):
        for q in uniq[i + 1 :]:
            hop = LineString([p, q])
            if hop.length > 40:
                continue
            if padded.covers(hop):
                g.add_edge(p, q, weight=hop.length)
    if a not in g or b not in g or not nx.has_path(g, a, b):
        raise ValueError("no legal path on passable inter-row ∪ passages")
    return [(float(x), float(y)) for x, y in nx.shortest_path(g, a, b, weight="weight")]


def _project_onto_passable(pt: tuple[float, float], passable) -> tuple[float, float]:
    p = Point(pt)
    if passable.covers(p):
        return pt
    from shapely.ops import nearest_points

    snapped = nearest_points(p, passable)[1]
    return (float(snapped.x), float(snapped.y))


def closed_walk(
    waypoints: list[tuple[float, float]],
    start: tuple[float, float],
    *,
    interrows: list[list[tuple[float, float]]] | None = None,
    passages: list[list[tuple[float, float]]] | None = None,
    forbidden: list[list[tuple[float, float]]] | None = None,
    tolerance_m: float = START_TOLERANCE_M,
    require_legal: bool = False,
    passable=None,
) -> list[tuple[float, float]]:
    interrows = interrows or []
    passages = passages or []
    forbidden = forbidden or []
    nodes = list(waypoints)
    if passable is None and (interrows or passages or forbidden):
        passable = passable_union(interrows, passages, forbidden)
    if passable is not None and not passable.is_empty:
        from shapely.ops import nearest_points

        snapped = nearest_points(Point(start), passable)[1]
        depot = (float(snapped.x), float(snapped.y))
        if _dist(start, depot) > tolerance_m:
            raise ValueError(
                f"Start is {_dist(start, depot):.2f} m from passable (limit {tolerance_m} m)"
            )
    else:
        if start not in nodes:
            nodes.append(start)
        depot = snap_start(start, nodes, tolerance_m)

    kept = []
    for n in nodes:
        if forbidden and any(_point_in_ring(n, z) for z in forbidden):
            continue
        kept.append(n)
    if depot not in kept:
        kept.append(depot)
    if passable is not None and not passable.is_empty:
        snapped: list[tuple[float, float]] = [depot]
        for n in kept:
            if n == depot:
                continue
            if Point(n).distance(passable) <= VISIT_M:
                snapped.append(_project_onto_passable(n, passable))
        kept = snapped

    try:
        import networkx as nx
        from networkx.algorithms.approximation import traveling_salesman_problem

        g = nx.Graph()
        for i, a in enumerate(kept):
            for j, b in enumerate(kept):
                if i < j:
                    g.add_edge(a, b, weight=_dist(a, b))
        tour = traveling_salesman_problem(g, cycle=True, weight="weight")
        if depot in tour:
            k = tour.index(depot)
            tour = tour[k:] + tour[1:k] + [depot]
        if tour[0] != tour[-1]:
            tour = list(tour) + [tour[0]]
        ordered = [(float(x), float(y)) for x, y in tour]
    except Exception:
        ordered = _nearest_neighbor_tour(kept, depot)

    if passable is not None and not passable.is_empty:
        stitched: list[tuple[float, float]] = []
        for a, b in zip(ordered, ordered[1:]):
            hop = legal_path(a, b, passable)
            if stitched and hop and hop[0] == stitched[-1]:
                stitched.extend(hop[1:])
            else:
                stitched.extend(hop)
        if stitched and stitched[0] != stitched[-1]:
            stitched.append(stitched[0])
        ordered = stitched or ordered
        frac = illegal_length_fraction(ordered, passable)
        if require_legal and frac > ILLEGAL_MAX:
            raise ValueError(
                f"{frac:.1%} of route is outside passable inter-row ∪ passages (limit 2%)"
            )
    return ordered


def write_route_geojson(
    coords_32635: list[tuple[float, float]],
    out_path: Path,
    *,
    start: tuple[float, float] | None = None,
) -> None:
    """Write one LineString in EPSG:32635 with planar length_m."""
    length = 0.0
    for a, b in zip(coords_32635, coords_32635[1:]):
        length += _dist(a, b)
    start_xy = start or (coords_32635[0] if coords_32635 else OFFICIAL_START)
    fc = {
        "type": "FeatureCollection",
        "name": "siret3_route",
        "crs": {"type": "name", "properties": {"name": "EPSG:32635"}},
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
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[float(x), float(y)] for x, y in coords_32635],
                },
            },
            {
                "type": "Feature",
                "properties": {"kind": "start"},
                "geometry": {"type": "Point", "coordinates": [float(start_xy[0]), float(start_xy[1])]},
            },
        ],
    }
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(fc, indent=2), encoding="utf-8")


def load_official_start(path: Path | None = None) -> tuple[float, float]:
    if path is None:
        return OFFICIAL_START
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    feat = data["features"][0]
    x, y = feat["geometry"]["coordinates"][:2]
    return (float(x), float(y))


def sample_waypoints_from_centroids(polys: list[list[tuple[float, float]]]) -> list[tuple[float, float]]:
    return [centroid(p) for p in polys if p]
