"""CVAT for images 1.1 writer and team_upload.zip builder."""

from __future__ import annotations

import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from xml.sax.saxutils import escape

from .tiles import parse_tile_name

MAX_ZIP_BYTES = 90 * 1024 * 1024
_PART_GLOB = "siret3_challenge_tiles_part*of5.zip"


@dataclass
class CvatShape:
    tag: str  # polygon | polyline | box
    label: str
    points: list[tuple[float, float]] = field(default_factory=list)
    xtl: float | None = None
    ytl: float | None = None
    xbr: float | None = None
    ybr: float | None = None
    attributes: dict[str, str] = field(default_factory=dict)


@dataclass
class CvatImage:
    name: str
    width: int
    height: int
    shapes: list[CvatShape] = field(default_factory=list)


def _points_attr(points: list[tuple[float, float]]) -> str:
    return ";".join(f"{x:.2f},{y:.2f}" for x, y in points)


def _attrs_xml(attributes: dict[str, str]) -> str:
    parts = []
    for key, value in attributes.items():
        parts.append(
            f'      <attribute name="{escape(key)}">{escape(str(value))}</attribute>\n'
        )
    return "".join(parts)


def render_annotations(images: list[CvatImage], *, task_name: str = "siret3") -> str:
    ordered = sorted(images, key=lambda im: im.name)
    labels = """      <label>
        <name>vineyard</name>
        <type>polygon</type>
        <attributes>
          <attribute>
            <name>vineyard_id</name>
            <mutable>False</mutable>
            <input_type>text</input_type>
            <default_value></default_value>
            <values></values>
          </attribute>
        </attributes>
      </label>
      <label>
        <name>row</name>
        <type>polyline</type>
        <attributes>
          <attribute>
            <name>row_id</name>
            <mutable>False</mutable>
            <input_type>text</input_type>
            <default_value></default_value>
            <values></values>
          </attribute>
          <attribute>
            <name>vineyard_id</name>
            <mutable>False</mutable>
            <input_type>text</input_type>
            <default_value></default_value>
            <values></values>
          </attribute>
          <attribute>
            <name>row_structure</name>
            <mutable>False</mutable>
            <input_type>select</input_type>
            <default_value>regular</default_value>
            <values>regular
disrupted
unassessable</values>
          </attribute>
        </attributes>
      </label>
      <label>
        <name>interrow_area</name>
        <type>polygon</type>
        <attributes>
          <attribute>
            <name>vineyard_id</name>
            <mutable>False</mutable>
            <input_type>text</input_type>
            <default_value></default_value>
            <values></values>
          </attribute>
          <attribute>
            <name>interrow_cover</name>
            <mutable>False</mutable>
            <input_type>select</input_type>
            <default_value>bare_soil</default_value>
            <values>bare_soil
vegetation
mixed
unassessable</values>
          </attribute>
        </attributes>
      </label>
      <label>
        <name>waste</name>
        <type>rectangle</type>
        <attributes>
          <attribute>
            <name>vineyard_id</name>
            <mutable>False</mutable>
            <input_type>text</input_type>
            <default_value></default_value>
            <values></values>
          </attribute>
        </attributes>
      </label>"""

    chunks = [
        '<?xml version="1.0" encoding="utf-8"?>\n',
        "<annotations>\n",
        "  <version>1.1</version>\n",
        "  <meta>\n",
        "    <task>\n",
        f"      <name>{escape(task_name)}</name>\n",
        f"      <size>{len(ordered)}</size>\n",
        "      <mode>annotation</mode>\n",
        "      <labels>\n",
        labels,
        "\n      </labels>\n",
        "    </task>\n",
        "  </meta>\n",
    ]
    for idx, image in enumerate(ordered):
        parse_tile_name(image.name)  # refuse renamed files
        chunks.append(
            f'  <image id="{idx}" name="{escape(image.name)}" '
            f'width="{image.width}" height="{image.height}">\n'
        )
        for shape in image.shapes:
            if shape.tag == "box":
                chunks.append(
                    f'    <box label="{escape(shape.label)}" '
                    f'xtl="{shape.xtl:.2f}" ytl="{shape.ytl:.2f}" '
                    f'xbr="{shape.xbr:.2f}" ybr="{shape.ybr:.2f}" occluded="0">\n'
                )
                chunks.append(_attrs_xml(shape.attributes))
                chunks.append("    </box>\n")
            else:
                chunks.append(
                    f'    <{shape.tag} label="{escape(shape.label)}" '
                    f'points="{_points_attr(shape.points)}" occluded="0">\n'
                )
                chunks.append(_attrs_xml(shape.attributes))
                chunks.append(f"    </{shape.tag}>\n")
        chunks.append("  </image>\n")
    chunks.append("</annotations>\n")
    return "".join(chunks)


def build_team_upload_zip(
    images: list[CvatImage],
    tiles_dir: Path,
    out_zip: Path,
    *,
    task_name: str = "siret3",
) -> Path:
    """Write annotations.xml + images/<original.tif> using byte copies of the TIFFs."""
    xml = render_annotations(images, task_name=task_name)
    out_zip = Path(out_zip)
    out_zip.parent.mkdir(parents=True, exist_ok=True)
    tiles_dir = Path(tiles_dir)
    with zipfile.ZipFile(out_zip, "w") as zf:
        zf.writestr("annotations.xml", xml, compress_type=zipfile.ZIP_DEFLATED)
        for image in images:
            src = tiles_dir / image.name
            if not src.is_file():
                raise FileNotFoundError(
                    f"Refusing zip: missing original tile {src}. "
                    "Import needs all 311 unchanged GeoTIFFs."
                )
            zf.write(src, arcname=f"images/{image.name}", compress_type=zipfile.ZIP_STORED)
    return out_zip


def official_part_membership(parts_dir: Path) -> dict[str, list[str]]:
    """Tile names inside each official challenge part ZIP, keyed by zip filename."""
    parts_dir = Path(parts_dir)
    zips = sorted(parts_dir.glob(_PART_GLOB))
    if not zips:
        raise FileNotFoundError(f"no {_PART_GLOB} in {parts_dir}")
    membership: dict[str, list[str]] = {}
    for zp in zips:
        with zipfile.ZipFile(zp) as zf:
            names = sorted(
                Path(n).name
                for n in zf.namelist()
                if n.lower().endswith(".tif") and not n.endswith("/")
            )
        membership[zp.name] = names
    return membership


def build_part_zips(
    images: list[CvatImage],
    tiles_dir: Path,
    parts_dir: Path,
    out_dir: Path,
    *,
    task_name: str = "siret3",
    max_bytes: int = MAX_ZIP_BYTES,
) -> list[Path]:
    """Write one CVAT ZIP per official tile part. Fail if any archive exceeds max_bytes."""
    by_name = {im.name: im for im in images}
    membership = official_part_membership(parts_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for part_name, tile_names in membership.items():
        subset = []
        for name in tile_names:
            if name in by_name:
                subset.append(by_name[name])
            else:
                subset.append(CvatImage(name=name, width=2048, height=2048, shapes=[]))
        dest = out_dir / part_name
        build_team_upload_zip(subset, tiles_dir, dest, task_name=task_name)
        size = dest.stat().st_size
        if size >= max_bytes:
            dest.unlink(missing_ok=True)
            raise ValueError(
                f"{dest} is {size} bytes (>= {max_bytes}, official 90 MB cap). "
                "Split or drop unused rasters."
            )
        written.append(dest)
    return written
