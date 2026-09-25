from __future__ import annotations

import base64
import io
import math
import urllib.request
from pathlib import Path
from typing import Any



def _source_bytes(source: str) -> bytes:
    if source.startswith('data:'):
        if ';base64,' not in source:
            raise ValueError('only base64 data URLs are supported')
        try:
            return base64.b64decode(source.split(';base64,', 1)[1], validate=False)
        except Exception as exc:
            raise ValueError('invalid base64 data URL') from exc
    if source.startswith(('http://', 'https://')):
        with urllib.request.urlopen(source, timeout=30) as response:  # nosec - explicit user-supplied image source
            return response.read()
    path = Path(source).expanduser()
    if not path.is_file():
        raise ValueError(f'image source does not exist: {source}')
    return path.read_bytes()


def _parse_box(value: str) -> tuple[int, int, int, int]:
    try:
        parts = [float(x.strip()) for x in value.split(',')]
    except ValueError as exc:
        raise ValueError('--box must be x,y,width,height') from exc
    if len(parts) != 4:
        raise ValueError('--box must be x,y,width,height')
    x, y, w, h = parts
    if not all(math.isfinite(x) for x in parts) or w <= 0 or h <= 0 or x < 0 or y < 0:
        raise ValueError('--box coordinates must be finite, non-negative, and have positive width/height')
    return round(x), round(y), round(w), round(h)


def _parse_aspect(value: str) -> tuple[float, float]:
    sep = ':' if ':' in value else ','
    try:
        parts = [float(x.strip()) for x in value.split(sep)]
    except ValueError as exc:
        raise ValueError('--aspect must be WIDTH:HEIGHT') from exc
    if len(parts) != 2 or not all(math.isfinite(x) and x > 0 for x in parts):
        raise ValueError('--aspect must contain two positive finite numbers')
    return parts[0], parts[1]


def _aspect_box(width: int, height: int, aspect: tuple[float, float], position: int) -> tuple[int, int, int, int]:
    if position not in range(9):
        raise ValueError('--position must be an integer from 0 through 8')
    aw, ah = aspect
    ratio = aw / ah
    if width / height > ratio:
        crop_h = height
        crop_w = round(height * ratio)
    else:
        crop_w = width
        crop_h = round(width / ratio)
    col = position % 3
    row = position // 3
    x = (0, (width - crop_w) // 2, width - crop_w)[col]
    y = (0, (height - crop_h) // 2, height - crop_h)[row]
    return x, y, crop_w, crop_h


def crop_webp(source: str, *, box: str | None = None, aspect: str | None = None, position: int = 4, quality: int = 92) -> tuple[bytes, dict[str, Any]]:
    if (box is None) == (aspect is None):
        raise ValueError('use exactly one of --box or --aspect')
    if not 0 <= quality <= 100:
        raise ValueError('--quality must be between 0 and 100')
    try:
        from PIL import Image
    except ImportError as exc:
        raise ValueError('image cropping requires Pillow; install the optional image dependency before using crop-image or crop-field') from exc
    raw = _source_bytes(source)
    with Image.open(io.BytesIO(raw)) as img:
        img.load()
        width, height = img.size
        if box is not None:
            x, y, w, h = _parse_box(box)
        else:
            x, y, w, h = _aspect_box(width, height, _parse_aspect(aspect or ''), position)
        if x + w > width or y + h > height:
            raise ValueError(f'crop box {x},{y},{w},{h} exceeds image bounds {width}x{height}')
        cropped = img.crop((x, y, x + w, y + h))
        if cropped.mode not in {'RGB', 'RGBA'}:
            cropped = cropped.convert('RGBA' if 'A' in cropped.getbands() else 'RGB')
        out = io.BytesIO()
        cropped.save(out, format='WEBP', quality=quality, method=6)
        data = out.getvalue()
    return data, {
        'source_size': [width, height],
        'crop_box': [x, y, w, h],
        'output_size': [w, h],
        'format': 'webp',
        'quality': quality,
    }


def webp_data_url(data: bytes) -> str:
    return 'data:image/webp;base64,' + base64.b64encode(data).decode('ascii')
