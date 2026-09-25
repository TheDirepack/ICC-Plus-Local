#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import concurrent.futures
import dataclasses
import hashlib
import functools
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Iterable

from .version import __version__

VERSION = __version__

TEXT_EXTS = {
    ".json", ".js", ".mjs", ".cjs", ".html", ".htm", ".css", ".txt",
    ".md", ".vue", ".ts", ".tsx", ".jsx"
}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tif", ".tiff", ".avif"}
DATA_URL_RE = re.compile(
    r"data:image/(?P<mime>png|jpe?g|gif|webp|bmp|tiff?|avif);base64,(?P<data>[A-Za-z0-9+/]+={0,2})",
    re.IGNORECASE,
)
QUOTED_IMAGE_RE = re.compile(
    r"(?P<quote>[\"'`])(?P<path>(?!data:|https?://|//)[^\"'`\r\n]+?\.(?:png|jpe?g|gif|webp|bmp|tiff?|avif))(?P<suffix>[?#][^\"'`\r\n]*)?(?P=quote)",
    re.IGNORECASE,
)
CSS_URL_RE = re.compile(
    r"url\(\s*(?P<quote>[\"']?)(?P<path>(?!data:|https?://|//)[^\"')\r\n]+?\.(?:png|jpe?g|gif|webp|bmp|tiff?|avif))(?P<suffix>[?#][^\"')\r\n]*)?(?P=quote)\s*\)",
    re.IGNORECASE,
)

MIME_TO_EXT = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/bmp": ".bmp",
    "image/tiff": ".tiff",
    "image/avif": ".avif",
}
EXT_TO_MIME = {
    ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
    ".gif": "image/gif", ".webp": "image/webp", ".bmp": "image/bmp",
    ".tif": "image/tiff", ".tiff": "image/tiff", ".avif": "image/avif",
}

class ToolError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code

@dataclasses.dataclass(frozen=True)
class Config:
    quality: int = 60
    workers: int = max(1, min(8, (os.cpu_count() or 2) // 2 or 1))
    encoder: str = "auto"
    assets: str = "rewrite"
    gif_mode: str = "webp"
    recompress_avif: bool = False
    min_savings_bytes: int = 256
    min_savings_percent: float = 2.0
    dry_run: bool = False
    pretty: bool = False
    use_convert_any: bool = True

@dataclasses.dataclass
class BlobResult:
    changed: bool
    data: bytes
    mime: str
    ext: str
    source_mime: str
    animated: bool = False
    encoder: str | None = None
    reason: str = ""
    error: str | None = None

    @property
    def bytes_after(self) -> int:
        return len(self.data)

@dataclasses.dataclass
class Totals:
    files_seen: int = 0
    files_written: int = 0
    images_seen: int = 0
    images_changed: int = 0
    images_kept: int = 0
    embedded_seen: int = 0
    embedded_changed: int = 0
    bytes_before: int = 0
    bytes_after: int = 0
    references_rewritten: int = 0
    warnings: int = 0

    def as_dict(self) -> dict:
        d = dataclasses.asdict(self)
        saved = self.bytes_before - self.bytes_after
        d["bytes_saved"] = saved
        d["savings_percent"] = round((saved / self.bytes_before * 100.0), 2) if self.bytes_before else 0.0
        return d


def which_any(names: Iterable[str]) -> str | None:
    for name in names:
        p = shutil.which(name)
        if p:
            return p
    return None


def run(cmd: list[str], *, timeout: int = 300) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=timeout)


def sniff_mime(data: bytes) -> str:
    if len(data) >= 3 and data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    if data.startswith(b"BM"):
        return "image/bmp"
    if data.startswith((b"II*\x00", b"MM\x00*")):
        return "image/tiff"
    if len(data) >= 16 and data[4:8] == b"ftyp":
        brands = {data[8:12]}
        brands.update(data[i:i+4] for i in range(16, min(len(data), 128), 4))
        if brands & {b"avif", b"avis", b"avio", b"mif1", b"msf1"}:
            return "image/avif"
    return "application/octet-stream"


def png_has_alpha(data: bytes) -> bool:
    if not data.startswith(b"\x89PNG\r\n\x1a\n") or len(data) < 26:
        return False
    color_type = data[25]
    return color_type in (4, 6) or b"tRNS" in data


def webp_flags(data: bytes) -> tuple[bool, bool]:
    if not (len(data) >= 16 and data[:4] == b"RIFF" and data[8:12] == b"WEBP"):
        return False, False
    pos = 12
    animated = False
    alpha = False
    while pos + 8 <= len(data):
        ctype = data[pos:pos+4]
        size = int.from_bytes(data[pos+4:pos+8], "little")
        body = data[pos+8:pos+8+size]
        if ctype == b"VP8X" and body:
            flags = body[0]
            animated = bool(flags & 0x02)
            alpha = bool(flags & 0x10)
        elif ctype == b"ANIM":
            animated = True
        elif ctype == b"ALPH":
            alpha = True
        pos += 8 + size + (size & 1)
    return animated, alpha


def gif_frame_count(data: bytes, magick: str | None) -> int:
    if magick:
        with tempfile.TemporaryDirectory(prefix="cyoa-gif-") as td:
            src = Path(td) / "in.gif"
            src.write_bytes(data)
            cp = run([magick, "identify", "-format", "%n\n", str(src)], timeout=60)
            if cp.returncode == 0:
                nums = [int(x) for x in cp.stdout.decode("utf-8", "ignore").split() if x.isdigit()]
                if nums:
                    return max(nums)
    # Safe fallback parser: walk GIF blocks and count image descriptors.
    try:
        if not data.startswith((b"GIF87a", b"GIF89a")) or len(data) < 13:
            return 1
        packed = data[10]
        pos = 13
        if packed & 0x80:
            pos += 3 * (2 ** ((packed & 0x07) + 1))
        frames = 0
        while pos < len(data):
            marker = data[pos]
            pos += 1
            if marker == 0x3B:
                break
            if marker == 0x2C:
                frames += 1
                if pos + 9 > len(data):
                    break
                packed_img = data[pos + 8]
                pos += 9
                if packed_img & 0x80:
                    pos += 3 * (2 ** ((packed_img & 0x07) + 1))
                if pos >= len(data):
                    break
                pos += 1  # LZW min code size
                while pos < len(data):
                    n = data[pos]
                    pos += 1
                    if n == 0:
                        break
                    pos += n
            elif marker == 0x21:
                if pos >= len(data):
                    break
                pos += 1  # extension label
                while pos < len(data):
                    n = data[pos]
                    pos += 1
                    if n == 0:
                        break
                    pos += n
            else:
                break
        return max(frames, 1)
    except Exception:
        return 1


def has_alpha(data: bytes, mime: str) -> bool:
    if mime == "image/png":
        return png_has_alpha(data)
    if mime == "image/webp":
        return webp_flags(data)[1]
    if mime == "image/gif":
        # GIF transparency is cheap to preserve by taking the alpha-safe path.
        return True
    return False


def quality_from_cq(cq: int) -> int:
    cq = max(0, min(63, cq))
    return max(1, min(100, round((63 - cq) * 100 / 63)))


def savings_ok(old: int, new: int, cfg: Config) -> bool:
    saved = old - new
    if saved < cfg.min_savings_bytes:
        return False
    if old and (saved / old * 100.0) < cfg.min_savings_percent:
        return False
    return True


@functools.lru_cache(maxsize=8)
def magick_supports_avif(magick: str) -> bool:
    cp = run([magick, "-list", "format"], timeout=30)
    if cp.returncode != 0:
        return False
    text = cp.stdout.decode("utf-8", "ignore")
    return bool(re.search(r"^\s*(?:AVIF|HEIC)\*?\s+rw", text, re.MULTILINE | re.IGNORECASE))


def encode_avif_magick(data: bytes, mime: str, quality: int, magick: str) -> bytes:
    if not magick_supports_avif(magick):
        raise RuntimeError("ImageMagick has no writable AVIF/HEIC coder")
    ext = MIME_TO_EXT.get(mime, ".img")
    with tempfile.TemporaryDirectory(prefix="cyoa-avif-") as td:
        src = Path(td) / f"in{ext}"
        dst = Path(td) / "out.avif"
        src.write_bytes(data)
        cp = run([magick, str(src), "-auto-orient", "-strip", "-quality", str(quality), str(dst)])
        if cp.returncode != 0 or not dst.exists():
            raise RuntimeError(cp.stderr.decode("utf-8", "replace").strip() or "ImageMagick AVIF encode failed")
        out = dst.read_bytes()
        if sniff_mime(out) != "image/avif":
            raise RuntimeError("ImageMagick did not produce AVIF bytes")
        return out


def encode_avif_ffmpeg(data: bytes, mime: str, quality: int, ffmpeg: str, alpha: bool = False) -> bytes:
    ext = MIME_TO_EXT.get(mime, ".img")
    # Map conventional 0..100 quality to AV1 CRF 63..0.
    crf = max(0, min(63, round((100 - quality) * 63 / 100)))
    with tempfile.TemporaryDirectory(prefix="cyoa-avif-") as td:
        src = Path(td) / f"in{ext}"
        dst = Path(td) / "out.avif"
        src.write_bytes(data)
        base = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(src)]
        if alpha:
            cmd = base + [
                "-filter_complex", "[0:v]alphaextract[a]", "-map", "0:v", "-map", "[a]",
                "-frames:v", "1", "-map_metadata", "-1", "-c:v", "libaom-av1",
                "-still-picture", "1", "-crf", str(crf), "-b:v", "0",
                "-cpu-used", "6", "-row-mt", "1",
                "-pix_fmt:v:0", "yuv420p", "-pix_fmt:v:1", "gray", str(dst)
            ]
        else:
            cmd = base + [
                "-frames:v", "1", "-map_metadata", "-1", "-c:v", "libaom-av1",
                "-still-picture", "1", "-crf", str(crf), "-b:v", "0",
                "-cpu-used", "6", "-row-mt", "1", "-pix_fmt", "yuv420p", str(dst)
            ]
        cp = run(cmd)
        if cp.returncode != 0 or not dst.exists():
            raise RuntimeError(cp.stderr.decode("utf-8", "replace").strip() or "FFmpeg AVIF encode failed")
        out = dst.read_bytes()
        if sniff_mime(out) != "image/avif":
            raise RuntimeError("FFmpeg did not produce AVIF bytes")
        return out


def encode_gif_webp(data: bytes, quality: int, magick: str | None, ffmpeg: str | None) -> tuple[bytes, str]:
    with tempfile.TemporaryDirectory(prefix="cyoa-gif-") as td:
        src = Path(td) / "in.gif"
        dst = Path(td) / "out.webp"
        src.write_bytes(data)
        if magick:
            cp = run([
                magick, str(src), "-coalesce", "-strip", "-quality", str(quality),
                "-define", "webp:method=6", str(dst)
            ])
            if cp.returncode == 0 and dst.exists():
                return dst.read_bytes(), "imagemagick"
        if ffmpeg:
            cp = run([
                ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(src),
                "-map_metadata", "-1", "-c:v", "libwebp_anim", "-quality", str(quality),
                "-compression_level", "6", "-loop", "0", str(dst)
            ])
            if cp.returncode == 0 and dst.exists():
                return dst.read_bytes(), "ffmpeg"
        raise RuntimeError("No available encoder could convert animated GIF to WebP")


def convert_via_convert_any(data: bytes, mime: str, convert_any: str) -> bytes | None:
    ext = MIME_TO_EXT.get(mime, ".img")
    with tempfile.TemporaryDirectory(prefix="cyoa-convert-") as td:
        src = Path(td) / f"in{ext}"
        dst = Path(td) / "decoded.png"
        src.write_bytes(data)
        cp = run([convert_any, str(src), "--to", "png", "--output", str(dst), "--overwrite"], timeout=300)
        if cp.returncode == 0 and dst.exists():
            return dst.read_bytes()
    return None


def compress_blob(data: bytes, declared_mime: str | None, cfg: Config) -> BlobResult:
    actual = sniff_mime(data)
    source_mime = actual if actual.startswith("image/") else (declared_mime or actual)
    magick = which_any(["magick"])
    ffmpeg = which_any(["ffmpeg"])
    convert_any = which_any(["convert-any"]) if cfg.use_convert_any else None

    if source_mime == "image/avif" and not cfg.recompress_avif:
        return BlobResult(False, data, "image/avif", ".avif", source_mime, reason="already-avif")

    animated = False
    if source_mime == "image/webp":
        animated = webp_flags(data)[0]
        if animated:
            return BlobResult(False, data, source_mime, ".webp", source_mime, animated=True, reason="animated-webp-kept")
    elif source_mime == "image/gif":
        animated = gif_frame_count(data, magick) > 1
        if animated:
            if cfg.gif_mode == "keep":
                return BlobResult(False, data, source_mime, ".gif", source_mime, animated=True, reason="animated-gif-kept")
            try:
                out, enc = encode_gif_webp(data, cfg.quality, magick, ffmpeg)
                if savings_ok(len(data), len(out), cfg):
                    return BlobResult(True, out, "image/webp", ".webp", source_mime, animated=True, encoder=enc, reason="animated-gif-to-webp")
                return BlobResult(False, data, source_mime, ".gif", source_mime, animated=True, reason="animated-conversion-not-smaller")
            except Exception as e:
                return BlobResult(False, data, source_mime, ".gif", source_mime, animated=True, reason="animated-conversion-failed", error=str(e))

    if source_mime not in MIME_TO_EXT:
        return BlobResult(False, data, source_mime, MIME_TO_EXT.get(source_mime, ".img"), source_mime, reason="unsupported")

    # FFmpeg handles AVIF alpha by storing the alpha mask as the second AV1 stream.
    # ImageMagick is a fallback only when its local build actually has a writable AVIF coder.
    candidates: list[tuple[str, callable]] = []
    alpha = has_alpha(data, source_mime)
    magick_avif = bool(magick and magick_supports_avif(magick))
    if cfg.encoder == "magick":
        if magick_avif:
            candidates.append(("imagemagick", lambda d=data, m=source_mime: encode_avif_magick(d, m, cfg.quality, magick)))
    elif cfg.encoder == "ffmpeg":
        if ffmpeg:
            candidates.append(("ffmpeg", lambda d=data, m=source_mime, a=alpha: encode_avif_ffmpeg(d, m, cfg.quality, ffmpeg, a)))
    else:
        if ffmpeg:
            candidates.append(("ffmpeg", lambda d=data, m=source_mime, a=alpha: encode_avif_ffmpeg(d, m, cfg.quality, ffmpeg, a)))
        if magick_avif:
            candidates.append(("imagemagick", lambda d=data, m=source_mime: encode_avif_magick(d, m, cfg.quality, magick)))

    if not candidates and convert_any:
        decoded = convert_via_convert_any(data, source_mime, convert_any)
        if decoded:
            return compress_blob(decoded, "image/png", dataclasses.replace(cfg, use_convert_any=False))

    errors = []
    for name, fn in candidates:
        try:
            out = fn()
            if savings_ok(len(data), len(out), cfg):
                return BlobResult(True, out, "image/avif", ".avif", source_mime, encoder=name, reason="converted")
            return BlobResult(False, data, source_mime, MIME_TO_EXT.get(source_mime, ".img"), source_mime, encoder=name, reason="conversion-not-smaller")
        except Exception as e:
            errors.append(f"{name}: {e}")

    return BlobResult(False, data, source_mime, MIME_TO_EXT.get(source_mime, ".img"), source_mime, reason="no-encoder", error="; ".join(errors) or "No suitable encoder found")


def data_url_from(result: BlobResult) -> str:
    return f"data:{result.mime};base64,{base64.b64encode(result.data).decode('ascii')}"


def compress_embedded_text(text: str, cfg: Config, totals: Totals) -> tuple[str, list[dict]]:
    matches = list(DATA_URL_RE.finditer(text))
    totals.embedded_seen += len(matches)
    if not matches:
        return text, []

    jobs: dict[str, tuple[bytes, str]] = {}
    for m in matches:
        try:
            raw = base64.b64decode(m.group("data"), validate=True)
        except Exception:
            continue
        key = hashlib.sha256(raw).hexdigest()
        jobs.setdefault(key, (raw, f"image/{m.group('mime').lower().replace('jpg', 'jpeg')}"))

    results: dict[str, BlobResult] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=cfg.workers) as ex:
        future_map = {ex.submit(compress_blob, raw, mime, cfg): key for key, (raw, mime) in jobs.items()}
        for fut in concurrent.futures.as_completed(future_map):
            key = future_map[fut]
            try:
                results[key] = fut.result()
            except Exception as e:
                raw, mime = jobs[key]
                results[key] = BlobResult(False, raw, mime, MIME_TO_EXT.get(mime, ".img"), mime, reason="exception", error=str(e))

    edits: list[tuple[int, int, str]] = []
    detail: list[dict] = []
    for m in matches:
        try:
            raw = base64.b64decode(m.group("data"), validate=True)
        except Exception:
            detail.append({"changed": False, "reason": "invalid-base64"})
            continue
        key = hashlib.sha256(raw).hexdigest()
        r = results[key]
        replacement = data_url_from(r) if r.changed else m.group(0)
        # If the declared MIME is wrong but bytes are valid, correct it even when the image stays unchanged.
        if not r.changed and r.source_mime.startswith("image/"):
            corrected = f"data:{r.source_mime};base64,{m.group('data')}"
            if corrected != m.group(0):
                replacement = corrected
        if replacement != m.group(0):
            edits.append((m.start(), m.end(), replacement))
        if r.changed:
            totals.embedded_changed += 1
            totals.images_changed += 1
        else:
            totals.images_kept += 1
        if r.error:
            totals.warnings += 1
        totals.images_seen += 1
        detail.append({
            "changed": r.changed,
            "source_mime": r.source_mime,
            "output_mime": r.mime,
            "bytes_before": len(raw),
            "bytes_after": len(r.data),
            "animated": r.animated,
            "encoder": r.encoder,
            "reason": r.reason,
            **({"error": r.error} if r.error else {}),
        })

    for start, end, replacement in reversed(edits):
        text = text[:start] + replacement + text[end:]
    return text, detail


def default_file_output(path: Path, result_ext: str | None = None) -> Path:
    if result_ext:
        return path.with_name(f"{path.stem}.compressed{result_ext}")
    return path.with_name(f"{path.stem}.compressed{path.suffix}")


def unique_output_path(path: Path) -> Path:
    if not path.exists():
        return path
    if path.suffix:
        stem, suffix = path.stem, path.suffix
        for n in range(2, 10000):
            candidate = path.with_name(f"{stem}-{n}{suffix}")
            if not candidate.exists():
                return candidate
    else:
        for n in range(2, 10000):
            candidate = path.with_name(f"{path.name}-{n}")
            if not candidate.exists():
                return candidate
    raise ToolError("OUTPUT_EXISTS", f"Could not choose a free output path near: {path}")


def compact_result(result: dict) -> dict:
    out = {"input": result.get("input"), "output": result.get("output")}
    if result.get("type"):
        out["type"] = result["type"]
    if "changed" in result:
        out["changed"] = result["changed"]
    return out


def compact_totals(totals: Totals) -> dict:
    full = totals.as_dict()
    out = {
        "images": full["images_seen"],
        "changed": full["images_changed"],
        "bytes_before": full["bytes_before"],
        "bytes_after": full["bytes_after"],
        "bytes_saved": full["bytes_saved"],
        "savings_percent": full["savings_percent"],
    }
    if full["references_rewritten"]:
        out["references_rewritten"] = full["references_rewritten"]
    if full["warnings"]:
        out["warnings"] = full["warnings"]
    return out


def safe_read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            return path.read_text(encoding="utf-8-sig")
        except Exception:
            return None
    except Exception:
        return None


def normalize_ref_path(raw: str) -> str:
    return raw.replace("\\", "/")


def rewrite_asset_refs(text: str, text_rel: Path, mapping: dict[str, str]) -> tuple[str, int]:
    count = 0

    def resolve_and_replace(path_text: str) -> str:
        nonlocal count
        normalized = normalize_ref_path(path_text)
        if normalized.startswith("/"):
            key = normalized.lstrip("/")
        else:
            base = text_rel.parent.as_posix()
            key = os.path.normpath(os.path.join(base, normalized)).replace("\\", "/")
            while key.startswith("./"):
                key = key[2:]
        if key not in mapping:
            return path_text
        new_key = mapping[key]
        if normalized.startswith("/"):
            new_path = "/" + new_key
        else:
            new_path = os.path.relpath(new_key, text_rel.parent.as_posix() or ".").replace("\\", "/")
            if path_text.startswith("./") and not new_path.startswith("."):
                new_path = "./" + new_path
        if "\\" in path_text and "/" not in path_text:
            new_path = new_path.replace("/", "\\")
        count += 1
        return new_path

    def qrepl(m: re.Match) -> str:
        new_path = resolve_and_replace(m.group("path"))
        return f"{m.group('quote')}{new_path}{m.group('suffix') or ''}{m.group('quote')}"

    def crepl(m: re.Match) -> str:
        new_path = resolve_and_replace(m.group("path"))
        q = m.group("quote") or ""
        return f"url({q}{new_path}{m.group('suffix') or ''}{q})"

    text = QUOTED_IMAGE_RE.sub(qrepl, text)
    text = CSS_URL_RE.sub(crepl, text)
    return text, count


def process_text_file(src: Path, dst: Path, cfg: Config, totals: Totals, mapping: dict[str, str] | None = None, rel: Path | None = None) -> dict:
    text = safe_read_text(src)
    if text is None:
        shutil.copy2(src, dst)
        totals.files_written += 1
        return {"input": str(src), "output": str(dst), "changed": False, "reason": "non-utf8"}
    before_bytes = len(text.encode("utf-8"))
    new_text, embedded = compress_embedded_text(text, cfg, totals)
    refs = 0
    if mapping is not None and rel is not None:
        new_text, refs = rewrite_asset_refs(new_text, rel, mapping)
        totals.references_rewritten += refs
    after_bytes = len(new_text.encode("utf-8"))
    totals.bytes_before += before_bytes
    totals.bytes_after += after_bytes
    changed = new_text != text
    if not cfg.dry_run:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(new_text, encoding="utf-8")
        try:
            shutil.copystat(src, dst)
        except OSError:
            pass
    totals.files_written += 1
    return {
        "input": str(src), "output": str(dst), "changed": changed,
        "bytes_before": before_bytes, "bytes_after": after_bytes,
        "embedded_images": embedded, "references_rewritten": refs,
    }


def process_image_file(src: Path, dst_base: Path, cfg: Config, totals: Totals) -> tuple[dict, Path]:
    raw = src.read_bytes()
    declared = EXT_TO_MIME.get(src.suffix.lower())
    r = compress_blob(raw, declared, cfg)
    totals.images_seen += 1
    totals.bytes_before += len(raw)
    totals.bytes_after += len(r.data)
    if r.changed:
        totals.images_changed += 1
        dst = dst_base.with_suffix(r.ext)
        if not cfg.dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(r.data)
        totals.files_written += 1
    else:
        totals.images_kept += 1
        dst = dst_base.with_suffix(src.suffix)
        if not cfg.dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        totals.files_written += 1
    return ({
        "input": str(src), "output": str(dst), "changed": r.changed,
        "source_mime": r.source_mime, "output_mime": r.mime,
        "bytes_before": len(raw), "bytes_after": len(r.data),
        "animated": r.animated, "encoder": r.encoder, "reason": r.reason,
        **({"error": r.error} if r.error else {}),
    }, dst)


def process_single_file(src: Path, output: Path | None, cfg: Config, totals: Totals, in_place: bool) -> dict:
    totals.files_seen += 1
    suffix = src.suffix.lower()
    if suffix in IMAGE_EXTS:
        if in_place:
            raise ToolError("IN_PLACE_IMAGE_UNSUPPORTED", "Standalone image conversion changes the extension; use an output path instead of --in-place.")
        raw = src.read_bytes()
        probe = compress_blob(raw, EXT_TO_MIME.get(suffix), cfg)
        dst = output or unique_output_path(default_file_output(src, probe.ext if probe.changed else src.suffix))
        # Avoid doing the expensive encode twice by writing the probed result here.
        totals.images_seen += 1
        totals.bytes_before += len(raw)
        totals.bytes_after += len(probe.data)
        totals.images_changed += int(probe.changed)
        totals.images_kept += int(not probe.changed)
        totals.warnings += int(bool(probe.error))
        if not cfg.dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(probe.data)
        totals.files_written += 1
        return {
            "input": str(src), "output": str(dst), "changed": probe.changed,
            "source_mime": probe.source_mime, "output_mime": probe.mime,
            "bytes_before": len(raw), "bytes_after": len(probe.data),
            "animated": probe.animated, "encoder": probe.encoder, "reason": probe.reason,
            **({"error": probe.error} if probe.error else {}),
        }
    if suffix not in TEXT_EXTS:
        raise ToolError("UNSUPPORTED_FILE", f"Unsupported input file type: {src.suffix or '(none)'}")
    dst = src if in_place else (output or unique_output_path(default_file_output(src)))
    return process_text_file(src, dst, cfg, totals)


def process_directory(src: Path, output: Path | None, cfg: Config, totals: Totals, in_place: bool) -> dict:
    if in_place and cfg.assets == "rewrite":
        raise ToolError("IN_PLACE_PROJECT_UNSAFE", "--in-place with --assets rewrite is disabled because asset extensions and references change. Use a separate output directory.")
    dst_root = src if in_place else (output or unique_output_path(src.with_name(src.name + "-compressed")))
    if output is not None and not in_place and dst_root.exists() and any(dst_root.iterdir()):
        raise ToolError("OUTPUT_EXISTS", f"Output directory is not empty: {dst_root}")
    if not cfg.dry_run:
        dst_root.mkdir(parents=True, exist_ok=True)

    all_files = [p for p in src.rglob("*") if p.is_file()]
    totals.files_seen += len(all_files)
    image_files = [p for p in all_files if p.suffix.lower() in IMAGE_EXTS]
    text_files = [p for p in all_files if p.suffix.lower() in TEXT_EXTS]
    other_files = [p for p in all_files if p not in image_files and p not in text_files]

    details: list[dict] = []
    mapping: dict[str, str] = {}

    if cfg.assets == "rewrite":
        def image_job(p: Path):
            rel = p.relative_to(src)
            raw = p.read_bytes()
            r = compress_blob(raw, EXT_TO_MIME.get(p.suffix.lower()), cfg)
            return p, rel, raw, r

        with concurrent.futures.ThreadPoolExecutor(max_workers=cfg.workers) as ex:
            futures = [ex.submit(image_job, p) for p in image_files]
            for fut in concurrent.futures.as_completed(futures):
                p, rel, raw, r = fut.result()
                totals.images_seen += 1
                totals.bytes_before += len(raw)
                totals.bytes_after += len(r.data)
                new_rel = rel.with_suffix(r.ext) if r.changed else rel
                mapping[rel.as_posix()] = new_rel.as_posix()
                out = dst_root / new_rel
                if r.changed:
                    totals.images_changed += 1
                    if not cfg.dry_run:
                        out.parent.mkdir(parents=True, exist_ok=True)
                        out.write_bytes(r.data)
                else:
                    totals.images_kept += 1
                    if not cfg.dry_run:
                        out.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(p, out)
                if r.error:
                    totals.warnings += 1
                totals.files_written += 1
                details.append({
                    "input": str(p), "output": str(out), "changed": r.changed,
                    "source_mime": r.source_mime, "output_mime": r.mime,
                    "bytes_before": len(raw), "bytes_after": len(r.data),
                    "animated": r.animated, "encoder": r.encoder, "reason": r.reason,
                    **({"error": r.error} if r.error else {}),
                })
    else:
        for p in image_files:
            rel = p.relative_to(src)
            mapping[rel.as_posix()] = rel.as_posix()
            out = dst_root / rel
            raw_size = p.stat().st_size
            totals.bytes_before += raw_size
            totals.bytes_after += raw_size
            totals.images_seen += 1
            totals.images_kept += 1
            if not cfg.dry_run:
                out.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, out)
            totals.files_written += 1

    for p in text_files:
        rel = p.relative_to(src)
        out = dst_root / rel
        details.append(process_text_file(p, out, cfg, totals, mapping if cfg.assets == "rewrite" else None, rel))

    for p in other_files:
        rel = p.relative_to(src)
        out = dst_root / rel
        size = p.stat().st_size
        totals.bytes_before += size
        totals.bytes_after += size
        if not cfg.dry_run:
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, out)
        totals.files_written += 1

    return {"input": str(src), "output": str(dst_root), "type": "directory", "files": details}


def probe_path(path: Path) -> dict:
    if not path.exists():
        raise ToolError("INPUT_NOT_FOUND", f"Input does not exist: {path}")
    if path.is_file():
        if path.suffix.lower() in IMAGE_EXTS:
            raw = path.read_bytes()
            mime = sniff_mime(raw)
            anim = (mime == "image/webp" and webp_flags(raw)[0]) or (mime == "image/gif" and gif_frame_count(raw, which_any(["magick"])) > 1)
            return {"path": str(path), "type": "image", "mime": mime, "bytes": len(raw), "animated": bool(anim), "alpha": has_alpha(raw, mime)}
        text = safe_read_text(path)
        if text is None:
            return {"path": str(path), "type": "file", "bytes": path.stat().st_size, "supported": False}
        return {"path": str(path), "type": "text", "bytes": path.stat().st_size, "embedded_images": len(DATA_URL_RE.findall(text))}
    files = [p for p in path.rglob("*") if p.is_file()]
    text_files = [p for p in files if p.suffix.lower() in TEXT_EXTS]
    image_files = [p for p in files if p.suffix.lower() in IMAGE_EXTS]
    embedded = 0
    for p in text_files:
        t = safe_read_text(p)
        if t:
            embedded += len(DATA_URL_RE.findall(t))
    return {
        "path": str(path), "type": "directory", "files": len(files),
        "text_files": len(text_files), "image_assets": len(image_files),
        "embedded_images": embedded,
    }


def doctor() -> dict:
    magick = which_any(["magick"])
    ffmpeg = which_any(["ffmpeg"])
    ffprobe = which_any(["ffprobe"])
    convert_any = which_any(["convert-any"])
    encoders = []
    if ffmpeg:
        cp = run([ffmpeg, "-hide_banner", "-encoders"], timeout=30)
        text = cp.stdout.decode("utf-8", "ignore") + cp.stderr.decode("utf-8", "ignore")
        for enc in ("libaom-av1", "libwebp_anim", "libwebp"):
            if enc in text:
                encoders.append(enc)
    magick_avif = bool(magick and magick_supports_avif(magick))
    return {
        "version": VERSION,
        "python": sys.version.split()[0],
        "magick": magick,
        "ffmpeg": ffmpeg,
        "ffprobe": ffprobe,
        "convert_any": convert_any,
        "ffmpeg_encoders": encoders,
        "ready": bool((ffmpeg and "libaom-av1" in encoders) or magick_avif),
        "magick_avif": magick_avif,
        "notes": [
            "FFmpeg is preferred for AVIF and preserves alpha with a separate AV1 alpha stream.",
            "ImageMagick is used for GIF inspection/animation and as an AVIF fallback when its build supports AVIF.",
            "convert-any is optional and is only used as a decoder fallback for unusual inputs.",
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cyoa-compress", description="Local CYOA image compressor for LLM/tool use.")
    p.add_argument("command_or_input", nargs="?", help="Input path, or one of: compress, probe, doctor")
    p.add_argument("inputs", nargs="*")
    p.add_argument("-o", "--output", type=Path)
    p.add_argument("--in-place", action="store_true", help="Rewrite a text CYOA file in place. Disabled for project asset rewriting.")
    p.add_argument("--quality", type=int, default=60, help="Image quality 0..100, higher is better. Default: 60")
    p.add_argument("--cq", type=int, help="Compatibility quality in the browser compressor's 0..63 direction; lower is better. Overrides --quality.")
    p.add_argument("--workers", type=int, default=max(1, min(8, (os.cpu_count() or 2) // 2 or 1)))
    p.add_argument("--encoder", choices=["auto", "magick", "ffmpeg"], default="auto")
    p.add_argument("--assets", choices=["rewrite", "embedded"], default="rewrite", help="For directories, also convert local image assets and rewrite references, or only embedded data URLs.")
    p.add_argument("--gif", dest="gif_mode", choices=["webp", "keep"], default="webp")
    p.add_argument("--recompress-avif", action="store_true")
    p.add_argument("--min-savings-bytes", type=int, default=256)
    p.add_argument("--min-savings-percent", type=float, default=2.0)
    p.add_argument("--no-convert-any", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--details", action="store_true", help="Include settings and per-file decisions in JSON output.")
    p.add_argument("--pretty", action="store_true")
    p.add_argument("--version", action="version", version=VERSION)
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    first = args.command_or_input
    if not first:
        parser.print_help(sys.stderr)
        return 2

    if first == "doctor":
        print(json.dumps(doctor(), indent=2 if args.pretty else None, separators=None if args.pretty else (",", ":")))
        return 0

    if first == "probe":
        if not args.inputs:
            raise ToolError("INPUT_REQUIRED", "probe requires at least one input path")
        payload = {"version": VERSION, "results": [probe_path(Path(x).expanduser().resolve()) for x in args.inputs]}
        print(json.dumps(payload, indent=2 if args.pretty else None, separators=None if args.pretty else (",", ":")))
        return 0

    inputs = args.inputs if first == "compress" else [first, *args.inputs]
    if not inputs:
        raise ToolError("INPUT_REQUIRED", "compress requires at least one input path")
    if args.output and len(inputs) > 1 and not args.output.exists() and args.output.suffix:
        raise ToolError("OUTPUT_AMBIGUOUS", "With multiple inputs, --output must be a directory.")
    if not 0 <= args.quality <= 100:
        raise ToolError("BAD_QUALITY", "--quality must be between 0 and 100")
    if args.cq is not None and not 0 <= args.cq <= 63:
        raise ToolError("BAD_CQ", "--cq must be between 0 and 63")
    if args.workers < 1:
        raise ToolError("BAD_WORKERS", "--workers must be at least 1")

    quality = quality_from_cq(args.cq) if args.cq is not None else args.quality
    cfg = Config(
        quality=quality,
        workers=args.workers,
        encoder=args.encoder,
        assets=args.assets,
        gif_mode=args.gif_mode,
        recompress_avif=args.recompress_avif,
        min_savings_bytes=max(1, args.min_savings_bytes),
        min_savings_percent=max(0.0, args.min_savings_percent),
        dry_run=args.dry_run,
        pretty=args.pretty,
        use_convert_any=not args.no_convert_any,
    )
    totals = Totals()
    details = []
    output_root = args.output.resolve() if args.output else None

    for raw_input in inputs:
        src = Path(raw_input).expanduser().resolve()
        if not src.exists():
            raise ToolError("INPUT_NOT_FOUND", f"Input does not exist: {src}")
        out = output_root
        if output_root and len(inputs) > 1:
            out = output_root / (src.name + ("-compressed" if src.is_dir() else ""))
        if src.is_dir():
            details.append(process_directory(src, out, cfg, totals, args.in_place))
        else:
            details.append(process_single_file(src, out, cfg, totals, args.in_place))

    payload = {
        "ok": True,
        "version": VERSION,
        "totals": compact_totals(totals),
        "results": [compact_result(x) for x in details],
    }
    if args.details:
        payload["settings"] = {
            "quality": cfg.quality,
            "cq_compat": args.cq,
            "workers": cfg.workers,
            "encoder": cfg.encoder,
            "assets": cfg.assets,
            "gif": cfg.gif_mode,
            "recompress_avif": cfg.recompress_avif,
            "dry_run": cfg.dry_run,
        }
        payload["results"] = details
    print(json.dumps(payload, indent=2 if args.pretty else None, separators=None if args.pretty else (",", ":")))
    return 0


def cli_main(argv: list[str] | None = None) -> int:
    try:
        return main(argv)
    except ToolError as e:
        print(json.dumps({"ok": False, "error": {"code": e.code, "message": str(e)}}), file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print(json.dumps({"ok": False, "error": {"code": "INTERRUPTED", "message": "Interrupted"}}), file=sys.stderr)
        return 130
    except Exception as e:
        print(json.dumps({"ok": False, "error": {"code": "UNEXPECTED", "message": str(e)}}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(cli_main())
