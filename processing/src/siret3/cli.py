"""siret3 CLI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import EXPECTED_TILE_COUNT, START_TOLERANCE_M, WORK_CRS
from .cvat11 import CvatImage, CvatShape, build_team_upload_zip, render_annotations
from .ids import ProjectedPoly, assign_row_ids, stitch_vineyards
from .measurements import write_csv
from .route import closed_walk, write_route_geojson
from .tiles import inventory, write_index


def _cmd_inventory(args: argparse.Namespace) -> int:
    recs = inventory(Path(args.tiles), expect=None if args.allow_partial else EXPECTED_TILE_COUNT)
    write_index(recs, Path(args.out))
    print(f"wrote {len(recs)} rows to {args.out}")
    return 0


def _load_projected(path: Path) -> list[ProjectedPoly]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    items = []
    for feat in data.get("features", data if isinstance(data, list) else []):
        props = feat.get("properties", feat)
        geom = feat.get("geometry", {})
        coords = geom.get("coordinates") or props.get("coords") or []
        if geom.get("type") == "Polygon":
            flat = [(float(x), float(y)) for x, y in coords[0]]
        elif geom.get("type") == "LineString":
            flat = [(float(x), float(y)) for x, y in coords]
        elif geom.get("type") == "Point":
            flat = [(float(coords[0]), float(coords[1]))]
        else:
            flat = [(float(a), float(b)) for a, b in coords]
        items.append(
            ProjectedPoly(
                kind=props.get("kind") or props.get("label") or "vineyard",
                coords=flat,
                tile=props.get("tile", ""),
                vineyard_id=props.get("vineyard_id"),
                row_id=props.get("row_id"),
            )
        )
    return items


def _cmd_stitch(args: argparse.Namespace) -> int:
    items = _load_projected(Path(args.predictions))
    items = stitch_vineyards(items)
    items = assign_row_ids(items)
    out = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "kind": p.kind,
                    "vineyard_id": p.vineyard_id,
                    "row_id": p.row_id,
                    "tile": p.tile,
                    "extras": p.extras,
                },
                "geometry": {
                    "type": "LineString" if p.kind == "row" else "Polygon",
                    "coordinates": p.coords if p.kind == "row" else [p.coords],
                },
            }
            for p in items
        ],
    }
    Path(args.out).write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"stitched {len(items)} features -> {args.out}")
    return 0


def _cmd_cvat(args: argparse.Namespace) -> int:
    # Minimal dry-run: one empty image per tile so the zip is complete.
    from .tiles import list_tile_paths, parse_tile_name

    tiles = list_tile_paths(Path(args.tiles))
    images = []
    for path in tiles:
        parse_tile_name(path.name)
        width = height = 1024
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
    build_team_upload_zip(images, Path(args.tiles), Path(args.out))
    print(f"wrote {args.out} with {len(images)} tiles")
    return 0


def _cmd_measurements(args: argparse.Namespace) -> int:
    items = _load_projected(Path(args.geojson))
    write_csv(items, Path(args.out))
    print(f"wrote {args.out} ({WORK_CRS}, planar, no terrain correction)")
    return 0


def _cmd_route(args: argparse.Namespace) -> int:
    from .crs import to_work_xy

    lon_s, lat_s = [float(x) for x in args.start.split(",")]
    if args.start_crs.upper() in {"EPSG:4326", "4326"}:
        start = to_work_xy(lon_s, lat_s)
    else:
        start = (lon_s, lat_s)
    items = _load_projected(Path(args.geojson))
    inter = [p.coords for p in items if p.kind == "interrow_area"]
    passages = [p.coords for p in items if p.kind == "passage"]
    forbidden = [p.coords for p in items if p.kind == "forbidden"]
    waypoints = [__import__("siret3.ids", fromlist=["centroid"]).centroid(p.coords) for p in items if p.kind in {"vineyard", "waste", "interrow_area"}]
    if not waypoints:
        raise SystemExit("No waypoints in GeoJSON (need vineyard / waste / interrow_area)")
    tour = closed_walk(
        waypoints,
        start,
        interrows=inter,
        passages=passages,
        forbidden=forbidden,
        tolerance_m=args.tolerance,
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

    st = sub.add_parser("stitch", help="Merge cross-tile IDs")
    st.add_argument("predictions")
    st.add_argument("--out", default="data/stitched.geojson")
    st.set_defaults(func=_cmd_stitch)

    cv = sub.add_parser("cvat-export", help="Build team_upload.zip (CVAT 1.1)")
    cv.add_argument("tiles")
    cv.add_argument("--out", default="team_upload.zip")
    cv.add_argument("--xml-only", action="store_true")
    cv.set_defaults(func=_cmd_cvat)

    ms = sub.add_parser("measurements", help="Planar EPSG:32635 measurements")
    ms.add_argument("geojson")
    ms.add_argument("--out", default="measurements.csv")
    ms.set_defaults(func=_cmd_measurements)

    rt = sub.add_parser("route", help="Closed walk, 5 m start snap")
    rt.add_argument("geojson")
    rt.add_argument("--start", required=True, help="lon,lat or x,y")
    rt.add_argument("--start-crs", default="EPSG:4326")
    rt.add_argument("--tolerance", type=float, default=START_TOLERANCE_M)
    rt.add_argument("--out", default="route.geojson")
    rt.set_defaults(func=_cmd_route)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
