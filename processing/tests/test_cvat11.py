from pathlib import Path

from siret3.cvat11 import CvatImage, CvatShape, render_annotations
from siret3.tiles import parse_tile_name


def test_parse_tile_name():
    assert parse_tile_name("siret3_r003_c021.tif") == (3, 21)


def test_parse_tile_name_rejects_rename():
    try:
        parse_tile_name("tile_003.tif")
    except ValueError as exc:
        assert "siret3_rXXX_cYYY" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_xml_has_version_and_original_names():
    images = [
        CvatImage(
            name="siret3_r001_c002.tif",
            width=512,
            height=512,
            shapes=[
                CvatShape(
                    tag="polygon",
                    label="vineyard",
                    points=[(1, 1), (10, 1), (10, 8), (1, 8)],
                    attributes={"vineyard_id": "V-0001"},
                ),
                CvatShape(
                    tag="polyline",
                    label="row",
                    points=[(2, 3), (9, 3)],
                    attributes={
                        "row_id": "R-V-0001-01",
                        "vineyard_id": "V-0001",
                        "row_structure": "regular",
                    },
                ),
                CvatShape(
                    tag="box",
                    label="waste",
                    xtl=20,
                    ytl=20,
                    xbr=40,
                    ybr=35,
                    attributes={"vineyard_id": "V-0001"},
                ),
            ],
        ),
        CvatImage(name="siret3_r001_c001.tif", width=512, height=512, shapes=[]),
    ]
    xml = render_annotations(images)
    assert "<version>1.1</version>" in xml
    # lexical order: c001 before c002, ids 0 then 1
    assert xml.index('name="siret3_r001_c001.tif"') < xml.index(
        'name="siret3_r001_c002.tif"'
    )
    assert 'id="0" name="siret3_r001_c001.tif"' in xml
    assert 'label="vineyard"' in xml
    assert 'label="row"' in xml
    assert 'xtl="20.00"' in xml
    assert "<attribute name=\"vineyard_id\">V-0001</attribute>" in xml
    assert "<attribute name=\"row_structure\">regular</attribute>" in xml
    assert "<name>waste</name>" in xml
    assert "<type>rectangle</type>" in xml
    assert "regular\ndisrupted\nunassessable" in xml
    assert "bare_soil\nvegetation\nmixed\nunassessable" in xml
    assert "trellis" not in xml
    assert "cover_crop" not in xml
    assert Path("siret3_r001_c001.tif").suffix == ".tif"
