#!/usr/bin/env python3
"""Tiled YOLO infer over siret3_rXXX_cYYY.tif. Writes per-tile GeoJSON in pixel space."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path


def _read_rgb(tile: Path):
    import numpy as np
    from PIL import Image

    return np.asarray(Image.open(tile).convert("RGB"))


def _nms_indices(boxes: list[tuple[float, float, float, float, float]], iou_thr: float = 0.45) -> list[int]:
    import numpy as np

    if not boxes:
        return []
    b = np.asarray(boxes, dtype=float)
    x1, y1, x2, y2, s = b.T
    areas = (x2 - x1) * (y2 - y1)
    order = s.argsort()[::-1]
    keep: list[int] = []
    while order.size:
        i = int(order[0])
        keep.append(i)
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])
        inter = np.maximum(0.0, xx2 - xx1) * np.maximum(0.0, yy2 - yy1)
        iou = inter / (areas[i] + areas[order[1:]] - inter + 1e-6)
        order = order[1:][iou <= iou_thr]
    return keep


def infer_tile_chips(model, tile: Path, *, chip: int, stride: int, conf: float, imgsz: int, max_det: int) -> list[dict]:
    from PIL import Image

    rgb = _read_rgb(tile)
    height, width = rgb.shape[:2]
    xs = list(range(0, max(width - chip, 0) + 1, stride))
    ys = list(range(0, max(height - chip, 0) + 1, stride))
    if not xs or xs[-1] + chip < width:
        xs.append(max(width - chip, 0))
    if not ys or ys[-1] + chip < height:
        ys.append(max(height - chip, 0))
    boxes: list[tuple[float, float, float, float, float]] = []
    rings: list[list[list[float]]] = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        for y0 in ys:
            for x0 in xs:
                w = min(chip, width - x0)
                h = min(chip, height - y0)
                crop = rgb[y0 : y0 + h, x0 : x0 + w]
                jpg = tmp_path / f"{x0}_{y0}.jpg"
                Image.fromarray(crop).save(jpg, quality=95)
                result = model.predict(
                    source=str(jpg),
                    imgsz=imgsz,
                    conf=conf,
                    max_det=max_det,
                    verbose=False,
                )[0]
                names = result.names
                if result.masks is None or result.boxes is None:
                    continue
                for i, poly in enumerate(result.masks.xy):
                    name = names[int(result.boxes.cls[i].item())]
                    if name in {"pole", "trunk", "vine_row"}:
                        continue
                    x1, y1, x2, y2 = [float(v) for v in result.boxes.xyxy[i].tolist()]
                    score = float(result.boxes.conf[i].item())
                    boxes.append((x1 + x0, y1 + y0, x2 + x0, y2 + y0, score))
                    ring = [[float(px) + x0, float(py) + y0] for px, py in poly.tolist()]
                    if ring and ring[0] != ring[-1]:
                        ring.append(list(ring[0]))
                    rings.append(ring)
    keep = _nms_indices(boxes)
    features = []
    for i in keep:
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "kind": "vineyard",
                    "label": "vineyard",
                    "tile": tile.name,
                    "score": boxes[i][4],
                },
                "geometry": {"type": "Polygon", "coordinates": [rings[i]]},
            }
        )
    return features


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--weights", required=True)
    p.add_argument("--tiles", required=True)
    p.add_argument("--out", default="data/predictions")
    p.add_argument("--imgsz", type=int, default=1280)
    p.add_argument("--conf", type=float, default=0.25)
    p.add_argument("--chip", type=int, default=0, help="if >0, JPEG-chip infer (match Sireț3 fine-tune)")
    p.add_argument("--stride", type=int, default=320)
    p.add_argument("--max-det", type=int, default=300)
    args = p.parse_args()

    tiles = sorted(Path(args.tiles).glob("siret3_r*_c*.tif"))
    if not tiles:
        raise SystemExit(f"no tiles in {args.tiles}")
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        from ultralytics import YOLO
    except ImportError:
        print("ultralytics missing. writing empty stubs so the GIS path can be tested.")
        for tile in tiles:
            (out_dir / f"{tile.stem}.geojson").write_text(
                json.dumps({"type": "FeatureCollection", "features": [], "tile": tile.name}),
                encoding="utf-8",
            )
        return 2

    model = YOLO(args.weights)
    for tile in tiles:
        if args.chip:
            features = infer_tile_chips(
                model,
                tile,
                chip=args.chip,
                stride=args.stride,
                conf=args.conf,
                imgsz=args.imgsz or args.chip,
                max_det=args.max_det,
            )
            (out_dir / f"{tile.stem}.geojson").write_text(
                json.dumps({"type": "FeatureCollection", "features": features}, indent=2),
                encoding="utf-8",
            )
            print(tile.name, len(features))
            continue
        results = model.predict(
            source=str(tile),
            imgsz=args.imgsz,
            conf=args.conf,
            max_det=args.max_det,
            verbose=False,
        )
        features = []
        for result in results:
            names = result.names
            if result.masks is not None:
                for i, poly in enumerate(result.masks.xy):
                    cls = int(result.boxes.cls[i].item())
                    name = names[cls]
                    if name in {"pole", "trunk"}:
                        continue
                    ring = poly.tolist()
                    features.append(
                        {
                            "type": "Feature",
                            "properties": {
                                "kind": "vineyard",
                                "label": name,
                                "tile": tile.name,
                                "score": float(result.boxes.conf[i].item()),
                            },
                            "geometry": {
                                "type": "Polygon",
                                "coordinates": [ring],
                            },
                        }
                    )
            elif result.boxes is not None:
                for box, cls, conf in zip(result.boxes.xyxy, result.boxes.cls, result.boxes.conf):
                    x1, y1, x2, y2 = [float(v) for v in box.tolist()]
                    features.append(
                        {
                            "type": "Feature",
                            "properties": {
                                "kind": "waste",
                                "label": names[int(cls.item())],
                                "tile": tile.name,
                                "score": float(conf.item()),
                            },
                            "geometry": {
                                "type": "Polygon",
                                "coordinates": [[
                                    [x1, y1], [x2, y1], [x2, y2], [x1, y2], [x1, y1]
                                ]],
                            },
                        }
                    )
        (out_dir / f"{tile.stem}.geojson").write_text(
            json.dumps({"type": "FeatureCollection", "features": features}, indent=2),
            encoding="utf-8",
        )
        print(tile.name, len(features))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
