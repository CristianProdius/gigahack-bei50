"""Rows, inter-rows, and attributes from individual canopy polygons."""

from __future__ import annotations

import math
from collections import defaultdict
from pathlib import Path

import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from .georef import xy_to_pixels_once
from .ids import ProjectedPoly, _row_heading, assign_block_ids, assign_row_ids, centroid
from .cvat11 import CvatImage, CvatShape

GAP_M = 5.0
ROW_CLUSTER_M = 1.2
EXG_THRESHOLD = 0.08


def _heading_from_nn(centroids: list[tuple[float, float]]) -> float:
    if len(centroids) < 2:
        return 0.0
    pts = np.asarray(centroids, dtype=float)
    angles: list[float] = []
    for i, p in enumerate(pts):
        d = np.linalg.norm(pts - p, axis=1)
        d[i] = np.inf
        j = int(np.argmin(d))
        if not np.isfinite(d[j]) or d[j] > 3.0:
            continue
        dx, dy = pts[j] - p
        angles.append(math.atan2(float(dy), float(dx)) % math.pi)
    if not angles:
        centered = pts - pts.mean(axis=0)
        cov = np.cov(centered.T) if len(pts) > 1 else np.eye(2)
        vals, vecs = np.linalg.eigh(cov)
        vx, vy = vecs[:, int(np.argmax(vals))]
        return math.atan2(float(vy), float(vx)) % math.pi
    s = sum(math.sin(2 * a) for a in angles)
    c = sum(math.cos(2 * a) for a in angles)
    return (0.5 * math.atan2(s, c)) % math.pi


def _perp_coord(pt: tuple[float, float], heading: float) -> float:
    return -pt[0] * math.sin(heading) + pt[1] * math.cos(heading)


def _along_coord(pt: tuple[float, float], heading: float) -> float:
    return pt[0] * math.cos(heading) + pt[1] * math.sin(heading)


def _cluster_1d(values: list[float], gap: float) -> list[list[int]]:
    order = sorted(range(len(values)), key=lambda i: values[i])
    groups: list[list[int]] = [[order[0]]]
    for i in order[1:]:
        if values[i] - values[groups[-1][-1]] <= gap:
            groups[-1].append(i)
        else:
            groups.append([i])
    return groups


def _line_from_points(pts: list[tuple[float, float]], heading: float) -> list[tuple[float, float]]:
    along = [_along_coord(p, heading) for p in pts]
    mean = (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))
    ux, uy = math.cos(heading), math.sin(heading)
    a0, a1 = min(along), max(along)
    mean_a = _along_coord(mean, heading)
    p0 = (mean[0] + (a0 - mean_a) * ux, mean[1] + (a0 - mean_a) * uy)
    p1 = (mean[0] + (a1 - mean_a) * ux, mean[1] + (a1 - mean_a) * uy)
    return [p0, p1]


def _structure_from_gaps(pts: list[tuple[float, float]], heading: float) -> str:
    if len(pts) < 2:
        return "regular"
    along = sorted(_along_coord(p, heading) for p in pts)
    for a, b in zip(along, along[1:]):
        if b - a >= GAP_M:
            return "disrupted"
    return "regular"


def row_axis_from_strip(coords: list[tuple[float, float]]) -> list[tuple[float, float]] | None:
    if len(coords) < 4:
        return None
    poly = Polygon(coords)
    if not poly.is_valid:
        poly = poly.buffer(0)
    if poly.is_empty:
        return None
    ring = list(poly.minimum_rotated_rectangle.exterior.coords)
    edges = []
    for a, b in zip(ring, ring[1:]):
        d = ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5
        edges.append((d, a, b))
    if len(edges) < 4:
        return None
    edges.sort(key=lambda e: e[0])
    short_a, short_b = edges[0], edges[1]
    mid = lambda e: ((e[1][0] + e[2][0]) / 2.0, (e[1][1] + e[2][1]) / 2.0)
    return [mid(short_a), mid(short_b)]


def rows_from_canopies(vines: list[ProjectedPoly]) -> list[ProjectedPoly]:
    rows: list[ProjectedPoly] = []
    groups: dict[tuple[str | None, str], list[ProjectedPoly]] = defaultdict(list)
    for v in vines:
        if v.kind != "vineyard":
            continue
        if (v.extras or {}).get("label") == "vine_row":
            axis = row_axis_from_strip(v.coords)
            if axis:
                rows.append(
                    ProjectedPoly(
                        kind="row",
                        coords=axis,
                        tile=v.tile,
                        vineyard_id=v.vineyard_id,
                        row_structure="regular",
                    )
                )
                continue
        groups[(v.vineyard_id, v.tile)].append(v)
    for (vid, tile), plants in groups.items():
        cents = [centroid(p.coords) for p in plants]
        heading = _heading_from_nn(cents)
        perp = [_perp_coord(c, heading) for c in cents]
        for idxs in _cluster_1d(perp, ROW_CLUSTER_M):
            cluster_pts = [cents[i] for i in idxs]
            if len(cluster_pts) == 1:
                ux, uy = math.cos(heading), math.sin(heading)
                p = cluster_pts[0]
                coords = [(p[0] - 0.6 * ux, p[1] - 0.6 * uy), (p[0] + 0.6 * ux, p[1] + 0.6 * uy)]
            else:
                coords = _line_from_points(cluster_pts, heading)
            rows.append(
                ProjectedPoly(
                    kind="row",
                    coords=coords,
                    tile=tile,
                    vineyard_id=vid,
                    row_structure=_structure_from_gaps(cluster_pts, heading),
                )
            )
    return rows


def _xy_at_along(
    coords: list[tuple[float, float]], heading: float, along: float
) -> tuple[float, float]:
    p0, p1 = coords[0], coords[-1]
    ux, uy = math.cos(heading), math.sin(heading)
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    den = dx * ux + dy * uy
    if abs(den) < 1e-6:
        return p0
    t = (along - _along_coord(p0, heading)) / den
    return (p0[0] + t * dx, p0[1] + t * dy)


def _overlap_corridor(
    a: list[tuple[float, float]],
    b: list[tuple[float, float]],
    heading: float,
    min_len: float = 1.0,
) -> list[tuple[float, float]] | None:
    if len(a) < 2 or len(b) < 2:
        return None
    aa = [_along_coord(p, heading) for p in a]
    ab = [_along_coord(p, heading) for p in b]
    pad = 1.5
    lo = max(min(aa) - pad, min(ab) - pad)
    hi = min(max(aa) + pad, max(ab) + pad)
    # keep the corridor inside the union of the two rows, not far past both
    union_lo = min(min(aa), min(ab))
    union_hi = max(max(aa), max(ab))
    lo = max(lo, union_lo)
    hi = min(hi, union_hi)
    if hi - lo < min_len:
        return None
    pa0 = _xy_at_along(a, heading, lo)
    pa1 = _xy_at_along(a, heading, hi)
    pb1 = _xy_at_along(b, heading, hi)
    pb0 = _xy_at_along(b, heading, lo)
    return [pa0, pa1, pb1, pb0, pa0]


def interrows_from_rows(
    rows: list[ProjectedPoly],
    vines: list[ProjectedPoly],
) -> list[ProjectedPoly]:
    inter: list[ProjectedPoly] = []
    groups: dict[tuple[str | None, str], list[ProjectedPoly]] = defaultdict(list)
    plants: dict[tuple[str | None, str], list[ProjectedPoly]] = defaultdict(list)
    for r in rows:
        groups[(r.vineyard_id, r.tile)].append(r)
    for v in vines:
        plants[(v.vineyard_id, v.tile)].append(v)
    for key, tile_rows in groups.items():
        if len(tile_rows) < 2:
            continue
        heading = _row_heading(tile_rows[0].coords) if len(tile_rows[0].coords) >= 2 else 0.0
        tile_rows = sorted(tile_rows, key=lambda r: _perp_coord(centroid(r.coords), heading))
        canopy_union = unary_union(
            [Polygon(p.coords).buffer(0.12) for p in plants.get(key, []) if len(p.coords) >= 3]
        )
        for a, b in zip(tile_rows, tile_rows[1:]):
            ring = _overlap_corridor(a.coords, b.coords, heading)
            if ring is None:
                continue
            poly = Polygon(ring)
            if not poly.is_valid or poly.is_empty:
                poly = poly.buffer(0)
            if not poly.is_empty and not canopy_union.is_empty:
                cut = poly.difference(canopy_union)
                if not cut.is_empty:
                    poly = cut
            if poly.geom_type == "MultiPolygon":
                poly = max(poly.geoms, key=lambda g: g.area)
            if not poly.is_valid:
                poly = poly.buffer(0)
            if poly.is_empty or poly.geom_type != "Polygon":
                continue
            coords = [(float(x), float(y)) for x, y in poly.exterior.coords]
            inter.append(
                ProjectedPoly(
                    kind="interrow_area",
                    coords=coords,
                    tile=a.tile,
                    vineyard_id=a.vineyard_id,
                )
            )
    return inter


def classify_cover(poly: ProjectedPoly, tile_path: Path) -> str:
    import rasterio
    from rasterio.features import geometry_mask
    from shapely.geometry import mapping

    geom = Polygon(poly.coords)
    if not geom.is_valid:
        geom = geom.buffer(0)
    if geom.is_empty:
        return "unassessable"
    with rasterio.open(tile_path) as src:
        mask = geometry_mask(
            [mapping(geom)],
            transform=src.transform,
            invert=True,
            out_shape=(src.height, src.width),
        )
        if not mask.any():
            return "unassessable"
        count = min(src.count, 3)
        bands = src.read(list(range(1, count + 1)))
        r = bands[0][mask].astype(float)
        g = bands[1][mask].astype(float) if count > 1 else r
        b = bands[2][mask].astype(float) if count > 2 else r
        denom = r + g + b
        exg = np.divide(2 * g - r - b, denom, out=np.zeros_like(r), where=denom > 0)
        veg = float((exg > EXG_THRESHOLD).mean())
    if veg < 0.25:
        return "bare_soil"
    if veg > 0.75:
        return "vegetation"
    return "mixed"


def _assign_waste_ids(items: list[ProjectedPoly]) -> None:
    vines = [p for p in items if p.kind == "vineyard" and p.vineyard_id]
    if not vines:
        return
    vine_c = [(p.vineyard_id, centroid(p.coords)) for p in vines]
    for w in items:
        if w.kind != "waste":
            continue
        wc = centroid(w.coords)
        best_id, best_d = None, float("inf")
        for vid, vc in vine_c:
            d = ((wc[0] - vc[0]) ** 2 + (wc[1] - vc[1]) ** 2) ** 0.5
            if d < best_d:
                best_d, best_id = d, vid
        w.vineyard_id = best_id if best_d <= 10.0 else None


def derive_from_canopies(
    items: list[ProjectedPoly],
    *,
    tiles_dir: Path | None = None,
    passages: list[list[tuple[float, float]]] | None = None,
    join_m: float = 6.0,
    row_join_m: float = 2.0,
) -> list[ProjectedPoly]:
    vines = assign_block_ids(
        [p for p in items if p.kind == "vineyard"],
        join_m=join_m,
        passages=passages,
    )
    others = [p for p in items if p.kind != "vineyard"]
    rows = rows_from_canopies(vines)
    combined = assign_row_ids(vines + rows, join_m=row_join_m)
    vines = [p for p in combined if p.kind == "vineyard"]
    rows = [p for p in combined if p.kind == "row"]
    inter = interrows_from_rows(rows, vines)
    if tiles_dir is not None:
        for poly in inter:
            tile = Path(tiles_dir) / poly.tile
            if tile.is_file():
                poly.interrow_cover = classify_cover(poly, tile)
            else:
                poly.interrow_cover = "unassessable"
    else:
        for poly in inter:
            poly.interrow_cover = poly.interrow_cover or "bare_soil"
    out = vines + rows + inter + others
    _assign_waste_ids(out)
    return out


def clip_simplify_ring(
    points: list[tuple[float, float]],
    width: int,
    height: int,
    tolerance: float,
) -> list[tuple[float, float]]:
    """Clip a ring to the tile and drop dense vertices for the 90 MiB ZIP cap."""
    if len(points) < 4:
        return points
    poly = Polygon(points)
    if not poly.is_valid:
        poly = poly.buffer(0)
    if poly.is_empty:
        return points
    clipped = poly.intersection(box(0.0, 0.0, float(width), float(height)))
    if clipped.is_empty:
        return points
    if clipped.geom_type == "MultiPolygon":
        clipped = max(clipped.geoms, key=lambda g: g.area)
    if clipped.geom_type != "Polygon":
        return points
    simple = clipped.simplify(tolerance, preserve_topology=True)
    if simple.is_empty or simple.geom_type != "Polygon":
        simple = clipped
    ring = [(float(x), float(y)) for x, y in simple.exterior.coords]
    return ring if len(ring) >= 4 else points


def images_from_projected(items: list[ProjectedPoly], tiles_dir: Path) -> list[CvatImage]:
    tiles_dir = Path(tiles_dir)
    by_tile: dict[str, list[ProjectedPoly]] = defaultdict(list)
    for p in items:
        if p.tile:
            by_tile[p.tile].append(p)
    images: list[CvatImage] = []
    for name, feats in sorted(by_tile.items()):
        tile = tiles_dir / name
        width = height = 2048
        inv = None
        try:
            import rasterio

            with rasterio.open(tile) as src:
                width, height = src.width, src.height
                inv = ~src.transform
        except Exception:
            pass
        shapes: list[CvatShape] = []
        for p in feats:
            if inv is not None:
                px = [tuple(map(float, inv @ (x, y))) for x, y in p.coords]
            elif tile.is_file():
                px = xy_to_pixels_once(tile, p.coords)
            else:
                px = p.coords
            attrs: dict[str, str] = {"vineyard_id": p.vineyard_id or ""}
            if p.kind == "row":
                attrs["row_id"] = p.row_id or ""
                attrs["row_structure"] = p.row_structure or "regular"
                shapes.append(CvatShape(tag="polyline", label="row", points=px, attributes=attrs))
            elif p.kind == "waste":
                xs = [c[0] for c in px]
                ys = [c[1] for c in px]
                shapes.append(
                    CvatShape(
                        tag="box",
                        label="waste",
                        xtl=min(xs),
                        ytl=min(ys),
                        xbr=max(xs),
                        ybr=max(ys),
                        attributes=attrs,
                    )
                )
            else:
                label = "interrow_area" if p.kind == "interrow_area" else "vineyard"
                if p.kind == "interrow_area":
                    attrs["interrow_cover"] = p.interrow_cover or "bare_soil"
                tol = 8.0 if p.kind == "interrow_area" else 2.0
                px = clip_simplify_ring(px, width, height, tol)
                shapes.append(CvatShape(tag="polygon", label=label, points=px, attributes=attrs))
        images.append(CvatImage(name=name, width=width, height=height, shapes=shapes))
    return images
