import base64
import json
import os
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
from iccplus_tools import assets as cc
from iccplus_tools.version import __version__


def rgba_png(width=128, height=128):
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        for x in range(width):
            raw.extend(((x * 2) & 255, (y * 2) & 255, (x + y) & 255, 128 if (x + y) % 3 else 255))
    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xffffffff)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + chunk(b"IEND", b"")
    )


class CyoaCompressTests(unittest.TestCase):
    def test_quality_mapping(self):
        self.assertEqual(cc.quality_from_cq(0), 100)
        self.assertEqual(cc.quality_from_cq(63), 1)
        self.assertGreater(cc.quality_from_cq(20), cc.quality_from_cq(40))

    def test_png_detection_and_alpha(self):
        data = rgba_png(16, 16)
        self.assertEqual(cc.sniff_mime(data), "image/png")
        self.assertTrue(cc.png_has_alpha(data))


    def test_unique_output_path(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            first = root / "project-compressed"
            first.mkdir()
            self.assertEqual(cc.unique_output_path(first), root / "project-compressed-2")

    def test_default_json_is_compact(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "project.json"
            src.write_text("{}", encoding="utf-8")
            cp = subprocess.run(
                [sys.executable, "-m", "iccplus_tools.assets", str(src)],
                capture_output=True, text=True, check=True,
            )
            payload = json.loads(cp.stdout)
            self.assertTrue(payload["ok"])
            self.assertNotIn("settings", payload)
            self.assertEqual(set(payload["results"][0]), {"input", "output", "changed"})

            cp = subprocess.run(
                [sys.executable, "-m", "iccplus_tools.assets", str(src), "--details"],
                capture_output=True, text=True, check=True,
            )
            detailed = json.loads(cp.stdout)
            self.assertIn("settings", detailed)
            self.assertIn("bytes_before", detailed["results"][0])

    def test_reference_rewrite(self):
        text = '<img src="images/a.png"><style>x{background:url(\'images/a.png\')}</style>'
        out, count = cc.rewrite_asset_refs(text, Path("index.html"), {"images/a.png": "images/a.avif"})
        self.assertEqual(count, 2)
        self.assertIn("images/a.avif", out)
        self.assertNotIn("images/a.png", out)

    @unittest.skipUnless(os.environ.get("ICCPLUS_RUN_ENCODER_TESTS") == "1" and cc.which_any(["ffmpeg"]), "set ICCPLUS_RUN_ENCODER_TESTS=1 for encoder integration test")
    def test_embedded_alpha_png_to_avif(self):
        png = rgba_png()
        text = json.dumps({"image": "data:image/png;base64," + base64.b64encode(png).decode()})
        cfg = cc.Config(quality=60, workers=1)
        totals = cc.Totals()
        out, detail = cc.compress_embedded_text(text, cfg, totals)
        obj = json.loads(out)
        self.assertTrue(obj["image"].startswith("data:image/avif;base64,"))
        avif = base64.b64decode(obj["image"].split(",", 1)[1])
        self.assertEqual(cc.sniff_mime(avif), "image/avif")
        with tempfile.NamedTemporaryFile(suffix=".avif") as f:
            f.write(avif); f.flush()
            probe = subprocess.run([
                "ffprobe", "-v", "error", "-show_entries", "stream=pix_fmt", "-of", "json", f.name
            ], capture_output=True, text=True, check=True)
        streams = json.loads(probe.stdout)["streams"]
        self.assertGreaterEqual(len(streams), 2)
        self.assertEqual(streams[1]["pix_fmt"], "gray")
        self.assertTrue(detail[0]["changed"])

    @unittest.skipUnless(os.environ.get("ICCPLUS_RUN_ENCODER_TESTS") == "1" and cc.which_any(["ffmpeg"]), "set ICCPLUS_RUN_ENCODER_TESTS=1 for encoder integration test")
    def test_project_asset_rewrite(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "proj"
            out = Path(td) / "out"
            (root / "images").mkdir(parents=True)
            (root / "images" / "a.png").write_bytes(rgba_png(256, 256))
            (root / "index.html").write_text('<img src="images/a.png">', encoding="utf-8")
            totals = cc.Totals()
            cfg = cc.Config(quality=60, workers=1)
            result = cc.process_directory(root, out, cfg, totals, False)
            html = (out / "index.html").read_text(encoding="utf-8")
            self.assertIn("images/a.avif", html)
            self.assertTrue((out / "images" / "a.avif").exists())
            self.assertGreaterEqual(totals.references_rewritten, 1)
            self.assertEqual(result["output"], str(out))


def run_main_cli(*args: str, stdin: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, '-m', 'iccplus_tools', *args],
        cwd=ROOT, input=stdin, text=True, capture_output=True, check=False,
    )


class IntegratedAssetCliTests(unittest.TestCase):
    def test_asset_probe_and_doctor(self):
        doctor = run_main_cli('doctor')
        self.assertEqual(doctor.returncode, 0, doctor.stderr)
        value = json.loads(doctor.stdout)
        self.assertEqual(value['tool_version'], __version__)
        self.assertIn('image_compression', value)
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / 'a.png'
            image.write_bytes(rgba_png(16, 16))
            probe = run_main_cli('asset-probe', str(image))
            self.assertEqual(probe.returncode, 0, probe.stderr)
            info = json.loads(probe.stdout)['results'][0]
            self.assertEqual(info['mime'], 'image/png')
            self.assertTrue(info['alpha'])

    @unittest.skipUnless(os.environ.get('ICCPLUS_RUN_ENCODER_TESTS') == '1' and cc.which_any(['ffmpeg']), 'set ICCPLUS_RUN_ENCODER_TESTS=1 for encoder integration test')
    def test_compress_integrated_command_rewrites_project_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'proj'
            out = Path(tmp) / 'out'
            (root / 'images').mkdir(parents=True)
            (root / 'images' / 'a.png').write_bytes(rgba_png(256, 256))
            (root / 'index.html').write_text('<img src="images/a.png">', encoding='utf-8')
            result = run_main_cli('compress', str(root), '-o', str(out), '--workers', '1')
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload['ok'])
            html = (out / 'index.html').read_text(encoding='utf-8')
            if payload['totals']['changed']:
                self.assertIn('images/a.avif', html)
                self.assertTrue((out / 'images' / 'a.avif').exists())
            else:
                self.assertIn('images/a.png', html)
                self.assertTrue((out / 'images' / 'a.png').exists())


if __name__ == "__main__":
    unittest.main()
