"""siret3 CLI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import EXPECTED_TILE_COUNT, START_TOLERANCE_M, WORK_CRS
from .cvat11 import CvatImage, build_part_zips, build_team_upload_zip, render_annotations
from .derive import derive_from_canopies, images_from_projected
from .ids import ProjectedPoly
from .measurements import write_csv
from .route import closed_walk, write_route_geojson
from .tiles import inventory, write_index


def _cmd_inventory(args: argparse.Namespace) -> int:
    recs = inventory(Path(args.tiles), expect=None if args.allow_partial else EXPECTED_TILE_COUNT)
    write_index(recs, Path(args.out))
    print(f"wrote {len(recs)} rows to {args.out}")
    return 0


def _rings_from_geometry(geom: dict) -> list[tuple[list[tuple[float, float]], list[list[tuple[float, float]]]]]:
    """Return (exterior, holes) for each polygon, or a single ring with no holes."""
    from shapely.geometry import shape

    gtype = geom.get("type")
    if gtype in {"Polygon", "MultiPolygon"}:
        g = shape(geom)
        polys = list(g.geoms) if g.geom_type == "MultiPolygon" else [g]
        out = []
        for poly in polys:
            if poly.is_empty:
                continue
            exterior = [(float(x), float(y)) for x, y in poly.exterior.coords]
            holes = [[(float(x), float(y)) for x, y in ring.coords] for ring in poly.interiors]
            out.append((exterior, holes))
        return out
    coords = geom.get("coordinates") or []
    if gtype == "LineString":
        return [([(float(x), float(y)) for x, y in coords], [])]
    if gtype == "MultiLineString":
        return [([(float(x), float(y)) for x, y in line], []) for line in coords]
    if gtype == "Point":
        return [([(float(coords[0]), float(coords[1]))], [])]
    if coords and isinstance(coords[0], (int, float)):
        return [([(float(coords[0]), float(coords[1]))], [])]
    if coords and isinstance(coords[0][0], (int, float)):
        return [([(float(a), float(b)) for a, b in coords], [])]
    return []


def _load_projected(path: Path) -> list[ProjectedPoly]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    items = []
    for feat in data.get("features", data if isinstance(data, list) else []):
        props = feat.get("properties", feat)
        geom = feat.get("geometry", {})
        kind = props.get("kind") or props.get("type") or props.get("label") or "vineyard"
        parsed = _rings_from_geometry(geom)
        if not parsed and props.get("coords"):
            parsed = [(props["coords"], [])]
        for ring, holes in parsed:
            if not ring:
                continue
            extras = {"holes": holes} if holes else None
            items.append(
                ProjectedPoly(
                    kind=kind,
                    coords=ring,
                    tile=props.get("tile", ""),
                    vineyard_id=props.get("vineyard_id"),
                    row_id=props.get("row_id"),
                    row_structure=props.get("row_structure"),
                    interrow_cover=props.get("interrow_cover"),
                    extras=extras,
                )
            )
    return items


def _dump_geojson(items: list[ProjectedPoly], out: Path) -> None:
    features = []
    for p in items:
        if p.kind == "inspection" or (p.kind != "row" and len(p.coords) == 1):
            geom = {"type": "Point", "coordinates": list(p.coords[0])}
        elif p.kind == "row":
            geom = {"type": "LineString", "coordinates": p.coords}
        elif p.kind == "waste" and len(p.coords) >= 2:
            geom = {"type": "LineString", "coordinates": p.coords}
        else:
            ring = p.coords if p.coords and p.coords[0] == p.coords[-1] else list(p.coords) + (
                [p.coords[0]] if p.coords else []
            )
            geom = {"type": "Polygon", "coordinates": [ring]}
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
                    "id": (p.extras or {}).get("id"),
                    "extras": p.extras,
                },
                "geometry": geom,
            }
        )
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"type": "FeatureCollection", "features": features}, indent=2), encoding="utf-8")


def _cmd_stitch(args: argparse.Namespace) -> int:
    items = _load_projected(Path(args.predictions))
    passages = None
    if args.passages:
        passages = [p.coords for p in _load_projected(Path(args.passages))]
    items = derive_from_canopies(items, tiles_dir=Path(args.tiles) if args.tiles else None, passages=passages)
    _dump_geojson(items, Path(args.out))
    print(f"derived {len(items)} features -> {args.out}")
    return 0


def _cmd_cvat(args: argparse.Namespace) -> int:
    from .cvat_parse import parse_cvat_zip
    from .tiles import list_tile_paths, parse_tile_name

    tiles_dir = Path(args.tiles)
    if args.from_cvat:
        images = parse_cvat_zip(Path(args.from_cvat))
    elif args.shapes:
        images = images_from_projected(_load_projected(Path(args.shapes)), tiles_dir)
    else:
        images = []
        for path in list_tile_paths(tiles_dir):
            parse_tile_name(path.name)
            width = height = 2048
            try:
                import rasterio

                with rasterio.open(path) as src:
                    width, height = src.width, src.height
            except Exception:
                pass
            images.append(CvatImage(name=path.name, width=width, height=height, shapes=[]))
    if args.xml_only:
        Path(args.out).write_text(render_annotations(images), encoding="utf-8")
        print(f"wrote XML for {len(images)} images")
        return 0
    if args.parts:
        written = build_part_zips(
            images,
            tiles_dir,
            Path(args.parts),
            Path(args.out_dir),
            task_name=args.task_name,
        )
        print(f"wrote {len(written)} part ZIPs in {args.out_dir}")
        return 0
    build_team_upload_zip(images, tiles_dir, Path(args.out), task_name=args.task_name)
    print(f"wrote {args.out} with {len(images)} tiles")
    return 0


def _cmd_measurements(args: argparse.Namespace) -> int:
    items = _load_projected(Path(args.geojson))
    write_csv(items, Path(args.out))
    print(f"wrote {args.out} ({WORK_CRS}, planar, no terrain correction)")
    return 0


def _cmd_inspect(args: argparse.Namespace) -> int:
    from .inspect import inspections_from_canopies

    items = _load_projected(Path(args.geojson))
    found = inspections_from_canopies(items)
    _dump_geojson(found, Path(args.out))
    print(f"wrote {len(found)} inspections -> {args.out}")
    return 0


def _cmd_route(args: argparse.Namespace) -> int:
    from .crs import to_work_xy
    from .ids import centroid
    from .inspect import inspections_from_canopies, waste_targets
    from .route import load_official_start, passable_from_items

    if args.start:
        lon_s, lat_s = [float(x) for x in args.start.split(",")]
        if args.start_crs.upper() in {"EPSG:4326", "4326"}:
            start = to_work_xy(lon_s, lat_s)
        else:
            start = (lon_s, lat_s)
    else:
        start = load_official_start(Path(args.start_file) if args.start_file else None)

    items = _load_projected(Path(args.geojson))
    if args.passages:
        items.extend(_load_projected(Path(args.passages)))
    if args.forbidden:
        items.extend(_load_projected(Path(args.forbidden)))
    inter = [p.coords for p in items if p.kind == "interrow_area"]
    passages = [p.coords for p in items if p.kind == "passage"]
    forbidden = [p.coords for p in items if p.kind == "forbidden"]
    ins = inspections_from_canopies(items)
    waypoints = [centroid(p.coords) for p in ins] + waste_targets(items)
    if not waypoints:
        waypoints = [
            centroid(p.coords)
            for p in items
            if p.kind in {"waste", "interrow_area", "inspection"}
        ]
    if not waypoints:
        raise SystemExit("No route targets (need inspections, waste, or interrow_area)")
    tour = closed_walk(
        waypoints,
        start,
        interrows=inter,
        passages=passages,
        forbidden=forbidden,
        tolerance_m=args.tolerance,
        require_legal=True,
        passable=passable_from_items(items),
    )
    write_route_geojson(tour, Path(args.out), start=start)
    print(f"closed walk {len(tour)} vertices -> {args.out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="siret3", description="Sireț3 vineyard processing")
    sub = p.add_subparsers(dest="cmd", required=True)

    inv = sub.add_parser("inventory", help="List and check siret3_rXXX_cYYY.tif tiles")
    inv.add_argument("tiles")
    inv.add_argument("--out", default="data/tile_index.csv")
    inv.add_argument("--allow-partial", action="store_true")
    inv.set_defaults(func=_cmd_inventory)

    st = sub.add_parser("stitch", help="Derive rows, inter-rows, and IDs from canopy polygons")
    st.add_argument("predictions")
    st.add_argument("--out", default="data/stitched.geojson")
    st.add_argument("--tiles", default=None, help="tile directory for ExG cover")
    st.add_argument("--passages", default=None, help="GeoJSON that splits blocks (roads)")
    st.set_defaults(func=_cmd_stitch)

    cv = sub.add_parser("cvat-export", help="Build CVAT 1.1 ZIP(s) with shapes")
    cv.add_argument("tiles")
    cv.add_argument("--out", default="team_upload.zip")
    cv.add_argument("--xml-only", action="store_true")
    cv.add_argument("--shapes", default=None, help="GeoJSON features to write into annotations.xml")
    cv.add_argument("--from-cvat", default=None, help="existing CVAT ZIP to copy shapes from")
    cv.add_argument("--parts", default=None, help="directory of official part*.zip (writes 5 ZIPs)")
    cv.add_argument("--out-dir", default="data/cvat_zips")
    cv.add_argument("--task-name", default="siret3")
    cv.set_defaults(func=_cmd_cvat)

    ms = sub.add_parser("measurements", help="Planar EPSG:32635 measurements")
    ms.add_argument("geojson")
    ms.add_argument("--out", default="measurements.csv")
    ms.set_defaults(func=_cmd_measurements)

    ins = sub.add_parser("inspect", help="Gap / missing-planting targets (not Marcaj)")
    ins.add_argument("geojson")
    ins.add_argument("--out", default="inspections.geojson")
    ins.set_defaults(func=_cmd_inspect)

    rt = sub.add_parser("route", help="Closed walk in EPSG:32635, 5 m start snap")
    rt.add_argument("geojson")
    rt.add_argument("--start", default=None, help="lon,lat or x,y; default official start")
    rt.add_argument("--start-file", default=None, help="GeoJSON Point in EPSG:32635")
    rt.add_argument("--start-crs", default="EPSG:4326")
    rt.add_argument("--passages", default=None)
    rt.add_argument("--forbidden", default=None)
    rt.add_argument("--tolerance", type=float, default=START_TOLERANCE_M)
    rt.add_argument("--out", default="route.geojson")
    rt.set_defaults(func=_cmd_route)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
