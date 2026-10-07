from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import zipfile
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]

FULL_EXCLUDE_PARTS = {
    ".git", ".github", ".pytest_cache", ".mypy_cache", ".ruff_cache", "__pycache__",
    "tests", "cli_tests", "compression_tests", "online_tests", "dist", "build",
}
FULL_EXCLUDE_SUFFIXES = {".pyc", ".pyo"}
FULL_EXCLUDE_NAMES = {"run-tests", "run-compression-tests", "run-upstream-parity-tests"}
FULL_EXECUTABLES = {"iccplus-local", "cyoa-compress", "install.sh"}

VIEWER_CODE = [
    "iccplus_tools/__init__.py",
    "iccplus_tools/version.py",
    "iccplus_tools/model.py",
    "iccplus_tools/requirements.py",
    "iccplus_tools/simulator.py",
    "iccplus_tools/scenario.py",
    "iccplus_tools/expressions.py",
    "iccplus_tools/js_compat.py",
    "iccplus_tools/build_string.py",
    "iccplus_tools/viewer_text.py",
    "iccplus_tools/viewer_cli.py",
]
VIEWER_DOCS = [
    "LICENSE", "VERSION", "SOURCE_NOTES.md", "COVERAGE.md", "VIEWER_TEST_README.md",
    "docs/COVERAGE.md", "docs/GAMEPLAY_RUNNER.md", "docs/PLAY_STRUCTURE.md",
    "docs/SESSION_PROTOCOL.md", "docs/TESTING.md", "docs/VISIBILITY_AND_HIDING.md",
    "docs/UPSTREAM_PARITY_AUDIT.md", "docs/EXTERNAL_UPSTREAM_VERIFICATION.md",
    "docs/cyoa/audit-rules.md", "docs/cyoa/guide/02-creator-and-viewer.md",
    "docs/cyoa/guide/11-balance-and-playtesting.md", "docs/cyoa/guide/17-local-testing.md",
    "docs/cyoa/guide/18-continuing-playtests.md", "docs/cyoa/prompts/blind-playtest.md",
    "skills/iccplus-viewer-test/SKILL.md",
]
VIEWER_FORBIDDEN_PREFIXES = (
    "iccplus_tools/editor.py", "iccplus_tools/generation.py", "iccplus_tools/build_pipeline.py",
    "iccplus_tools/operations.py", "iccplus_tools/phase_ops.py", "iccplus_tools/assets.py",
    "iccplus_tools/image_", "iccplus_tools/packaging.py", "iccplus_tools/style_templates.py",
    "iccplus_tools/visuals.py", "skills/iccplus-local/", "skills/cyoa-plan/",
    "skills/cyoa-develop/", "skills/cyoa-migrate/", "skills/cyoa-ship/",
)


def _version() -> str:
    return (ROOT / "VERSION").read_text(encoding="utf-8").strip()


def _iter_full_files() -> Iterable[Path]:
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if any(part in FULL_EXCLUDE_PARTS for part in rel.parts):
            continue
        if path.suffix in FULL_EXCLUDE_SUFFIXES:
            continue
        if rel.as_posix() in FULL_EXCLUDE_NAMES:
            continue
        yield rel


def _zip_write(
    zf: zipfile.ZipFile,
    source: Path,
    arcname: str,
    *,
    executable: bool | None = None,
) -> None:
    data = source.read_bytes()
    info = zipfile.ZipInfo(arcname)
    info.date_time = (2020, 1, 1, 0, 0, 0)
    info.compress_type = zipfile.ZIP_DEFLATED
    is_executable = bool(source.stat().st_mode & 0o111) if executable is None else executable
    info.external_attr = (0o755 if is_executable else 0o644) << 16
    zf.writestr(info, data)


def _manifest(kind: str, source_ref: str, files: list[str]) -> bytes:
    value = {
        "distribution": kind,
        "version": _version(),
        "source_ref": source_ref,
        "files": files,
    }
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _write_generated(zf: zipfile.ZipFile, arcname: str, data: bytes, *, executable: bool = False) -> None:
    info = zipfile.ZipInfo(arcname)
    info.date_time = (2020, 1, 1, 0, 0, 0)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = (0o755 if executable else 0o644) << 16
    zf.writestr(info, data)


def build_full(out_dir: Path, source_ref: str) -> Path:
    version = _version()
    dest = out_dir / f"iccplus-local-full-{version}.zip"
    files = [str(x).replace("\\", "/") for x in _iter_full_files()]
    prefix = f"iccplus-local-full-{version}"
    with zipfile.ZipFile(dest, "w") as zf:
        for rel in _iter_full_files():
            rel_text = str(rel).replace("\\", "/")
            _zip_write(
                zf,
                ROOT / rel,
                f"{prefix}/{rel_text}",
                executable=True if rel_text in FULL_EXECUTABLES else None,
            )
        _write_generated(zf, f"{prefix}/RELEASE_MANIFEST.json", _manifest("full", source_ref, files))
    return dest


def _viewer_pyproject() -> bytes:
    version = _version()
    return f'''[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "iccplus-viewer-test"
version = "{version}"
description = "Minimal ICC Plus Viewer/runtime testing environment"
requires-python = ">=3.11"
license = {{text = "MIT"}}
dependencies = []

[project.scripts]
iccplus-viewer-test = "iccplus_tools.viewer_cli:main"

[tool.setuptools.packages.find]
where = ["."]
include = ["iccplus_tools*"]
'''.encode("utf-8")


def _viewer_init() -> bytes:
    return b'''from .model import Entity, ProjectIndex
from .requirements import RequirementEngine, RequirementTrace
from .scenario import run_scenario
from .simulator import ChoiceStatus, Event, RuntimeState, Simulator, explore, project_fingerprint
from .version import __version__

__all__ = [
    "ChoiceStatus", "Entity", "Event", "ProjectIndex", "RequirementEngine", "RequirementTrace",
    "RuntimeState", "Simulator", "__version__", "explore", "project_fingerprint", "run_scenario",
]
'''


def build_viewer(out_dir: Path, source_ref: str) -> Path:
    version = _version()
    dest = out_dir / f"iccplus-viewer-test-{version}.zip"
    prefix = f"iccplus-viewer-test-{version}"
    copied: list[str] = []
    with zipfile.ZipFile(dest, "w") as zf:
        for rel_text in VIEWER_CODE + VIEWER_DOCS:
            if rel_text == "iccplus_tools/__init__.py":
                _write_generated(zf, f"{prefix}/{rel_text}", _viewer_init())
            else:
                path = ROOT / rel_text
                if not path.is_file():
                    raise FileNotFoundError(f"viewer distribution input is missing: {rel_text}")
                _zip_write(zf, path, f"{prefix}/{rel_text}")
            copied.append(rel_text)
        _write_generated(zf, f"{prefix}/pyproject.toml", _viewer_pyproject())
        copied.append("pyproject.toml")
        _write_generated(zf, f"{prefix}/RELEASE_MANIFEST.json", _manifest("viewer-test", source_ref, sorted(copied)))
    _verify_viewer_archive(dest)
    return dest


def _verify_viewer_archive(path: Path) -> None:
    with zipfile.ZipFile(path) as zf:
        names = [n.split("/", 1)[1] for n in zf.namelist() if "/" in n]
    for forbidden in VIEWER_FORBIDDEN_PREFIXES:
        if any(name.startswith(forbidden) for name in names):
            raise RuntimeError(f"viewer archive leaked authoring content: {forbidden}")
    required = {
        "iccplus_tools/simulator.py", "iccplus_tools/viewer_cli.py", "skills/iccplus-viewer-test/SKILL.md",
        "docs/GAMEPLAY_RUNNER.md", "docs/PLAY_STRUCTURE.md", "VIEWER_TEST_README.md",
    }
    missing = sorted(required.difference(names))
    if missing:
        raise RuntimeError(f"viewer archive missing required files: {missing}")


def checksums(paths: list[Path], out_dir: Path) -> Path:
    dest = out_dir / "SHA256SUMS.txt"
    lines = [f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}" for p in paths]
    dest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return dest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="release-dist")
    parser.add_argument("--source-ref", default="unknown")
    args = parser.parse_args()
    out = Path(args.output_dir)
    if not out.is_absolute():
        out = ROOT / out
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    full = build_full(out, args.source_ref)
    viewer = build_viewer(out, args.source_ref)
    sums = checksums([full, viewer], out)
    print(json.dumps({"full": str(full), "viewer": str(viewer), "checksums": str(sums)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
