"""Planar measurements in EPSG:32635. No terrain correction."""

from __future__ import annotations

import csv
from pathlib import Path

from .ids import ProjectedPoly, centroid


def _ring_area(coords: list[tuple[float, float]]) -> float:
    if len(coords) < 3:
        return 0.0
    pts = coords
    if pts[0] != pts[-1]:
        pts = pts + [pts[0]]
    acc = 0.0
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        acc += x1 * y2 - x2 * y1
    return abs(acc) / 2.0


def _line_length(coords: list[tuple[float, float]]) -> float:
    total = 0.0
    for (x1, y1), (x2, y2) in zip(coords, coords[1:]):
        total += ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
    return total


def measure(item: ProjectedPoly) -> dict:
    area = _ring_area(item.coords) if item.kind in {"vineyard", "interrow_area", "waste"} else ""
    length = _line_length(item.coords) if item.kind == "row" else ""
    if item.kind == "waste" and len(item.coords) >= 2:
        # bbox as two corners or a ring
        if len(item.coords) == 2:
            (x0, y0), (x1, y1) = item.coords
            area = abs(x1 - x0) * abs(y1 - y0)
    n_parts = 1
    if item.extras and "n_parts" in item.extras:
        n_parts = int(item.extras["n_parts"])
    ident = item.row_id or item.vineyard_id or ""
    return {
        "kind": item.kind,
        "id": ident,
        "vineyard_id": item.vineyard_id or "",
        "area_m2": f"{area:.3f}" if area != "" else "",
        "length_m": f"{length:.3f}" if length != "" else "",
        "n_parts": n_parts,
        "tile_names": item.tile,
        "centroid_x": f"{centroid(item.coords)[0]:.3f}",
        "centroid_y": f"{centroid(item.coords)[1]:.3f}",
    }


def write_csv(items: list[ProjectedPoly], out_csv: Path) -> None:
    rows = [measure(item) for item in items]
    out_csv = Path(out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "kind",
        "id",
        "vineyard_id",
        "area_m2",
        "length_m",
        "n_parts",
        "tile_names",
        "centroid_x",
        "centroid_y",
    ]
    with out_csv.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
