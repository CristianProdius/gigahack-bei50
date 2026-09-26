from siret3.example_yolo import (
    canonical_tile_name,
    chip_windows,
    plants_from_cvat_xml,
    plants_in_chip,
    yolo_seg_line,
)


def test_yolo_seg_line_normalizes_polygon():
    line = yolo_seg_line(0, [(0.0, 0.0), (100.0, 0.0), (100.0, 50.0), (0.0, 50.0)], 200, 100)
    parts = [float(x) for x in line.split()]
    assert parts[0] == 0
    assert parts[1:3] == [0.0, 0.0]
    assert parts[3:5] == [0.5, 0.0]
    assert parts[5:7] == [0.5, 0.5]


def test_chip_windows_covers_2048_with_overlap():
    wins = chip_windows(2048, 2048, chip=1024, stride=512)
    assert (0, 0, 1024, 1024) in wins
    assert (1024, 1024, 1024, 1024) in wins
    assert len(wins) == 9


def test_chip_windows_640_covers_full_tile():
    wins = chip_windows(2048, 2048, chip=640, stride=320)
    assert wins[0] == (0, 0, 640, 640)
    assert any(x0 + w == 2048 and y0 + h == 2048 for x0, y0, w, h in wins)
    assert len(wins) >= 25


def test_plants_in_chip_keeps_centroid_inside():
    plant = [(10.0, 10.0), (20.0, 10.0), (20.0, 20.0), (10.0, 20.0)]
    outside = [(2000.0, 2000.0), (2010.0, 2000.0), (2010.0, 2010.0), (2000.0, 2010.0)]
    kept = plants_in_chip([plant, outside], 0, 0, 1024, 1024)
    assert len(kept) == 1
    assert kept[0][0] == (10.0, 10.0)


def test_canonical_tile_name_strips_marcaj_job_prefix():
    assert canonical_tile_name("1713_siret3_r017_c008.tif") == "siret3_r017_c008.tif"
    assert canonical_tile_name("images/train/1750_siret3_r022_c012.tif") == "siret3_r022_c012.tif"
    assert canonical_tile_name("siret3_r006_c004.tif") == "siret3_r006_c004.tif"


def test_plants_from_cvat_xml_keeps_empty_tiles_and_vineyard_only():
    xml = """<?xml version="1.0"?>
    <annotations>
      <image id="0" name="1713_siret3_r017_c008.tif" width="2048" height="2048"/>
      <image id="1" name="1750_siret3_r022_c012.tif" width="2048" height="2048">
        <polygon label="vineyard" points="10,10;20,10;20,20;10,20"/>
        <polygon label="interrow_area" points="0,0;100,0;100,100;0,100"/>
        <polyline label="row" points="0,5;100,5"/>
      </image>
    </annotations>
    """
    tiles = dict(plants_from_cvat_xml(xml))
    assert tiles["siret3_r017_c008.tif"] == []
    assert len(tiles["siret3_r022_c012.tif"]) == 1
    assert tiles["siret3_r022_c012.tif"][0][0] == (10.0, 10.0)
