"""Cross-tile vineyard / row IDs after projection to EPSG:32635."""

from __future__ import annotations

import hashlib
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


def stitch_vineyards(
    items: list[ProjectedPoly],
    *,
    iou_threshold: float = 0.2,
    min_overlap_m2: float = 8.0,
) -> list[ProjectedPoly]:
    vines = [p for p in items if p.kind == "vineyard"]
    rest = [p for p in items if p.kind != "vineyard"]
    n = len(vines)
    _, find, union = _union_find(n)
    for i in range(n):
        for j in range(i + 1, n):
            inter = _intersection_area(vines[i].coords, vines[j].coords)
            if inter >= min_overlap_m2 or bbox_iou(vines[i].coords, vines[j].coords) >= iou_threshold:
                union(i, j)
    groups: dict[int, list[int]] = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    ranked = []
    for idxs in groups.values():
        pts = [pt for k in idxs for pt in vines[k].coords]
        cx, cy = centroid(pts)
        ranked.append((cx, cy, idxs, pts))
    ranked.sort(key=lambda t: (t[0], t[1]))
    out: list[ProjectedPoly] = []
    for seq, (cx, cy, idxs, pts) in enumerate(ranked, start=1):
        vid = f"V-{seq:04d}"
        extras = {"hash": stable_hash_id("V", cx, cy), "n_parts": len(idxs)}
        tiles = sorted({vines[k].tile for k in idxs})
        out.append(
            ProjectedPoly(
                kind="vineyard",
                coords=pts,
                tile=",".join(tiles),
                vineyard_id=vid,
                extras=extras,
            )
        )
    out.extend(rest)
    return out


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
        by_v.setdefault(r.vineyard_id or "V-0000", []).append(r)

    assigned: list[ProjectedPoly] = []
    for vid, group in by_v.items():
        n = len(group)
        _, find, union = _union_find(n)
        for i in range(n):
            for j in range(i + 1, n):
                if endpoint_gap(group[i].coords, group[j].coords) <= join_m:
                    union(i, j)
        clusters: dict[int, list[int]] = {}
        for i in range(n):
            clusters.setdefault(find(i), []).append(i)
        scored = []
        for idxs in clusters.values():
            pts = [pt for k in idxs for pt in group[k].coords]
            cx, cy = centroid(pts)
            scored.append((cx, cy, idxs, pts))
        scored.sort(key=lambda t: (t[0], t[1]))
        for seq, (cx, cy, idxs, pts) in enumerate(scored, start=1):
            rid = f"R-{vid}-{seq:02d}"
            tiles = sorted({group[k].tile for k in idxs})
            assigned.append(
                ProjectedPoly(
                    kind="row",
                    coords=pts,
                    tile=",".join(tiles),
                    vineyard_id=vid,
                    row_id=rid,
                    extras={"hash": stable_hash_id("R", cx, cy), "n_parts": len(idxs)},
                )
            )
    return vines + assigned + other
