#!/usr/bin/env python3
"""Tiled YOLO infer over siret3_rXXX_cYYY.tif. Writes per-tile GeoJSON in pixel space."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--weights", required=True)
    p.add_argument("--tiles", required=True)
    p.add_argument("--out", default="data/predictions")
    p.add_argument("--imgsz", type=int, default=1280)
    p.add_argument("--conf", type=float, default=0.25)
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
        results = model.predict(source=str(tile), imgsz=args.imgsz, conf=args.conf, verbose=False)
        features = []
        for result in results:
            names = result.names
            if result.masks is not None:
                for i, poly in enumerate(result.masks.xy):
                    cls = int(result.boxes.cls[i].item())
                    features.append(
                        {
                            "type": "Feature",
                            "properties": {
                                "kind": "vineyard" if names[cls] == "vineyard" else "row",
                                "label": names[cls],
                                "tile": tile.name,
                                "score": float(result.boxes.conf[i].item()),
                            },
                            "geometry": {
                                "type": "Polygon" if names[cls] == "vineyard" else "LineString",
                                "coordinates": poly.tolist()
                                if names[cls] != "vineyard"
                                else [poly.tolist()],
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
