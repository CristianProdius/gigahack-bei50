"""Marcaj / CVAT export → planar EPSG:32635. Do not re-derive plants or rows."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

from .crs import from_work_xy, transformer
from .cvat11 import CvatImage, CvatShape
from .cvat_parse import parse_cvat11, parse_cvat_zip
from .georef import pixels_to_xy_once
from .ids import ProjectedPoly

_LABELS = {"vineyard", "row", "interrow_area", "waste"}


def _attr_map(raw) -> dict[str, str]:
    if not raw:
        return {}
    if isinstance(raw, dict):
        return {str(k): "" if v is None else str(v).strip() for k, v in raw.items()}
    out: dict[str, str] = {}
    for item in raw:
        if not isinstance(item, dict):
            continue
        name = item.get("name") or item.get("spec_id")
        if not name:
            continue
        out[str(name)] = str(item.get("value") or item.get("text") or "").strip()
    return out


def _pairs(points) -> list[tuple[float, float]]:
    if not points:
        return []
    if isinstance(points[0], (list, tuple)):
        return [(float(p[0]), float(p[1])) for p in points]
    if len(points) % 2:
        raise ValueError("flat point list must have even length")
    return [(float(points[i]), float(points[i + 1])) for i in range(0, len(points), 2)]


def _shape_from_json(raw: dict) -> CvatShape | None:
    label = str(raw.get("label") or raw.get("label_name") or "")
    if label not in _LABELS:
        return None
    tag = str(raw.get("type") or raw.get("shape_type") or "polygon").lower()
    if tag in {"rectangle", "box", "rect"}:
        tag = "box"
    attrs = _attr_map(raw.get("attributes"))
    if tag == "box":
        if raw.get("xtl") is not None:
            return CvatShape(
                tag="box",
                label=label,
                xtl=float(raw["xtl"]),
                ytl=float(raw["ytl"]),
                xbr=float(raw["xbr"]),
                ybr=float(raw["ybr"]),
                attributes=attrs,
            )
        pts = _pairs(raw.get("points") or [])
        if len(pts) >= 2:
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            return CvatShape(
                tag="box",
                label=label,
                xtl=min(xs),
                ytl=min(ys),
                xbr=max(xs),
                ybr=max(ys),
                attributes=attrs,
            )
        return None
    return CvatShape(tag=tag, label=label, points=_pairs(raw.get("points") or []), attributes=attrs)


def _images_from_json(data) -> list[CvatImage]:
    if isinstance(data, dict) and "images" in data:
        rows = data["images"]
    elif isinstance(data, dict) and all(isinstance(v, dict) for v in data.values()):
        rows = [{"name": k, **v} for k, v in data.items() if k != "info"]
    elif isinstance(data, list):
        rows = data
    else:
        raise ValueError("unsupported Marcaj JSON")
    images: list[CvatImage] = []
    for row in rows:
        name = str(row.get("name") or row.get("file_name") or "")
        if not name:
            continue
        shapes = []
        for raw in row.get("shapes") or row.get("elements") or []:
            shape = _shape_from_json(raw)
            if shape is not None:
                shapes.append(shape)
        images.append(
            CvatImage(
                name=name,
                width=int(row.get("width") or 0),
                height=int(row.get("height") or 0),
                shapes=shapes,
            )
        )
    return images


def _merge_images(groups: list[list[CvatImage]]) -> list[CvatImage]:
    by_name: dict[str, CvatImage] = {}
    for images in groups:
        for im in images:
            existing = by_name.get(im.name)
            if existing is None:
                by_name[im.name] = CvatImage(
                    name=im.name,
                    width=im.width,
                    height=im.height,
                    shapes=list(im.shapes),
                )
            else:
                existing.shapes.extend(im.shapes)
                if im.width:
                    existing.width = im.width
                if im.height:
                    existing.height = im.height
    return [by_name[k] for k in sorted(by_name)]


def collect_cvat_images(path: Path) -> list[CvatImage]:
    path = Path(path)
    if path.is_dir():
        files = sorted(path.rglob("*"))
        groups = [collect_cvat_images(p) for p in files if p.suffix.lower() in {".zip", ".xml", ".json"}]
        return _merge_images(groups)
    suffix = path.suffix.lower()
    if suffix == ".zip":
        return parse_cvat_zip(path)
    if suffix == ".xml":
        return parse_cvat11(path.read_text(encoding="utf-8"))
    if suffix == ".json":
        return _images_from_json(json.loads(path.read_text(encoding="utf-8")))
    raise ValueError(f"unsupported Marcaj export: {path}")


def _box_ring(shape: CvatShape) -> list[tuple[float, float]]:
    xtl, ytl, xbr, ybr = float(shape.xtl), float(shape.ytl), float(shape.xbr), float(shape.ybr)
    return [(xtl, ytl), (xbr, ytl), (xbr, ybr), (xtl, ybr), (xtl, ytl)]


def projected_from_cvat(images: list[CvatImage], tiles_dir: Path) -> list[ProjectedPoly]:
    tiles_dir = Path(tiles_dir)
    out: list[ProjectedPoly] = []
    for im in images:
        if not im.shapes:
            continue
        tile = tiles_dir / im.name
        if not tile.is_file():
            raise FileNotFoundError(f"missing GeoTIFF for {im.name} under {tiles_dir}")
        for shape in im.shapes:
            if shape.label not in _LABELS:
                continue
            px = _box_ring(shape) if shape.tag == "box" else list(shape.points)
            if len(px) < 2:
                continue
            xy = pixels_to_xy_once(tile, px)
            attrs = shape.attributes or {}
            out.append(
                ProjectedPoly(
                    kind=shape.label,
                    coords=xy,
                    tile=im.name,
                    vineyard_id=attrs.get("vineyard_id") or None,
                    row_id=attrs.get("row_id") or None,
                    row_structure=attrs.get("row_structure") or None,
                    interrow_cover=attrs.get("interrow_cover") or None,
                )
            )
    return out


def _geometry_for(item: ProjectedPoly) -> dict:
    coords = item.coords
    if item.kind == "row":
        return {"type": "LineString", "coordinates": coords}
    if item.kind == "inspection" or (item.kind not in {"vineyard", "interrow_area", "waste"} and len(coords) == 1):
        return {"type": "Point", "coordinates": list(coords[0])}
    ring = coords if coords and coords[0] == coords[-1] else list(coords) + ([coords[0]] if coords else [])
    return {"type": "Polygon", "coordinates": [ring]}


def dump_projected_geojson(items: list[ProjectedPoly], out: Path) -> None:
    features = []
    for p in items:
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "kind": p.kind,
                    "vineyard_id": p.vineyard_id,
                    "row_id": p.row_id,
                    "row_structure": p.row_structure,
                    "interrow_cover": p.interrow_cover,
                    "tile": p.tile,
                    "id": (p.extras or {}).get("id") or p.row_id or p.vineyard_id,
                    "extras": p.extras,
                    "crs": "EPSG:32635",
                },
                "geometry": _geometry_for(p),
            }
        )
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps({"type": "FeatureCollection", "features": features}, indent=2),
        encoding="utf-8",
    )


def _looks_lonlat(x: float, y: float) -> bool:
    return abs(x) <= 180.0 and abs(y) <= 90.0


def _first_xy(geom: dict) -> tuple[float, float] | None:
    coords = geom.get("coordinates")
    while isinstance(coords, (list, tuple)) and coords and isinstance(coords[0], (list, tuple)):
        coords = coords[0]
    if isinstance(coords, (list, tuple)) and len(coords) >= 2 and isinstance(coords[0], (int, float)):
        return float(coords[0]), float(coords[1])
    return None


def _map_coords(coords, fn):
    if isinstance(coords, (list, tuple)) and coords and isinstance(coords[0], (int, float)):
        lon, lat = fn(float(coords[0]), float(coords[1]))
        return [lon, lat]
    return [_map_coords(c, fn) for c in coords]


def _normalize_props(props: dict) -> dict:
    out = dict(props or {})
    kind = out.get("kind") or out.get("type") or out.get("label")
    if kind:
        out["kind"] = kind
    return out


def to_wgs84_collection(fc: dict) -> dict:
    feats = []
    sample_xy = None
    for feat in fc.get("features") or []:
        geom = feat.get("geometry") or {}
        sample_xy = sample_xy or _first_xy(geom)
        break
    already = bool(sample_xy and _looks_lonlat(*sample_xy))
    tr = None if already else transformer("EPSG:32635", "EPSG:4326")

    def conv(x: float, y: float) -> tuple[float, float]:
        if already:
            return x, y
        lon, lat = tr.transform(x, y)
        return float(lon), float(lat)

    for feat in fc.get("features") or []:
        geom = dict(feat.get("geometry") or {})
        if geom.get("coordinates") is not None:
            geom = {**geom, "coordinates": _map_coords(geom["coordinates"], conv)}
        feats.append(
            {
                "type": "Feature",
                "properties": _normalize_props(feat.get("properties") or {}),
                "geometry": geom,
            }
        )
    return {
        "type": "FeatureCollection",
        "name": fc.get("name") or "siret3_wgs84",
        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
        "features": feats,
    }


def _simplify_fc(fc: dict, *, default_kind: str | None = None) -> dict:
    """Drop vertices in the work CRS so MapLibre is not given 400 MB of plants."""
    from shapely.geometry import mapping, shape

    tols = {
        "vineyard": 0.35,
        "interrow_area": 1.5,
        "row": 0.6,
        "forbidden": 1.0,
        "passage": 1.0,
    }
    feats = []
    for feat in fc.get("features") or []:
        props = _normalize_props(feat.get("properties") or {})
        if default_kind:
            props["kind"] = default_kind
        geom = feat.get("geometry")
        kind = props.get("kind")
        tol = tols.get(kind)
        if geom and tol:
            try:
                g = shape(geom)
                if g.is_empty:
                    continue
                g = g.simplify(tol, preserve_topology=True)
                if g.is_empty:
                    continue
                geom = mapping(g)
            except Exception:
                pass
        feats.append({"type": "Feature", "properties": props, "geometry": geom})
    return {**fc, "features": feats}


def write_web_layers(
    *,
    layers: Path | None,
    inspector: Path | None,
    farmer: Path | None,
    measurements: Path | None,
    forbidden: Path | None,
    passages: Path | None,
    inspections: Path | None,
    out_dir: Path,
) -> list[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    def _load(path: Path) -> dict:
        return json.loads(Path(path).read_text(encoding="utf-8"))

    def _dump(path: Path, obj: dict) -> None:
        path.write_text(json.dumps(obj, separators=(",", ":")), encoding="utf-8")

    merged: list[dict] = []
    for path, default_kind in (
        (layers, None),
        (forbidden, "forbidden"),
        (passages, "passage"),
        (inspections, "inspection"),
    ):
        if not path:
            continue
        fc = to_wgs84_collection(_simplify_fc(_load(path), default_kind=default_kind))
        merged.extend(fc["features"])
    layers_path = out_dir / "layers.geojson"
    _dump(layers_path, {"type": "FeatureCollection", "name": "siret3_layers", "features": merged})
    written.append(layers_path)

    if inspector:
        dest = out_dir / "route.geojson"
        _dump(dest, to_wgs84_collection(_load(inspector)))
        written.append(dest)
    if farmer:
        dest = out_dir / "route-farmer.geojson"
        _dump(dest, to_wgs84_collection(_load(farmer)))
        written.append(dest)
    if measurements:
        dest = out_dir / "measurements.csv"
        dest.write_bytes(Path(measurements).read_bytes())
        written.append(dest)
    return written


# keep pyproj import used when callers want a single point
def point_to_wgs84(east: float, north: float) -> tuple[float, float]:
    return from_work_xy(east, north)
