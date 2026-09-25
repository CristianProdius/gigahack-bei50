"""Inventory and name-check the 311 Sireț3 GeoTIFF tiles."""

from __future__ import annotations

import csv
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from . import EXPECTED_TILE_COUNT, TILE_NAME_RE

_NAME = re.compile(TILE_NAME_RE)


@dataclass(frozen=True)
class TileRecord:
    name: str
    row: int
    col: int
    path: str
    width_px: int | None = None
    height_px: int | None = None
    crs: str | None = None
    west: float | None = None
    south: float | None = None
    east: float | None = None
    north: float | None = None


def parse_tile_name(name: str) -> tuple[int, int]:
    m = _NAME.match(name)
    if not m:
        raise ValueError(
            f"Tile name {name!r} does not match siret3_rXXX_cYYY.tif"
        )
    return int(m.group(1)), int(m.group(2))


def list_tile_paths(tiles_dir: Path) -> list[Path]:
    paths = sorted(p for p in Path(tiles_dir).glob("siret3_r*_c*.tif") if p.is_file())
    return paths


def _read_raster_meta(path: Path) -> dict:
    try:
        import rasterio
    except ImportError:
        return {}
    with rasterio.open(path) as src:
        b = src.bounds
        crs = str(src.crs) if src.crs else None
        return {
            "width_px": src.width,
            "height_px": src.height,
            "crs": crs,
            "west": float(b.left),
            "south": float(b.bottom),
            "east": float(b.right),
            "north": float(b.top),
        }


def inventory(tiles_dir: Path, *, expect: int = EXPECTED_TILE_COUNT) -> list[TileRecord]:
    paths = list_tile_paths(tiles_dir)
    records: list[TileRecord] = []
    bad: list[str] = []
    for path in paths:
        try:
            row, col = parse_tile_name(path.name)
        except ValueError as exc:
            bad.append(str(exc))
            continue
        meta = _read_raster_meta(path)
        records.append(
            TileRecord(
                name=path.name,
                row=row,
                col=col,
                path=str(path.resolve()),
                **meta,
            )
        )
    if bad:
        raise ValueError("Bad tile names:\n" + "\n".join(bad))
    if expect and len(records) != expect:
        raise ValueError(
            f"Expected {expect} tiles named siret3_rXXX_cYYY.tif, found {len(records)} in {tiles_dir}"
        )
    return records


def write_index(records: list[TileRecord], out_csv: Path) -> None:
    out_csv = Path(out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(asdict(records[0]).keys()) if records else [
        "name",
        "row",
        "col",
        "path",
    ]
    with out_csv.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        for rec in records:
            w.writerow(asdict(rec))
