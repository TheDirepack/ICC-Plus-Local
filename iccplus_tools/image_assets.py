from __future__ import annotations

import base64
import mimetypes
import os
import tempfile
from pathlib import Path
from typing import Any

from .assets import Config, BlobResult, compress_blob, data_url_from, sniff_mime


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f'.{path.name}.', suffix='.tmp', dir=path.parent)
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, 'wb') as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def _data_url_parts(value: str) -> tuple[str, bytes] | None:
    if not value.startswith('data:image/') or ';base64,' not in value:
        return None
    head, encoded = value.split(';base64,', 1)
    mime = head[5:].lower().replace('image/jpg', 'image/jpeg')
    try:
        data = base64.b64decode(encoded, validate=False)
    except Exception as exc:
        raise ValueError('invalid base64 image data URL') from exc
    return mime, data


def prepare_image_reference(
    value: str,
    *,
    base_dir: Path | None = None,
    embed_local: bool = False,
    config: Config | None = None,
) -> tuple[str, dict[str, Any]]:
    """Prepare one image reference for project storage.

    Local files and embedded data URLs are automatically compressed when a
    supported encoder can produce a worthwhile smaller result. Remote URLs are
    retained as URLs and are not downloaded merely to optimize them.
    """
    cfg = config or Config()
    raw_value = str(value or '')
    if not raw_value:
        return raw_value, {'automatic': True, 'changed': False, 'reason': 'empty'}

    parts = _data_url_parts(raw_value)
    if parts is not None:
        mime, data = parts
        result = compress_blob(data, mime, cfg)
        final = data_url_from(result) if result.changed else raw_value
        if not result.changed and result.source_mime.startswith('image/') and result.source_mime != mime:
            final = f'data:{result.source_mime};base64,' + base64.b64encode(data).decode('ascii')
        report = {
            'automatic': True,
            'source': 'data-url',
            'changed': final != raw_value,
            'compression_changed': bool(result.changed),
            'reason': result.reason,
            'source_mime': result.source_mime,
            'output_mime': result.mime,
            'bytes_before': len(data),
            'bytes_after': len(result.data),
            'encoder': result.encoder,
            'error': result.error,
        }
        return final, report

    if raw_value.startswith(('http://', 'https://', '//')):
        return raw_value, {'automatic': True, 'changed': False, 'reason': 'remote-url-kept'}

    root = (base_dir or Path.cwd()).expanduser().resolve()
    raw_path = Path(raw_value).expanduser()
    path = raw_path if raw_path.is_absolute() else root / raw_path
    path = path.resolve()
    if not path.is_file():
        return raw_value, {'automatic': True, 'changed': False, 'reason': 'local-file-not-found'}

    data = path.read_bytes()
    declared = mimetypes.guess_type(path.name)[0]
    actual = sniff_mime(data)
    mime = actual if actual.startswith('image/') else declared
    if not mime or not mime.startswith('image/'):
        raise ValueError(f'image source is not a recognized image: {path}')
    result = compress_blob(data, mime, cfg)

    if embed_local:
        chosen = result.data if result.changed else data
        chosen_mime = result.mime if result.changed else (result.source_mime if result.source_mime.startswith('image/') else mime)
        final = f'data:{chosen_mime};base64,' + base64.b64encode(chosen).decode('ascii')
        return final, {
            'automatic': True,
            'source': str(path),
            'changed': bool(result.changed),
            'reason': result.reason,
            'source_mime': result.source_mime,
            'output_mime': chosen_mime,
            'bytes_before': len(data),
            'bytes_after': len(chosen),
            'encoder': result.encoder,
            'error': result.error,
            'embedded': True,
        }

    if not result.changed:
        return raw_value, {
            'automatic': True,
            'source': str(path),
            'changed': False,
            'reason': result.reason,
            'source_mime': result.source_mime,
            'output_mime': result.mime,
            'bytes_before': len(data),
            'bytes_after': len(data),
            'encoder': result.encoder,
            'error': result.error,
            'output': raw_value,
        }

    target = path.with_suffix(result.ext)
    _atomic_write(target, result.data)
    if raw_path.is_absolute():
        final = str(target)
    else:
        try:
            final = target.relative_to(root).as_posix()
        except ValueError:
            final = str(target)
    return final, {
        'automatic': True,
        'source': str(path),
        'changed': True,
        'reason': result.reason,
        'source_mime': result.source_mime,
        'output_mime': result.mime,
        'bytes_before': len(data),
        'bytes_after': len(result.data),
        'encoder': result.encoder,
        'error': result.error,
        'output': final,
    }
