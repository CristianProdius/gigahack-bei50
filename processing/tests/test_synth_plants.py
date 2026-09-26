import numpy as np

from siret3.example_yolo import yolo_seg_line
from siret3.synth_plants import crop_plant, paste_plants_on_background


def test_crop_plant_returns_rgba_cutout():
    rgb = np.zeros((20, 20, 3), dtype=np.uint8)
    rgb[5:15, 5:15] = (0, 200, 0)
    poly = [(5.0, 5.0), (15.0, 5.0), (15.0, 15.0), (5.0, 15.0)]
    cut, local = crop_plant(rgb, poly, pad=1)
    assert cut.ndim == 3 and cut.shape[2] == 4
    assert cut[..., 3].max() > 0
    assert len(local) == 4


def test_paste_plants_writes_normalized_yolo_polygons():
    bg = np.full((64, 64, 3), 40, dtype=np.uint8)
    plant = np.zeros((12, 12, 4), dtype=np.uint8)
    plant[2:10, 2:10] = (10, 180, 20, 255)
    local = [(2.0, 2.0), (10.0, 2.0), (10.0, 10.0), (2.0, 10.0)]
    image, polys = paste_plants_on_background(
        bg, [(plant, local)], n_plants=1, rng_seed=1
    )
    assert image.shape == (64, 64, 3)
    assert len(polys) == 1
    line = yolo_seg_line(0, polys[0], 64, 64)
    parts = [float(x) for x in line.split()]
    assert parts[0] == 0
    assert all(0.0 <= v <= 1.0 for v in parts[1:])


def test_paste_plants_can_emit_empty_negative():
    bg = np.full((32, 32, 3), 80, dtype=np.uint8)
    image, polys = paste_plants_on_background(bg, [], n_plants=0, rng_seed=0)
    assert image.shape == (32, 32, 3)
    assert polys == []
