from siret3.geo import clip_pixel_coords


def test_clip_keeps_interior_polygon():
    ring = [(10, 10), (90, 10), (90, 80), (10, 80), (10, 10)]
    parts = clip_pixel_coords(ring, 100, 100, kind="vineyard")
    assert len(parts) == 1
    assert parts[0][0][0] >= 0


def test_clip_drops_outside_polygon():
    ring = [(200, 200), (240, 200), (240, 240), (200, 240)]
    assert clip_pixel_coords(ring, 100, 100, kind="vineyard") == []


def test_clip_row_line():
    parts = clip_pixel_coords([(0, 50), (200, 50)], 100, 100, kind="row")
    assert len(parts) == 1
    xs = [p[0] for p in parts[0]]
    assert max(xs) <= 100.01
