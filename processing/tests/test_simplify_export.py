from siret3.derive import clip_simplify_ring


def test_clip_simplify_ring_drops_dense_verts_and_clips_to_tile():
    # 200-point circle, partly outside the 100x100 tile
    import math

    pts = [
        (50 + 80 * math.cos(t), 50 + 80 * math.sin(t))
        for t in [i * 2 * math.pi / 200 for i in range(200)]
    ]
    pts.append(pts[0])
    out = clip_simplify_ring(pts, 100, 100, tolerance=4.0)
    assert 4 <= len(out) <= 40
    assert all(0.0 <= x <= 100.0 and 0.0 <= y <= 100.0 for x, y in out)
