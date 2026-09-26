from siret3.filter_plants import drop_sparse_tile_canopies, nms_canopy_centroids


def _plant(tile: str, x: float, y: float, score: float = 0.6) -> dict:
    return {
        "type": "Feature",
        "properties": {"kind": "vineyard", "label": "vineyard", "tile": tile, "score": score},
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[x, y], [x + 0.2, y], [x + 0.2, y + 0.2], [x, y + 0.2], [x, y]]],
        },
    }


def test_drop_sparse_tile_canopies_clears_few_plants_keeps_waste():
    feats = [_plant("empty.tif", i, 0) for i in range(3)]
    feats.append(
        {
            "type": "Feature",
            "properties": {"kind": "waste", "tile": "empty.tif"},
            "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]},
        }
    )
    dense = [_plant("full.tif", i, 0) for i in range(12)]
    out = drop_sparse_tile_canopies(feats + dense, min_plants=10)
    kinds = [(f["properties"]["tile"], f["properties"]["kind"]) for f in out]
    assert kinds.count(("empty.tif", "vineyard")) == 0
    assert kinds.count(("empty.tif", "waste")) == 1
    assert kinds.count(("full.tif", "vineyard")) == 12


def test_nms_canopy_centroids_keeps_highest_score_within_half_metre():
    a = _plant("t.tif", 0.0, 0.0, score=0.4)
    b = _plant("t.tif", 0.1, 0.0, score=0.9)
    far = _plant("t.tif", 3.0, 0.0, score=0.5)
    waste = {
        "type": "Feature",
        "properties": {"kind": "waste", "tile": "t.tif"},
        "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]},
    }
    out = nms_canopy_centroids([a, b, far, waste], min_dist_m=0.5)
    vines = [f for f in out if f["properties"]["kind"] == "vineyard"]
    assert len(vines) == 2
    assert {f["properties"]["score"] for f in vines} == {0.9, 0.5}
    assert any(f["properties"]["kind"] == "waste" for f in out)
