"""Parse CVAT for images 1.1 XML / ZIPs into CvatImage objects."""

from __future__ import annotations

import zipfile
from pathlib import Path

from lxml import etree

from .cvat11 import CvatImage, CvatShape

_KNOWN_ATTRS = {
    "vineyard_id",
    "row_id",
    "row_structure",
    "interrow_cover",
}


def _parse_points(raw: str) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for pair in raw.split(";"):
        pair = pair.strip()
        if not pair:
            continue
        x_s, y_s = pair.split(",", 1)
        points.append((float(x_s), float(y_s)))
    return points


def _attrs(el) -> dict[str, str]:
    out: dict[str, str] = {}
    for child in el:
        if child.tag != "attribute":
            continue
        name = child.get("name")
        if name not in _KNOWN_ATTRS:
            continue
        out[name] = (child.text or "").strip()
    return out


def _parse_shape(el) -> CvatShape:
    tag = el.tag
    label = el.get("label") or ""
    attrs = _attrs(el)
    if tag == "box":
        return CvatShape(
            tag="box",
            label=label,
            xtl=float(el.get("xtl")),
            ytl=float(el.get("ytl")),
            xbr=float(el.get("xbr")),
            ybr=float(el.get("ybr")),
            attributes=attrs,
        )
    return CvatShape(
        tag=tag,
        label=label,
        points=_parse_points(el.get("points") or ""),
        attributes=attrs,
    )


def parse_cvat11(xml: str) -> list[CvatImage]:
    root = etree.fromstring(xml.encode("utf-8") if isinstance(xml, str) else xml)
    images: list[CvatImage] = []
    for el in root.iter("image"):
        shapes = [
            _parse_shape(child)
            for child in el
            if child.tag in {"polygon", "polyline", "box"}
        ]
        images.append(
            CvatImage(
                name=el.get("name") or "",
                width=int(el.get("width") or 0),
                height=int(el.get("height") or 0),
                shapes=shapes,
            )
        )
    return images


def parse_cvat_zip(path: Path) -> list[CvatImage]:
    with zipfile.ZipFile(path) as zf:
        xml = zf.read("annotations.xml").decode("utf-8")
    return parse_cvat11(xml)


def _round_pts(points: list[tuple[float, float]], ndigits: int = 1) -> list[tuple[float, float]]:
    return [(round(x, ndigits), round(y, ndigits)) for x, y in points]


def _shape_key(shape: CvatShape) -> tuple:
    box = None
    if shape.tag == "box":
        box = (
            None if shape.xtl is None else round(shape.xtl, 1),
            None if shape.ytl is None else round(shape.ytl, 1),
            None if shape.xbr is None else round(shape.xbr, 1),
            None if shape.ybr is None else round(shape.ybr, 1),
        )
    return (
        shape.tag,
        shape.label,
        tuple(_round_pts(shape.points)),
        box,
        tuple(sorted(shape.attributes.items())),
    )


def shapes_semantically_equal(a: list[CvatImage], b: list[CvatImage]) -> bool:
    by_a = {im.name: im for im in a}
    by_b = {im.name: im for im in b}
    if set(by_a) != set(by_b):
        return False
    for name, im_a in by_a.items():
        im_b = by_b[name]
        if (im_a.width, im_a.height) != (im_b.width, im_b.height):
            return False
        keys_a = sorted(_shape_key(s) for s in im_a.shapes)
        keys_b = sorted(_shape_key(s) for s in im_b.shapes)
        if keys_a != keys_b:
            return False
    return True
