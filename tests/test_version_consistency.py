from __future__ import annotations

import tomllib
from pathlib import Path

from iccplus_tools.capabilities import capabilities
from iccplus_tools.version import __version__

ROOT = Path(__file__).resolve().parents[1]


def test_release_version_is_consistent_across_package_metadata_and_docs():
    assert (ROOT / 'VERSION').read_text().strip() == __version__
    pyproject = tomllib.loads((ROOT / 'pyproject.toml').read_text())
    assert pyproject['project']['version'] == __version__
    assert capabilities()['tool_version'] == __version__
    readme_head = (ROOT / 'README.md').read_text()[:1000]
    assert f'Version {__version__}' in readme_head
    notes = (ROOT / 'RELEASE_NOTES.md').read_text()[:500]
    assert f'## {__version__}' in notes
