from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CURRENT_DOCS = [
    ROOT / "README.md",
    ROOT / "skills/iccplus-local/SKILL.md",
    ROOT / "START_HERE.md",
    ROOT / "docs/CLI_REFERENCE.md",
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Synchronize ICC Plus Local release version metadata.")
    parser.add_argument("version", help="Version text to use exactly as supplied.")
    args = parser.parse_args()
    set_version(args.version)
    print(args.version.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
