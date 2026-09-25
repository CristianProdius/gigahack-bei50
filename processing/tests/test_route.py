from siret3.route import closed_walk, is_passable, snap_start


def test_snap_start_within_five_metres():
    nodes = [(0.0, 0.0), (10.0, 0.0)]
    assert snap_start((3.0, 0.0), nodes) == (0.0, 0.0)


def test_snap_start_rejects_far_point():
    try:
        snap_start((40.0, 0.0), [(0.0, 0.0)])
    except ValueError as exc:
        assert "5" in str(exc) or "limit" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_forbidden_zone_not_passable():
    inter = [[(0, 0), (10, 0), (10, 10), (0, 10)]]
    forbidden = [[(4, 4), (6, 4), (6, 6), (4, 6)]]
    assert is_passable((1, 1), inter, [], forbidden) is True
    assert is_passable((5, 5), inter, [], forbidden) is False


def test_closed_walk_returns_to_start():
    pts = [(0.0, 0.0), (8.0, 0.0), (8.0, 6.0), (0.0, 6.0)]
    tour = closed_walk(pts, (0.1, 0.0))
    assert tour[0] == tour[-1]
    assert len(tour) >= 2
