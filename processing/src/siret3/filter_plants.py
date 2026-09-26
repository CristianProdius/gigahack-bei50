"""Drop empty-tile false canopies and chip-overlap duplicates."""

from __future__ import annotations

from collections import defaultdict

from shapely.geometry import shape


def drop_sparse_tile_canopies(features: list[dict], min_plants: int = 10) -> list[dict]:
    """Clear vineyard polygons on tiles with fewer than min_plants. Keep waste."""
    if min_plants <= 0:
        return list(features)
    vines_by_tile: dict[str, list[int]] = defaultdict(list)
    for i, feat in enumerate(features):
        props = feat.get("properties") or {}
        if props.get("kind") == "vineyard":
            vines_by_tile[str(props.get("tile") or "")].append(i)
    drop = {i for idxs in vines_by_tile.values() if 0 < len(idxs) < min_plants for i in idxs}
    return [feat for i, feat in enumerate(features) if i not in drop]


def nms_canopy_centroids(features: list[dict], min_dist_m: float = 0.5) -> list[dict]:
    """Keep the highest-score canopy when centroids are closer than min_dist_m."""
    if min_dist_m <= 0:
        return list(features)
    vines = []
    others = []
    for feat in features:
        if (feat.get("properties") or {}).get("kind") == "vineyard":
            vines.append(feat)
        else:
            others.append(feat)
    vines.sort(key=lambda f: float((f.get("properties") or {}).get("score") or 0.0), reverse=True)
    kept: list[dict] = []
    pts: list[tuple[float, float]] = []
    min_d2 = min_dist_m * min_dist_m
    for feat in vines:
        geom = shape(feat["geometry"])
        if geom.is_empty:
            continue
        c = geom.centroid
        if any((c.x - x) ** 2 + (c.y - y) ** 2 < min_d2 for x, y in pts):
            continue
        kept.append(feat)
        pts.append((c.x, c.y))
    return others + kept
