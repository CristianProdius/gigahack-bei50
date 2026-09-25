"""Project infer pixel GeoJSON to EPSG:32635 (one affine per tile)."""

from __future__ import annotations

import json
from pathlib import Path

from .georef import pixels_to_xy_once

WORK_CRS = "EPSG:32635"


def collect_geojson_paths(inputs: list[Path]) -> list[Path]:
    paths: list[Path] = []
    for raw in inputs:
        p = Path(raw)
        if p.is_dir():
            paths.extend(sorted(p.glob("*.geojson")))
        elif p.is_file():
            paths.append(p)
        else:
            raise FileNotFoundError(p)
    return paths


def _project_coords(coords, tile: Path):
    if not coords:
        return coords
    if isinstance(coords[0], (int, float)):
        pts = pixels_to_xy_once(tile, [(float(coords[0]), float(coords[1]))])
        return list(pts[0])
    if coords and isinstance(coords[0][0], (int, float)):
        return [list(p) for p in pixels_to_xy_once(tile, [(float(a), float(b)) for a, b in coords])]
    return [_project_coords(part, tile) for part in coords]


def project_inputs(inputs: list[Path], tiles_dir: Path) -> dict:
    tiles_dir = Path(tiles_dir)
    features = []
    cache: dict[str, Path] = {}
    for path in collect_geojson_paths(inputs):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        for feat in data.get("features") or []:
            props = dict(feat.get("properties") or {})
            tile_name = props.get("tile") or f"{path.stem}.tif"
            tile = cache.get(tile_name)
            if tile is None:
                tile = tiles_dir / tile_name
                cache[tile_name] = tile
            if not tile.is_file():
                raise FileNotFoundError(f"missing tile {tile} for {path}")
            geom = dict(feat.get("geometry") or {})
            if geom.get("coordinates") is not None:
                geom = {**geom, "coordinates": _project_coords(geom["coordinates"], tile)}
            features.append({"type": "Feature", "properties": props, "geometry": geom})
    return {
        "type": "FeatureCollection",
        "name": "siret3_predictions_32635",
        "crs": {"type": "name", "properties": {"name": WORK_CRS}},
        "features": features,
    }


def write_projected(inputs: list[Path], tiles_dir: Path, out: Path) -> dict:
    fc = project_inputs(inputs, tiles_dir)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(fc, indent=2), encoding="utf-8")
    return fc
