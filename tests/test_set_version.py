from __future__ import annotations

from pathlib import Path

import scripts.set_version as versioning


def test_set_version_uses_supplied_text_as_authority(monkeypatch, tmp_path: Path):
    (tmp_path / "iccplus_tools").mkdir()
    (tmp_path / "skills/iccplus-local").mkdir(parents=True)
    (tmp_path / "docs").mkdir()

    (tmp_path / "VERSION").write_text("old-version\n", encoding="utf-8")
    (tmp_path / "iccplus_tools/version.py").write_text('__version__ = "old-version"\n', encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text('[project]\nversion = "old-version"\n', encoding="utf-8")

    docs = [
        tmp_path / "README.md",
        tmp_path / "skills/iccplus-local/SKILL.md",
        tmp_path / "START_HERE.md",
        tmp_path / "docs/CLI_REFERENCE.md",
    ]
    for doc in docs:
        doc.write_text("Current old-version text\n", encoding="utf-8")

    historical = tmp_path / "RELEASE_NOTES.md"
    historical.write_text("## old-version\nHistorical release\n", encoding="utf-8")

    monkeypatch.setattr(versioning, "ROOT", tmp_path)
    monkeypatch.setattr(versioning, "CURRENT_DOCS", docs)

    versioning.set_version("v2026.10-custom")

    assert (tmp_path / "VERSION").read_text(encoding="utf-8") == "v2026.10-custom\n"
    assert '__version__ = "v2026.10-custom"' in (tmp_path / "iccplus_tools/version.py").read_text(encoding="utf-8")
    assert 'version = "v2026.10-custom"' in (tmp_path / "pyproject.toml").read_text(encoding="utf-8")
    assert all("v2026.10-custom" in doc.read_text(encoding="utf-8") for doc in docs)
    assert historical.read_text(encoding="utf-8").startswith("## old-version")
