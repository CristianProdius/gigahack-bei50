"""Inspection targets from ≥ 5 m planting gaps. Not a Marcaj label."""

from __future__ import annotations

from collections import defaultdict

from .derive import GAP_M, _along_coord, _heading_from_nn
from .ids import ProjectedPoly, centroid


def inspections_from_canopies(items: list[ProjectedPoly]) -> list[ProjectedPoly]:
    plants_by_row: dict[str, list[ProjectedPoly]] = defaultdict(list)
    rows = [p for p in items if p.kind == "row"]
    vines = [p for p in items if p.kind == "vineyard"]
    if not rows:
        return []
    # Assign each plant to nearest row of the same vineyard.
    for v in vines:
        same = [r for r in rows if r.vineyard_id == v.vineyard_id] or rows
        vc = centroid(v.coords)
        nearest = min(same, key=lambda r: _dist(vc, centroid(r.coords)))
        rid = nearest.row_id or "UNK"
        plants_by_row[rid].append(v)

    out: list[ProjectedPoly] = []
    rows_by_id = {r.row_id: r for r in rows if r.row_id}
    for rid, plants in plants_by_row.items():
        row = rows_by_id.get(rid)
        if row is None or (row.row_structure or "regular") == "regular":
            # Still emit if a physical 5 m gap exists even if marked regular.
            pass
        cents = [centroid(p.coords) for p in plants]
        if len(cents) < 2:
            continue
        heading = _heading_from_nn(cents)
        ordered = sorted(cents, key=lambda p: _along_coord(p, heading))
        n = 0
        for a, b in zip(ordered, ordered[1:]):
            gap = ((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5
            if gap < GAP_M:
                continue
            n += 1
            mid = ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
            vid = row.vineyard_id if row else plants[0].vineyard_id
            out.append(
                ProjectedPoly(
                    kind="inspection",
                    coords=[mid],
                    tile=row.tile if row else plants[0].tile,
                    vineyard_id=vid,
                    row_id=rid,
                    extras={"id": f"INS-{rid}-{n:02d}", "gap_m": round(gap, 3)},
                )
            )
    return out


def _dist(a: tuple[float, float], b: tuple[float, float]) -> float:
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def waste_targets(items: list[ProjectedPoly]) -> list[tuple[float, float]]:
    return [centroid(p.coords) for p in items if p.kind == "waste" and p.coords]


def parse_targets(raw: str) -> set[str]:
    parts = {p.strip().lower() for p in (raw or "").split(",") if p.strip()}
    allowed = {"inspections", "waste"}
    unknown = parts - allowed
    if unknown:
        raise ValueError(f"unknown route targets {sorted(unknown)}; use inspections,waste")
    return parts or {"inspections", "waste"}


def select_waypoints(items: list[ProjectedPoly], targets: set[str]) -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = []
    if "inspections" in targets:
        existing = [centroid(p.coords) for p in items if p.kind == "inspection" and p.coords]
        if existing:
            pts.extend(existing)
        else:
            pts.extend(centroid(p.coords) for p in inspections_from_canopies(items) if p.coords)
    if "waste" in targets:
        pts.extend(waste_targets(items))
    return pts
