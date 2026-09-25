import zipfile
from pathlib import Path

import pytest

from siret3.cvat11 import (
    MAX_ZIP_BYTES,
    CvatImage,
    CvatShape,
    build_part_zips,
    build_team_upload_zip,
    official_part_membership,
)
from siret3.cvat_parse import parse_cvat_zip, shapes_semantically_equal

REPO = Path(__file__).resolve().parents[2]
EXAMPLE_ZIP = REPO / "data/challenge/05_examples/siret3_examples_cvat.zip"
TILES = REPO / "data/tiles"
PARTS = REPO / "data/challenge/01_tiles"


def _tiny_tif(path: Path, payload: bytes = b"TIFF") -> None:
    path.write_bytes(payload)


def test_official_part_membership_counts():
    if not any(PARTS.glob("siret3_challenge_tiles_part*of5.zip")):
        pytest.skip("official tile part ZIPs missing")
    parts = official_part_membership(PARTS)
    assert sorted(parts) == [
        "siret3_challenge_tiles_part1of5.zip",
        "siret3_challenge_tiles_part2of5.zip",
        "siret3_challenge_tiles_part3of5.zip",
        "siret3_challenge_tiles_part4of5.zip",
        "siret3_challenge_tiles_part5of5.zip",
    ]
    counts = [len(parts[k]) for k in sorted(parts)]
    assert counts == [74, 71, 78, 76, 12]
    assert sum(counts) == 311
    assert "siret3_r006_c004.tif" in parts["siret3_challenge_tiles_part1of5.zip"]


def test_build_team_upload_zip_copies_original_names(tmp_path: Path):
    tiles = tmp_path / "tiles"
    tiles.mkdir()
    _tiny_tif(tiles / "siret3_r001_c001.tif")
    images = [
        CvatImage(
            name="siret3_r001_c001.tif",
            width=8,
            height=8,
            shapes=[
                CvatShape(
                    tag="polygon",
                    label="vineyard",
                    points=[(1, 1), (4, 1), (4, 4)],
                    attributes={"vineyard_id": "V01"},
                )
            ],
        )
    ]
    out = tmp_path / "team.zip"
    build_team_upload_zip(images, tiles, out)
    with zipfile.ZipFile(out) as zf:
        names = set(zf.namelist())
        assert names == {"annotations.xml", "images/siret3_r001_c001.tif"}
        assert zf.read("images/siret3_r001_c001.tif") == b"TIFF"
        assert zf.getinfo("images/siret3_r001_c001.tif").compress_type == zipfile.ZIP_STORED
        assert zf.getinfo("annotations.xml").compress_type == zipfile.ZIP_DEFLATED


def test_build_part_zips_follows_membership(tmp_path: Path):
    tiles = tmp_path / "tiles"
    tiles.mkdir()
    _tiny_tif(tiles / "siret3_r001_c001.tif")
    _tiny_tif(tiles / "siret3_r002_c002.tif")
    parts_dir = tmp_path / "parts"
    parts_dir.mkdir()
    with zipfile.ZipFile(parts_dir / "siret3_challenge_tiles_part1of5.zip", "w") as zf:
        zf.writestr("siret3_r001_c001.tif", b"x")
    with zipfile.ZipFile(parts_dir / "siret3_challenge_tiles_part2of5.zip", "w") as zf:
        zf.writestr("siret3_r002_c002.tif", b"x")
    images = [
        CvatImage(name="siret3_r001_c001.tif", width=8, height=8, shapes=[]),
        CvatImage(name="siret3_r002_c002.tif", width=8, height=8, shapes=[]),
    ]
    out_dir = tmp_path / "out"
    written = build_part_zips(images, tiles, parts_dir, out_dir)
    assert [p.name for p in written] == [
        "siret3_challenge_tiles_part1of5.zip",
        "siret3_challenge_tiles_part2of5.zip",
    ]
    with zipfile.ZipFile(written[0]) as zf:
        assert "images/siret3_r001_c001.tif" in zf.namelist()
        assert "images/siret3_r002_c002.tif" not in zf.namelist()


def test_build_part_zips_rejects_over_limit(tmp_path: Path):
    tiles = tmp_path / "tiles"
    tiles.mkdir()
    _tiny_tif(tiles / "siret3_r001_c001.tif", b"0" * 200)
    parts_dir = tmp_path / "parts"
    parts_dir.mkdir()
    with zipfile.ZipFile(parts_dir / "siret3_challenge_tiles_part1of5.zip", "w") as zf:
        zf.writestr("siret3_r001_c001.tif", b"x")
    images = [CvatImage(name="siret3_r001_c001.tif", width=8, height=8, shapes=[])]
    with pytest.raises(ValueError, match="90 MB"):
        build_part_zips(images, tiles, parts_dir, tmp_path / "out", max_bytes=50)


@pytest.mark.skipif(
    not EXAMPLE_ZIP.is_file() or not (TILES / "siret3_r021_c012.tif").is_file(),
    reason="example ZIP or tiles missing",
)
def test_example_zip_roundtrip_from_official_parse(tmp_path: Path):
    images = parse_cvat_zip(EXAMPLE_ZIP)
    out = tmp_path / "examples.zip"
    build_team_upload_zip(images, TILES, out, task_name="examples")
    again = parse_cvat_zip(out)
    assert shapes_semantically_equal(images, again)
    assert out.stat().st_size < MAX_ZIP_BYTES
