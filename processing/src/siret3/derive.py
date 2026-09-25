"""Rows, inter-rows, and attributes from individual canopy polygons."""

from __future__ import annotations

import math
from collections import defaultdict
from pathlib import Path

import numpy as np
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

from .georef import xy_to_pixels
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


def rows_from_canopies(vines: list[ProjectedPoly]) -> list[ProjectedPoly]:
    rows: list[ProjectedPoly] = []
    groups: dict[tuple[str | None, str], list[ProjectedPoly]] = defaultdict(list)
    for v in vines:
        if v.kind != "vineyard":
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
            ring = list(a.coords) + list(reversed(b.coords))
            if ring[0] != ring[-1]:
                ring.append(ring[0])
            poly = Polygon(ring)
            if not poly.is_valid or poly.is_empty:
                poly = poly.buffer(0)
            if (poly.is_empty or poly.area < 1.0) and len(a.coords) >= 2 and len(b.coords) >= 2:
                la, lb = LineString(a.coords), LineString(b.coords)
                dist = max(float(la.distance(lb)), 0.5)
                poly = la.buffer(dist, cap_style=2).intersection(lb.buffer(dist, cap_style=2))
            if not poly.is_empty and not canopy_union.is_empty:
                cut = poly.difference(canopy_union)
                if not cut.is_empty:
                    poly = cut
            if poly.geom_type == "MultiPolygon":
                poly = max(poly.geoms, key=lambda g: g.area)
            if poly.geom_type != "Polygon" or poly.is_empty:
                poly = Polygon(ring)
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
) -> list[ProjectedPoly]:
    vines = assign_block_ids(
        [p for p in items if p.kind == "vineyard"],
        passages=passages,
    )
    others = [p for p in items if p.kind != "vineyard"]
    rows = rows_from_canopies(vines)
    combined = assign_row_ids(vines + rows, join_m=2.0)
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
        try:
            import rasterio

            with rasterio.open(tile) as src:
                width, height = src.width, src.height
        except Exception:
            pass
        shapes: list[CvatShape] = []
        for p in feats:
            px = xy_to_pixels(tile, p.coords) if tile.is_file() else p.coords
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
                shapes.append(CvatShape(tag="polygon", label=label, points=px, attributes=attrs))
        images.append(CvatImage(name=name, width=width, height=height, shapes=shapes))
    return images
