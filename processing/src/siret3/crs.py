"""CRS helpers. Scoring geometry is always planar EPSG:32635."""

from __future__ import annotations

from typing import Any

from . import WORK_CRS

try:
    from pyproj import Transformer
except ImportError:  # pragma: no cover - optional until deps installed
    Transformer = None  # type: ignore


def transformer(from_crs: str, to_crs: str = WORK_CRS) -> Any:
    if Transformer is None:
        raise RuntimeError("pyproj is required for reprojection")
    return Transformer.from_crs(from_crs, to_crs, always_xy=True)


def to_work_xy(x: float, y: float, from_crs: str = "EPSG:4326") -> tuple[float, float]:
    """Project a single point to EPSG:32635. Input is lon,lat if from_crs is 4326."""
    tr = transformer(from_crs, WORK_CRS)
    east, north = tr.transform(x, y)
    return float(east), float(north)


def from_work_xy(east: float, north: float, to_crs: str = "EPSG:4326") -> tuple[float, float]:
    tr = transformer(WORK_CRS, to_crs)
    x, y = tr.transform(east, north)
    return float(x), float(y)
