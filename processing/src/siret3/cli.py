"""siret3 CLI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import EXPECTED_TILE_COUNT, START_TOLERANCE_M, WORK_CRS
from .cvat11 import CvatImage, build_part_zips, build_team_upload_zip, render_annotations
from .derive import derive_from_canopies, images_from_projected
from .ids import ProjectedPoly
from .project import write_projected
from .marcaj import collect_cvat_images, dump_projected_geojson, projected_from_cvat, write_web_layers
from .measurements import write_csv
from .route import closed_walk, write_route_geojson
from .tiles import inventory, write_index


def _cmd_project(args: argparse.Namespace) -> int:
    fc = write_projected(
        [Path(p) for p in args.inputs],
        Path(args.tiles),
        Path(args.out),
        min_plants=args.min_plants,
        nms_m=args.nms_m,
    )
    print(f"projected {len(fc['features'])} features -> {args.out}")
    return 0


def _cmd_inventory(args: argparse.Namespace) -> int:
    recs = inventory(Path(args.tiles), expect=None if args.allow_partial else EXPECTED_TILE_COUNT)
    write_index(recs, Path(args.out))
    print(f"wrote {len(recs)} rows to {args.out}")
    return 0


def _xy_pairs(seq) -> list[tuple[float, float]]:
    return [(float(x), float(y)) for x, y in seq]


def _rings_from_geometry(geom: dict) -> list[tuple[list[tuple[float, float]], list[list[tuple[float, float]]]]]:
    """Return (exterior, holes) for each polygon, or a single ring with no holes."""
    gtype = geom.get("type")
    coords = geom.get("coordinates") or []
    if gtype == "Polygon" and coords:
        return [(_xy_pairs(coords[0]), [_xy_pairs(r) for r in coords[1:]])]
    if gtype == "MultiPolygon":
        out = []
        for poly in coords:
            if not poly:
                continue
            out.append((_xy_pairs(poly[0]), [_xy_pairs(r) for r in poly[1:]]))
        return out
    if gtype == "LineString":
        return [(_xy_pairs(coords), [])]
    if gtype == "MultiLineString":
        return [(_xy_pairs(line), []) for line in coords]
    if gtype == "Point":
        return [([(float(coords[0]), float(coords[1]))], [])]
    if coords and isinstance(coords[0], (int, float)):
        return [([(float(coords[0]), float(coords[1]))], [])]
    if coords and isinstance(coords[0][0], (int, float)):
        return [(_xy_pairs(coords), [])]
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
            extras: dict = {}
            if holes:
                extras["holes"] = holes
            if props.get("label"):
                extras["label"] = props["label"]
            items.append(
                ProjectedPoly(
                    kind=kind,
                    coords=ring,
                    tile=props.get("tile", ""),
                    vineyard_id=props.get("vineyard_id"),
                    row_id=props.get("row_id"),
                    row_structure=props.get("row_structure"),
                    interrow_cover=props.get("interrow_cover"),
                    extras=extras or None,
                )
            )
    return items


def _dump_geojson(items: list[ProjectedPoly], out: Path) -> None:
    dump_projected_geojson(items, Path(out))


def _cmd_stitch(args: argparse.Namespace) -> int:
    items = _load_projected(Path(args.predictions))
    passages = None
    if args.passages:
        passages = []
        for p in _load_projected(Path(args.passages)):
            holes = (p.extras or {}).get("holes") or []
            passages.append((p.coords, holes) if holes else p.coords)
    items = derive_from_canopies(
        items,
        tiles_dir=Path(args.tiles) if args.tiles else None,
        passages=passages,
        join_m=args.join_m,
        row_join_m=args.row_join_m,
    )
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


def _cmd_marcaj_import(args: argparse.Namespace) -> int:
    images = collect_cvat_images(Path(args.source))
    items = projected_from_cvat(images, Path(args.tiles))
    dump_projected_geojson(items, Path(args.out))
    n = len(items)
    kinds = {}
    for p in items:
        kinds[p.kind] = kinds.get(p.kind, 0) + 1
    print(f"imported {n} Marcaj shapes {kinds} -> {args.out} (no GIS re-derive)")
    return 0


def _cmd_web_layers(args: argparse.Namespace) -> int:
    written = write_web_layers(
        layers=Path(args.layers) if args.layers else None,
        inspector=Path(args.inspector) if args.inspector else None,
        farmer=Path(args.farmer) if args.farmer else None,
        measurements=Path(args.measurements) if args.measurements else None,
        forbidden=Path(args.forbidden) if args.forbidden else None,
        passages=Path(args.passages) if args.passages else None,
        inspections=Path(args.inspections) if args.inspections else None,
        out_dir=Path(args.out_dir),
    )
    print("wrote " + ", ".join(str(p) for p in written))
    return 0


def _cmd_route(args: argparse.Namespace) -> int:
    from .crs import to_work_xy
    from .ids import centroid
    from .inspect import parse_targets, select_waypoints, waste_targets
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
    passages_path = args.passages or (
        str(Path("data/challenge/02_route/passages.geojson"))
        if Path("data/challenge/02_route/passages.geojson").is_file()
        else None
    )
    forbidden_path = args.forbidden or (
        str(Path("data/challenge/02_route/forbidden.geojson"))
        if Path("data/challenge/02_route/forbidden.geojson").is_file()
        else None
    )
    if passages_path:
        items.extend(_load_projected(Path(passages_path)))
    if forbidden_path:
        items.extend(_load_projected(Path(forbidden_path)))
    inter = [p.coords for p in items if p.kind == "interrow_area"]
    passages = [p.coords for p in items if p.kind == "passage"]
    forbidden = [p.coords for p in items if p.kind == "forbidden"]
    wanted = parse_targets(getattr(args, "targets", "inspections,waste"))
    waypoints = select_waypoints(items, wanted)
    if not waypoints:
        waypoints = [
            centroid(p.coords)
            for p in items
            if p.kind in {"waste", "interrow_area", "inspection"}
        ]
    if not waypoints:
        raise SystemExit("No route targets (need inspections, waste, or interrow_area)")
    if "inspections" in wanted and len(waypoints) > 280:
        waste = waste_targets(items)
        rest = [p for p in waypoints if p not in set(waste)]
        step = max(1, len(rest) // max(1, 280 - len(waste)))
        waypoints = waste + rest[::step]
        print(f"capped inspector waypoints to {len(waypoints)}")
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
    role = "farmer" if wanted == {"waste"} else "inspector"
    write_route_geojson(tour, Path(args.out), start=start, role=role)
    print(f"closed walk {len(tour)} vertices role={role} -> {args.out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="siret3", description="Sireț3 vineyard processing")
    sub = p.add_subparsers(dest="cmd", required=True)

    inv = sub.add_parser("inventory", help="List and check siret3_rXXX_cYYY.tif tiles")
    inv.add_argument("tiles")
    inv.add_argument("--out", default="data/tile_index.csv")
    inv.add_argument("--allow-partial", action="store_true")
    inv.set_defaults(func=_cmd_inventory)

    pj = sub.add_parser("project", help="Pixel infer GeoJSON → one EPSG:32635 FeatureCollection")
    pj.add_argument("inputs", nargs="+", help="GeoJSON files or directories")
    pj.add_argument("--tiles", default="data/tiles")
    pj.add_argument("--out", default="data/predictions_32635.geojson")
    pj.add_argument("--min-plants", type=int, default=10, help="drop vineyard polygons on tiles below this count")
    pj.add_argument("--nms-m", type=float, default=0.5, help="drop lower-score plants whose centroids are this close")
    pj.set_defaults(func=_cmd_project)

    st = sub.add_parser("stitch", help="Derive rows, inter-rows, and IDs from canopy polygons")
    st.add_argument("predictions")
    st.add_argument("--out", default="data/stitched.geojson")
    st.add_argument("--tiles", default=None, help="tile directory for ExG cover")
    st.add_argument("--passages", default=None, help="GeoJSON that splits blocks (roads)")
    st.add_argument("--join-m", type=float, default=6.0, help="max plant-to-plant gap for one vineyard_id")
    st.add_argument("--row-join-m", type=float, default=2.0, help="max along-row gap to share a row_id across tiles")
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
    rt.add_argument(
        "--targets",
        default="inspections,waste",
        help="comma list: inspections,waste (inspector) or waste (farmer)",
    )
    rt.set_defaults(func=_cmd_route)

    mi = sub.add_parser(
        "marcaj-import",
        help="CVAT/Marcaj export (ZIP/XML/JSON) → EPSG:32635 GeoJSON; keeps human rows/plants",
    )
    mi.add_argument("source", help="ZIP, annotations.xml, json_simple, or a folder of those")
    mi.add_argument("--tiles", default="data/tiles")
    mi.add_argument("--out", default="data/marcaj_32635.geojson")
    mi.set_defaults(func=_cmd_marcaj_import)

    wl = sub.add_parser("web-layers", help="Reproject 32635 layers to WGS84 for MapLibre")
    wl.add_argument("--layers", default=None, help="Marcaj 32635 FeatureCollection")
    wl.add_argument("--inspector", default=None)
    wl.add_argument("--farmer", default=None)
    wl.add_argument("--measurements", default=None)
    wl.add_argument("--forbidden", default=None)
    wl.add_argument("--passages", default=None)
    wl.add_argument("--inspections", default=None)
    wl.add_argument("--out-dir", default="web/public/layers")
    wl.set_defaults(func=_cmd_web_layers)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
