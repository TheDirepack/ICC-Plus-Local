from __future__ import annotations

import tomllib
import hashlib
import json
from pathlib import Path

from iccplus_tools.capabilities import capabilities
from iccplus_tools.version import __version__
from iccplus_tools.upstream_2106 import ICCPLUS_VERSION, ICCPLUS_COMMIT, default_export_text

ROOT = Path(__file__).resolve().parents[1]


def test_release_version_is_consistent_across_package_metadata_and_docs():
    assert (ROOT / 'VERSION').read_text().strip() == __version__
    pyproject = tomllib.loads((ROOT / 'pyproject.toml').read_text())
    assert pyproject['project']['version'] == __version__
    assert capabilities()['tool_version'] == __version__


def test_manifest_tracks_pinned_source_and_exact_default_export():
    manifest = json.loads((ROOT / 'PACKAGE_MANIFEST.json').read_text())
    exported = default_export_text().encode('utf-8')
    assert manifest['tool_version'] == __version__
    assert manifest['target_icc_plus_version'] == ICCPLUS_VERSION
    assert manifest['target_source_commit'] == ICCPLUS_COMMIT
    assert manifest['local_regression']['default_export_bytes'] == len(exported)
    assert manifest['local_regression']['default_export_sha256'] == hashlib.sha256(exported).hexdigest()
