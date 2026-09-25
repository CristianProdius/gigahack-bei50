from pathlib import Path

import pytest

from siret3.cvat11 import render_annotations
from siret3.cvat_parse import parse_cvat11, parse_cvat_zip, shapes_semantically_equal

REPO = Path(__file__).resolve().parents[2]
EXAMPLE_ZIP = REPO / "data/challenge/05_examples/siret3_examples_cvat.zip"


def _tiny_xml() -> str:
    return """<?xml version="1.0" encoding="utf-8"?>
<annotations>
  <version>1.1</version>
  <image id="0" name="siret3_r001_c001.tif" width="2048" height="2048">
    <polygon label="vineyard" source="manual" occluded="0" points="10.0,10.0;20.0,10.0;20.0,18.0" z_order="0">
      <attribute name="vineyard_id">V01</attribute>
    </polygon>
    <polyline label="row" occluded="0" points="1.0,2.0;9.0,2.5">
      <attribute name="vineyard_id">V01</attribute>
      <attribute name="row_id">V01-R01</attribute>
      <attribute name="row_structure">regular</attribute>
    </polyline>
    <box label="waste" xtl="100.4" ytl="110.1" xbr="140.0" ybr="150.0" occluded="0">
      <attribute name="vineyard_id">V01</attribute>
    </box>
    <polygon label="interrow_area" points="30.0,30.0;80.0,30.0;80.0,50.0;30.0,50.0">
      <attribute name="vineyard_id">V01</attribute>
      <attribute name="interrow_cover">bare_soil</attribute>
    </polygon>
  </image>
</annotations>
"""


def test_parse_tiny_xml_shapes_and_attrs():
    images = parse_cvat11(_tiny_xml())
    assert len(images) == 1
    im = images[0]
    assert im.name == "siret3_r001_c001.tif"
    assert im.width == 2048 and im.height == 2048
    by_label = {s.label: s for s in im.shapes}
    assert set(by_label) == {"vineyard", "row", "waste", "interrow_area"}
    assert by_label["vineyard"].tag == "polygon"
    assert by_label["vineyard"].points[0] == (10.0, 10.0)
    assert by_label["vineyard"].attributes["vineyard_id"] == "V01"
    assert by_label["row"].tag == "polyline"
    assert by_label["row"].attributes["row_id"] == "V01-R01"
    assert by_label["waste"].tag == "box"
    assert by_label["waste"].xtl == pytest.approx(100.4)
    assert by_label["waste"].ybr == pytest.approx(150.0)
    assert by_label["interrow_area"].attributes["interrow_cover"] == "bare_soil"


def test_roundtrip_tiny_xml_is_semantically_equal():
    original = parse_cvat11(_tiny_xml())
    rendered = parse_cvat11(render_annotations(original))
    assert shapes_semantically_equal(original, rendered)


@pytest.mark.skipif(not EXAMPLE_ZIP.is_file(), reason="official example ZIP not in repo")
def test_parse_official_example_counts():
    images = parse_cvat_zip(EXAMPLE_ZIP)
    by_name = {im.name: im for im in images}
    assert set(by_name) == {"siret3_r021_c012.tif", "siret3_r006_c004.tif"}

    v01 = by_name["siret3_r021_c012.tif"]
    assert v01.width == 2048
    assert sum(1 for s in v01.shapes if s.label == "vineyard") == 399
    assert sum(1 for s in v01.shapes if s.label == "row") == 25
    assert sum(1 for s in v01.shapes if s.label == "interrow_area") == 24
    assert sum(1 for s in v01.shapes if s.label == "waste") == 0
    assert {s.attributes["vineyard_id"] for s in v01.shapes} == {"V01"}
    assert {s.attributes["row_structure"] for s in v01.shapes if s.label == "row"} == {"regular"}
    assert {s.attributes["interrow_cover"] for s in v01.shapes if s.label == "interrow_area"} == {
        "bare_soil"
    }

    v02 = by_name["siret3_r006_c004.tif"]
    assert sum(1 for s in v02.shapes if s.label == "vineyard") == 251
    assert sum(1 for s in v02.shapes if s.label == "row") == 26
    assert sum(1 for s in v02.shapes if s.label == "interrow_area") == 25
    rows = [s for s in v02.shapes if s.label == "row"]
    assert sum(1 for s in rows if s.attributes["row_structure"] == "disrupted") == 5
    assert sum(1 for s in rows if s.attributes["row_structure"] == "regular") == 21
    covers = [s.attributes["interrow_cover"] for s in v02.shapes if s.label == "interrow_area"]
    assert covers.count("bare_soil") == 21
    assert covers.count("mixed") == 4


@pytest.mark.skipif(not EXAMPLE_ZIP.is_file(), reason="official example ZIP not in repo")
def test_official_example_roundtrip_counts():
    original = parse_cvat_zip(EXAMPLE_ZIP)
    again = parse_cvat11(render_annotations(original, task_name="roundtrip"))
    assert shapes_semantically_equal(original, again)
