from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CURRENT_DOCS = [
    ROOT / "README.md",
    ROOT / "skills/iccplus-local/SKILL.md",
    ROOT / "START_HERE.md",
    ROOT / "docs/CLI_REFERENCE.md",
    ROOT / "docs/PACKAGE_README.md",
    ROOT / "docs/README.md",
    ROOT / "docs/PLAY_STRUCTURE.md",
    ROOT / "skills/cyoa-ship/SKILL.md",
]


def _replace_once(path: Path, pattern: str, replacement: str) -> None:
    text = path.read_text(encoding="utf-8")
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE)
    if count != 1:
        raise RuntimeError(f"could not update version marker in {path.relative_to(ROOT)}")
    path.write_text(updated, encoding="utf-8")


def set_version(version: str) -> None:
    version = version.strip()
    if not version:
        raise ValueError("version must not be empty")
    if "\n" in version or "\r" in version:
        raise ValueError("version must be one line")

    old = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    (ROOT / "VERSION").write_text(version + "\n", encoding="utf-8")

    _replace_once(
        ROOT / "iccplus_tools/version.py",
        r'^__version__\s*=\s*["\'][^"\']+["\']\s*$',
        f'__version__ = "{version}"',
    )
    _replace_once(
        ROOT / "pyproject.toml",
        r'(?m)^version\s*=\s*"[^"]+"\s*$',
        f'version = "{version}"',
    )

    if old and old != version:
        for path in CURRENT_DOCS:
            text = path.read_text(encoding="utf-8")
            if old in text:
                path.write_text(text.replace(old, version), encoding="utf-8")

        # Current release metadata is part of the version contract too.
        manifest_path = ROOT / "PACKAGE_MANIFEST.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("tool_version") != old:
            raise RuntimeError("package manifest version does not match VERSION")
        manifest["tool_version"] = version
        old_rc = re.search(r"rc\d+", old)
        new_rc = re.search(r"rc\d+", version)
        if old_rc and new_rc and isinstance(manifest.get("package"), str):
            manifest["package"] = manifest["package"].replace(old_rc.group(), new_rc.group(), 1)
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Synchronize ICC Plus Local release version metadata.")
    parser.add_argument("version", help="Version text to use exactly as supplied.")
    args = parser.parse_args()
    set_version(args.version)
    print(args.version.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
