from __future__ import annotations

import io
from pathlib import Path

from PIL import Image

from iccplus_tools.image_edit import crop_webp, webp_data_url


def make_png(path: Path, size=(100, 50)) -> None:
    img = Image.new('RGB', size)
    img.save(path, format='PNG')


def output_size(data: bytes) -> tuple[int, int]:
    with Image.open(io.BytesIO(data)) as img:
        return img.size


def test_crop_exact_box(tmp_path: Path) -> None:
    src = tmp_path / 'src.png'
    make_png(src)
    data, meta = crop_webp(str(src), box='10,5,30,20')
    assert output_size(data) == (30, 20)
    assert meta['source_size'] == [100, 50]
    assert meta['crop_box'] == [10, 5, 30, 20]
    assert meta['output_size'] == [30, 20]


def test_aspect_crop_center_matches_creator_grid(tmp_path: Path) -> None:
    src = tmp_path / 'src.png'
    make_png(src, (100, 50))
    data, meta = crop_webp(str(src), aspect='1:1', position=4)
    assert output_size(data) == (50, 50)
    assert meta['crop_box'] == [25, 0, 50, 50]


def test_aspect_crop_corner_positions(tmp_path: Path) -> None:
    src = tmp_path / 'src.png'
    make_png(src, (100, 50))
    expected = {
        0: [0, 0, 50, 50],
        2: [50, 0, 50, 50],
        6: [0, 0, 50, 50],
        8: [50, 0, 50, 50],
    }
    for position, box in expected.items():
        _, meta = crop_webp(str(src), aspect='1:1', position=position)
        assert meta['crop_box'] == box


def test_data_url_round_trip(tmp_path: Path) -> None:
    src = tmp_path / 'src.png'
    make_png(src, (20, 20))
    data, _ = crop_webp(str(src), box='0,0,10,10')
    url = webp_data_url(data)
    assert url.startswith('data:image/webp;base64,')
    data2, meta = crop_webp(url, box='0,0,5,5')
    assert output_size(data2) == (5, 5)
    assert meta['source_size'] == [10, 10]
