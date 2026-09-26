"""Copy-paste Sireț3 example plants onto other tile backgrounds for YOLO-seg."""

from __future__ import annotations

import math
import random

import numpy as np


def crop_plant(
    rgb: np.ndarray,
    poly: list[tuple[float, float]],
    pad: int = 2,
) -> tuple[np.ndarray, list[tuple[float, float]]]:
    h, w = rgb.shape[:2]
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    x0 = max(int(math.floor(min(xs))) - pad, 0)
    y0 = max(int(math.floor(min(ys))) - pad, 0)
    x1 = min(int(math.ceil(max(xs))) + pad, w)
    y1 = min(int(math.ceil(max(ys))) + pad, h)
    if x1 <= x0 or y1 <= y0:
        cut = np.zeros((1, 1, 4), dtype=np.uint8)
        return cut, [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    patch = rgb[y0:y1, x0:x1].copy()
    yy, xx = np.mgrid[0 : patch.shape[0], 0 : patch.shape[1]]
    mask = _point_in_poly(xx + x0 + 0.5, yy + y0 + 0.5, poly)
    rgba = np.zeros((patch.shape[0], patch.shape[1], 4), dtype=np.uint8)
    rgba[..., :3] = patch
    rgba[..., 3] = np.where(mask, 255, 0).astype(np.uint8)
    local = [(float(x - x0), float(y - y0)) for x, y in poly]
    return rgba, local


def _point_in_poly(xs: np.ndarray, ys: np.ndarray, poly: list[tuple[float, float]]) -> np.ndarray:
    inside = np.zeros(xs.shape, dtype=bool)
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        cond = ((yi > ys) != (yj > ys)) & (
            xs < (xj - xi) * (ys - yi) / ((yj - yi) + 1e-9) + xi
        )
        inside ^= cond
        j = i
    return inside


def paste_plants_on_background(
    background: np.ndarray,
    plants: list[tuple[np.ndarray, list[tuple[float, float]]]],
    *,
    n_plants: int,
    rng_seed: int = 0,
) -> tuple[np.ndarray, list[list[tuple[float, float]]]]:
    rng = random.Random(rng_seed)
    out = np.ascontiguousarray(background.copy())
    if out.ndim != 3 or out.shape[2] < 3:
        raise ValueError("background must be HxWx3")
    h, w = out.shape[:2]
    if n_plants <= 0 or not plants:
        return out, []
    polys: list[list[tuple[float, float]]] = []
    for i in range(n_plants):
        cut, local = plants[rng.randrange(len(plants))]
        if cut.shape[0] < 2 or cut.shape[1] < 2:
            continue
        scale = rng.uniform(0.7, 1.4)
        nh = max(2, int(cut.shape[0] * scale))
        nw = max(2, int(cut.shape[1] * scale))
        if nh >= h or nw >= w:
            continue
        cut_s = _resize_rgba(cut, nw, nh)
        x0 = rng.randint(0, w - nw)
        y0 = rng.randint(0, h - nh)
        alpha = (cut_s[..., 3:4].astype(np.float32) / 255.0)
        region = out[y0 : y0 + nh, x0 : x0 + nw].astype(np.float32)
        blended = cut_s[..., :3].astype(np.float32) * alpha + region * (1.0 - alpha)
        out[y0 : y0 + nh, x0 : x0 + nw] = blended.astype(np.uint8)
        sx = nw / cut.shape[1]
        sy = nh / cut.shape[0]
        poly = [(x0 + px * sx, y0 + py * sy) for px, py in local]
        if len(poly) >= 3:
            polys.append(poly)
    return out, polys


def _resize_rgba(cut: np.ndarray, nw: int, nh: int) -> np.ndarray:
    try:
        from PIL import Image

        im = Image.fromarray(cut, mode="RGBA").resize((nw, nh), Image.Resampling.BILINEAR)
        return np.asarray(im)
    except Exception:
        ys = (np.linspace(0, cut.shape[0] - 1, nh)).astype(int)
        xs = (np.linspace(0, cut.shape[1] - 1, nw)).astype(int)
        return cut[ys][:, xs]
