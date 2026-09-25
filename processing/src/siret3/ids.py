"""Cross-tile vineyard / row IDs after projection to EPSG:32635."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass


@dataclass
class ProjectedPoly:
    """Polygon or line already in EPSG:32635. coords are [(x, y), ...]."""

    kind: str  # vineyard | row | interrow_area | waste
    coords: list[tuple[float, float]]
    tile: str
    score: float = 1.0
    vineyard_id: str | None = None
    row_id: str | None = None
    row_structure: str | None = None
    interrow_cover: str | None = None
    extras: dict | None = None


def centroid(coords: list[tuple[float, float]]) -> tuple[float, float]:
    if not coords:
        return (0.0, 0.0)
    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    return (sum(xs) / len(xs), sum(ys) / len(ys))


def bbox(coords: list[tuple[float, float]]) -> tuple[float, float, float, float]:
    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    return (min(xs), min(ys), max(xs), max(ys))


def _overlap_1d(a0: float, a1: float, b0: float, b1: float) -> float:
    return max(0.0, min(a1, b1) - max(a0, b0))


def bbox_iou(a: list[tuple[float, float]], b: list[tuple[float, float]]) -> float:
    ax0, ay0, ax1, ay1 = bbox(a)
    bx0, by0, bx1, by1 = bbox(b)
    iw = _overlap_1d(ax0, ax1, bx0, bx1)
    ih = _overlap_1d(ay0, ay1, by0, by1)
    inter = iw * ih
    if inter <= 0:
        return 0.0
    area_a = max(ax1 - ax0, 0.0) * max(ay1 - ay0, 0.0)
    area_b = max(bx1 - bx0, 0.0) * max(by1 - by0, 0.0)
    union = area_a + area_b - inter
    return inter / union if union else 0.0


def endpoint_gap(a: list[tuple[float, float]], b: list[tuple[float, float]]) -> float:
    """Smallest distance between any pair of endpoints (for row stitching)."""
    if not a or not b:
        return float("inf")
    ends_a = (a[0], a[-1])
    ends_b = (b[0], b[-1])
    best = float("inf")
    for pa in ends_a:
        for pb in ends_b:
            d = ((pa[0] - pb[0]) ** 2 + (pa[1] - pb[1]) ** 2) ** 0.5
            best = min(best, d)
    return best


def stable_hash_id(prefix: str, x: float, y: float, quantum_m: float = 0.5) -> str:
    qx = int(round(x / quantum_m))
    qy = int(round(y / quantum_m))
    digest = hashlib.sha1(f"{prefix}:{qx}:{qy}".encode("utf-8")).hexdigest()[:8]
    return f"{prefix}-{digest}"


def _union_find(n: int) -> tuple[list[int], callable, callable]:
    parent = list(range(n))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i: int, j: int) -> None:
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[rj] = ri

    return parent, find, union


def _intersection_area(a: list[tuple[float, float]], b: list[tuple[float, float]]) -> float:
    ax0, ay0, ax1, ay1 = bbox(a)
    bx0, by0, bx1, by1 = bbox(b)
    return _overlap_1d(ax0, ax1, bx0, bx1) * _overlap_1d(ay0, ay1, by0, by1)


def _is_xy(pt) -> bool:
    return isinstance(pt, (tuple, list)) and len(pt) >= 2 and isinstance(pt[0], (int, float))


def _passage_polygon(spec):
    """Ring [(x,y), ...] or (exterior, holes) with vineyard interiors as holes."""
    from shapely.geometry import Polygon

    if not spec:
        return None
    if _is_xy(spec[0]):
        if len(spec) < 3:
            return None
        poly = Polygon(spec)
    else:
        exterior = spec[0]
        holes = spec[1] if len(spec) > 1 else []
        if not exterior or len(exterior) < 3:
            return None
        poly = Polygon(exterior, holes or [])
    if not poly.is_valid:
        poly = poly.buffer(0)
    return poly if not poly.is_empty else None


def _segment_hits_passages(
    a: tuple[float, float],
    b: tuple[float, float],
    passages: list | None,
) -> bool:
    if not passages:
        return False
    from shapely.geometry import LineString

    seg = LineString([a, b])
    for spec in passages:
        poly = _passage_polygon(spec)
        if poly is not None and seg.intersects(poly):
            return True
    return False


def assign_block_ids(
    items: list[ProjectedPoly],
    *,
    join_m: float = 6.0,
    passages: list | None = None,
) -> list[ProjectedPoly]:
    """Assign V01, V02, … to plants. Keep one polygon per plant."""
    vines = [p for p in items if p.kind == "vineyard"]
    rest = [p for p in items if p.kind != "vineyard"]
    if not vines:
        return list(items)
    cents = [centroid(v.coords) for v in vines]
    n = len(vines)
    _, find, union = _union_find(n)
    for i in range(n):
        for j in range(i + 1, n):
            d = ((cents[i][0] - cents[j][0]) ** 2 + (cents[i][1] - cents[j][1]) ** 2) ** 0.5
            if d <= join_m and not _segment_hits_passages(cents[i], cents[j], passages):
                union(i, j)
    groups: dict[int, list[int]] = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    ranked = []
    for idxs in groups.values():
        cx = sum(cents[k][0] for k in idxs) / len(idxs)
        cy = sum(cents[k][1] for k in idxs) / len(idxs)
        ranked.append((cx, cy, idxs))
    ranked.sort(key=lambda t: (t[0], t[1]))
    id_of = {}
    for seq, (_cx, _cy, idxs) in enumerate(ranked, start=1):
        vid = f"V{seq:02d}"
        for k in idxs:
            id_of[k] = vid
    out: list[ProjectedPoly] = []
    for i, vine in enumerate(vines):
        vine.vineyard_id = id_of[i]
        extras = dict(vine.extras or {})
        extras["hash"] = stable_hash_id("V", *cents[i])
        vine.extras = extras
        out.append(vine)
    out.extend(rest)
    return out


def stitch_vineyards(
    items: list[ProjectedPoly],
    *,
    iou_threshold: float = 0.2,
    min_overlap_m2: float = 8.0,
) -> list[ProjectedPoly]:
    """Deprecated alias: IDs only, geometries stay one-plant-per-polygon."""
    del iou_threshold, min_overlap_m2
    return assign_block_ids(items)


def _row_heading(coords: list[tuple[float, float]]) -> float:
    if len(coords) < 2:
        return 0.0
    dx = coords[-1][0] - coords[0][0]
    dy = coords[-1][1] - coords[0][1]
    return math.atan2(dy, dx) % math.pi


def _heading_close(a: float, b: float, tol: float = 0.26) -> bool:
    diff = abs(a - b) % math.pi
    diff = min(diff, math.pi - diff)
    return diff <= tol


def _perp_offset(coords: list[tuple[float, float]], heading: float) -> float:
    cx, cy = centroid(coords)
    return -cx * math.sin(heading) + cy * math.cos(heading)


def assign_row_ids(
    items: list[ProjectedPoly],
    *,
    join_m: float = 1.0,
) -> list[ProjectedPoly]:
    vines = [p for p in items if p.kind == "vineyard" and p.vineyard_id]
    rows = [p for p in items if p.kind == "row"]
    other = [p for p in items if p.kind not in {"vineyard", "row"}]

    def nearest_vine(coords: list[tuple[float, float]]) -> str | None:
        cx, cy = centroid(coords)
        best_id, best_d = None, float("inf")
        for v in vines:
            vx, vy = centroid(v.coords)
            d = ((cx - vx) ** 2 + (cy - vy) ** 2) ** 0.5
            if d < best_d:
                best_d, best_id = d, v.vineyard_id
        return best_id

    for r in rows:
        r.vineyard_id = r.vineyard_id or nearest_vine(r.coords)

    by_v: dict[str, list[ProjectedPoly]] = {}
    for r in rows:
        by_v.setdefault(r.vineyard_id or "V00", []).append(r)

    for vid, group in by_v.items():
        n = len(group)
        _, find, union = _union_find(n)
        for i in range(n):
            for j in range(i + 1, n):
                if group[i].tile == group[j].tile:
                    continue
                hi = _row_heading(group[i].coords)
                hj = _row_heading(group[j].coords)
                if _heading_close(hi, hj) and abs(
                    _perp_offset(group[i].coords, hi) - _perp_offset(group[j].coords, hi)
                ) <= 1.5:
                    union(i, j)
        clusters: dict[int, list[int]] = {}
        for i in range(n):
            clusters.setdefault(find(i), []).append(i)
        scored = []
        for idxs in clusters.values():
            pts = [pt for k in idxs for pt in group[k].coords]
            cx, cy = centroid(pts)
            scored.append((cx, cy, idxs))
        scored.sort(key=lambda t: (t[0], t[1]))
        for seq, (cx, cy, idxs) in enumerate(scored, start=1):
            rid = f"{vid}-R{seq:02d}"
            for k in idxs:
                row = group[k]
                row.row_id = rid
                extras = dict(row.extras or {})
                extras["hash"] = stable_hash_id("R", cx, cy)
                extras["n_parts"] = len(idxs)
                row.extras = extras
    return vines + rows + other
