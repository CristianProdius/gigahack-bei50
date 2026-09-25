"""Derive inter-row polygons from vineyard outline minus canopies / row buffers."""

from __future__ import annotations

from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

from .ids import ProjectedPoly, _as_polygon, _ring, centroid


def derive_interrows(
    items: list[ProjectedPoly],
    canopy_buffer_m: float = 0.4,
    row_buffer_m: float = 0.35,
    cover: str = "unknown",
) -> list[ProjectedPoly]:
    vines = [p for p in items if p.kind == "vineyard"]
    rows = [p for p in items if p.kind == "row"]
    extra = [p for p in items if p.kind not in {"vineyard", "row", "interrow_area"}]
    out: list[ProjectedPoly] = list(vines) + list(rows) + extra

    for vine in vines:
        block = _as_polygon(vine.coords)
        if block.is_empty:
            continue
        subtract = []
        for row in rows:
            if row.vineyard_id and vine.vineyard_id and row.vineyard_id != vine.vineyard_id:
                continue
            if len(row.coords) >= 2:
                subtract.append(LineString(row.coords).buffer(row_buffer_m, cap_style=2))
        subtract.append(block.buffer(-canopy_buffer_m) if block.area > 1 else block.buffer(0))
        leftover = block
        if subtract:
            leftover = block.difference(unary_union(subtract))
        leftover = leftover.buffer(0)
        if leftover.is_empty:
            continue
        parts = list(leftover.geoms) if leftover.geom_type == "MultiPolygon" else [leftover]
        local_rows = [r for r in rows if r.vineyard_id == vine.vineyard_id and len(r.coords) >= 2]
        for part in parts:
            if part.is_empty or part.area < 0.5:
                continue
            pieces = _voronoi_split(part, local_rows) if len(local_rows) >= 2 else [part]
            for piece in pieces:
                if piece.is_empty or piece.area < 0.5:
                    continue
                out.append(
                    ProjectedPoly(
                        kind="interrow_area",
                        coords=_ring(piece),
                        tile=vine.tile,
                        vineyard_id=vine.vineyard_id,
                        extras={"interrow_cover": cover, "n_parts": 1},
                    )
                )
    return out


def _voronoi_split(poly: Polygon, rows: list[ProjectedPoly]) -> list[Polygon]:
    try:
        from shapely.ops import voronoi_diagram
    except Exception:
        return [poly]
    seeds = [poly.intersection(LineString(r.coords)) for r in rows]
    seeds = [s for s in seeds if not s.is_empty]
    if len(seeds) < 2:
        return [poly]
    diag = voronoi_diagram(unary_union(seeds), envelope=poly.envelope)
    pieces = []
    for cell in diag.geoms:
        clip = cell.intersection(poly)
        if clip.is_empty:
            continue
        if clip.geom_type == "Polygon":
            pieces.append(clip)
        elif clip.geom_type == "MultiPolygon":
            pieces.extend(list(clip.geoms))
    return pieces or [poly]


def colour_cover_guess(mean_rgb: tuple[float, float, float]) -> str:
    r, g, b = mean_rgb
    exg = 2 * g - r - b
    if exg > 25 and g > r and g > b:
        return "grass"
    if r > 90 and g > 70 and b < 80 and r >= g:
        return "soil"
    if exg > 10:
        return "cover_crop"
    return "unknown"
