"""Official example / Marcaj CVAT → YOLO-seg chips (Sireț3 plants only)."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

_TILE_NAME = re.compile(r"(siret3_r\d+_c\d+\.tif)$", re.I)


def canonical_tile_name(name: str) -> str:
    base = Path(str(name).replace("\\", "/")).name
    match = _TILE_NAME.search(base)
    return match.group(1) if match else base


def plants_from_cvat_xml(xml: str | bytes) -> list[tuple[str, list[list[tuple[float, float]]]]]:
    root = ET.fromstring(xml)
    out: list[tuple[str, list[list[tuple[float, float]]]]] = []
    for el in root.iter("image"):
        name = canonical_tile_name(el.get("name") or "")
        plants: list[list[tuple[float, float]]] = []
        for poly in el.findall("polygon"):
            if (poly.get("label") or "") != "vineyard":
                continue
            pts = []
            for pair in (poly.get("points") or "").split(";"):
                pair = pair.strip()
                if not pair:
                    continue
                x_s, y_s = pair.split(",", 1)
                pts.append((float(x_s), float(y_s)))
            if len(pts) >= 3:
                plants.append(pts)
        out.append((name, plants))
    return out


def yolo_seg_line(
    cls: int,
    points: list[tuple[float, float]],
    width: int,
    height: int,
) -> str:
    coords: list[str] = [str(cls)]
    for x, y in points:
        coords.append(f"{max(0.0, min(1.0, x / width)):.6f}")
        coords.append(f"{max(0.0, min(1.0, y / height)):.6f}")
    return " ".join(coords)


def chip_windows(width: int, height: int, chip: int = 1024, stride: int = 512) -> list[tuple[int, int, int, int]]:
    xs = list(range(0, max(width - chip, 0) + 1, stride))
    ys = list(range(0, max(height - chip, 0) + 1, stride))
    if not xs or xs[-1] + chip < width:
        xs.append(max(width - chip, 0))
    if not ys or ys[-1] + chip < height:
        ys.append(max(height - chip, 0))
    out: list[tuple[int, int, int, int]] = []
    seen: set[tuple[int, int]] = set()
    for y0 in ys:
        for x0 in xs:
            key = (x0, y0)
            if key in seen:
                continue
            seen.add(key)
            out.append((x0, y0, min(chip, width - x0), min(chip, height - y0)))
    return out


def _centroid(points: list[tuple[float, float]]) -> tuple[float, float]:
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return (sum(xs) / len(xs), sum(ys) / len(ys))


def plants_in_chip(
    plants: list[list[tuple[float, float]]],
    x0: int,
    y0: int,
    w: int,
    h: int,
) -> list[list[tuple[float, float]]]:
    kept: list[list[tuple[float, float]]] = []
    for pts in plants:
        if len(pts) < 3:
            continue
        cx, cy = _centroid(pts)
        if not (x0 <= cx < x0 + w and y0 <= cy < y0 + h):
            continue
        shifted = [(px - x0, py - y0) for px, py in pts]
        kept.append(shifted)
    return kept


def write_example_yolo(
    example_zip: Path,
    tiles_dir: Path,
    out_dir: Path,
    *,
    chip: int = 640,
    stride: int = 320,
    holdout_frac: float = 0.15,
) -> dict[str, int]:
    """Write YOLO-seg chips from the official (not scored) example ZIP.

    Both example styles go into train. A small random holdout is val only.
    """
    images = dict(plants_from_cvat_zip(Path(example_zip)))
    return _dump_plant_records(
        images,
        Path(tiles_dir),
        Path(out_dir),
        chip=chip,
        stride=stride,
        holdout_frac=holdout_frac,
        yaml_name="siret3-examples.yaml",
    )


def plants_from_cvat_zip(zip_path: Path) -> list[tuple[str, list[list[tuple[float, float]]]]]:
    with zipfile.ZipFile(zip_path) as zf:
        xml = zf.read("annotations.xml")
    return plants_from_cvat_xml(xml)


def write_plant_yolo(
    zips: list[Path],
    tiles_dir: Path,
    out_dir: Path,
    *,
    chip: int = 640,
    stride: int = 320,
    holdout_frac: float = 0.15,
) -> dict[str, int]:
    merged: dict[str, list[list[tuple[float, float]]]] = {}
    for zip_path in zips:
        for name, plants in plants_from_cvat_zip(Path(zip_path)):
            merged[name] = plants
    return _dump_plant_records(
        merged,
        Path(tiles_dir),
        Path(out_dir),
        chip=chip,
        stride=stride,
        holdout_frac=holdout_frac,
        yaml_name="siret3-plants.yaml",
    )


def _dump_plant_records(
    images: dict[str, list[list[tuple[float, float]]]],
    tiles_dir: Path,
    out_dir: Path,
    *,
    chip: int,
    stride: int,
    holdout_frac: float,
    yaml_name: str,
) -> dict[str, int]:
    import random

    out = Path(out_dir)
    split_dirs = {
        "train": (out / "images" / "train", out / "labels" / "train"),
        "val": (out / "images" / "val", out / "labels" / "val"),
    }
    for img_dir, lab_dir in split_dirs.values():
        img_dir.mkdir(parents=True, exist_ok=True)
        lab_dir.mkdir(parents=True, exist_ok=True)

    records: list[tuple[str, object, list[str]]] = []
    for name, plants in images.items():
        tile = Path(tiles_dir) / name
        if not tile.is_file():
            raise FileNotFoundError(tile)
        rgb = _read_rgb(tile)
        height, width = rgb.shape[:2]
        records.append(
            (
                Path(name).stem,
                rgb,
                [yolo_seg_line(0, pts, width, height) for pts in plants],
            )
        )
        for x0, y0, w, h in chip_windows(width, height, chip=chip, stride=stride):
            kept = plants_in_chip(plants, x0, y0, w, h)
            if not kept and plants:
                continue
            records.append(
                (
                    f"{Path(name).stem}_{x0}_{y0}",
                    rgb[y0 : y0 + h, x0 : x0 + w],
                    [yolo_seg_line(0, pts, w, h) for pts in kept],
                )
            )

    rng = random.Random(0)
    rng.shuffle(records)
    n_val = max(1, int(len(records) * holdout_frac))
    val_stems = {stem for stem, _crop, _lines in records[:n_val]}

    n_chips = 0
    n_plants = 0
    for stem, crop, lines in records:
        split = "val" if stem in val_stems else "train"
        img_dir, lab_dir = split_dirs[split]
        _save_rgb(img_dir / f"{stem}.jpg", crop)
        (lab_dir / f"{stem}.txt").write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        n_chips += 1
        n_plants += len(lines)
    (out / yaml_name).write_text(
        "\n".join(
            [
                f"path: {out.resolve()}",
                "train: images/train",
                "val: images/val",
                "names:",
                "  0: vineyard",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return {"chips": n_chips, "plant_instances": n_plants, "tiles": len(images)}


def _save_rgb(path: Path, rgb) -> None:
    try:
        from PIL import Image

        Image.fromarray(rgb).save(path, quality=95)
    except ImportError:
        tif = path.with_suffix(".tif")
        import rasterio

        h, w, c = rgb.shape
        with rasterio.open(
            tif,
            "w",
            driver="GTiff",
            height=h,
            width=w,
            count=c,
            dtype=rgb.dtype,
        ) as dst:
            for i in range(c):
                dst.write(rgb[:, :, i], i + 1)


def _read_rgb(tile: Path):
    import numpy as np

    try:
        from PIL import Image

        im = Image.open(tile).convert("RGB")
        return np.asarray(im)
    except Exception:
        import rasterio

        with rasterio.open(tile) as src:
            count = min(src.count, 3)
            bands = src.read(list(range(1, count + 1)))
        rgb = np.transpose(bands, (1, 2, 0))
        if rgb.dtype != np.uint8:
            rgb = np.clip(rgb, 0, 255).astype(np.uint8)
        if rgb.shape[2] == 1:
            rgb = np.repeat(rgb, 3, axis=2)
        return rgb
