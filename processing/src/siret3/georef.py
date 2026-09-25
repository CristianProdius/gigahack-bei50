"""Pixel ↔ EPSG:32635 using each tile's GeoTIFF affine."""

from __future__ import annotations

from pathlib import Path


def pixel_to_xy(tile: Path, col: float, row: float) -> tuple[float, float]:
    import rasterio

    with rasterio.open(tile) as src:
        x, y = src.transform @ (col, row)
    return float(x), float(y)


def xy_to_pixel(tile: Path, x: float, y: float) -> tuple[float, float]:
    import rasterio

    with rasterio.open(tile) as src:
        col, row = ~src.transform @ (x, y)
    return float(col), float(row)


def pixels_to_xy(tile: Path, points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    return [pixel_to_xy(tile, c, r) for c, r in points]


def xy_to_pixels(tile: Path, points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    return [xy_to_pixel(tile, x, y) for x, y in points]
