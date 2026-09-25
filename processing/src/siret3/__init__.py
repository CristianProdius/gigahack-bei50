"""Siret3 vineyard processing. Measurements are planar EPSG:32635."""

WORK_CRS = "EPSG:32635"
TILE_NAME_RE = r"^siret3_r(\d{3})_c(\d{3})\.tif$"
EXPECTED_TILE_COUNT = 311
START_TOLERANCE_M = 5.0

__all__ = [
    "WORK_CRS",
    "TILE_NAME_RE",
    "EXPECTED_TILE_COUNT",
    "START_TOLERANCE_M",
]
