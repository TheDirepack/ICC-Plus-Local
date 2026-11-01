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
    assert capabilities()['target']['icc_plus_version'] == ICCPLUS_VERSION
    assert capabilities()['target']['source_commit'] == ICCPLUS_COMMIT
    assert ICCPLUS_VERSION in capabilities()['build_system']['blank_source']



def test_all_live_discovery_and_build_targets_match_upstream_pin():
    from iccplus_tools.build_pipeline import TARGET_VERSION, TARGET_COMMIT
    from iccplus_tools.gui_parity import gui_parity_report
    from iccplus_tools.guides import guide

    assert (TARGET_VERSION, TARGET_COMMIT) == (ICCPLUS_VERSION, ICCPLUS_COMMIT)
    report = gui_parity_report()
    assert report['target'] == {'icc_plus_version': ICCPLUS_VERSION, 'source_commit': ICCPLUS_COMMIT}
    assert report['source_audit']['baseline_version'] == '2.10.7'
    assert report['source_audit']['baseline_source_commit'] != ICCPLUS_COMMIT
    assert ICCPLUS_VERSION in guide('typed-authoring')['goal']
    assert ICCPLUS_COMMIT in ' '.join(guide('parity')['rules'])


def test_active_documentation_tracks_pinned_target_and_discount_boundary():
    for path in ('COVERAGE.md', 'SOURCE_NOTES.md', 'docs/SOURCE_NOTES.md',
                 'docs/ICCPLUS_FIELD_REFERENCE.md', 'docs/SPARSE_RUNTIME_SERIALIZATION.md'):
        assert ICCPLUS_VERSION in (ROOT / path).read_text(), path
    coverage = (ROOT / 'COVERAGE.md').read_text()
    assert 'four or more' in coverage
    assert 'more than two sources' not in coverage


def test_manifest_tracks_pinned_source_and_exact_default_export():
    manifest = json.loads((ROOT / 'PACKAGE_MANIFEST.json').read_text())
    exported = default_export_text().encode('utf-8')
    assert manifest['tool_version'] == __version__
    assert manifest['target_icc_plus_version'] == ICCPLUS_VERSION
    assert manifest['target_source_commit'] == ICCPLUS_COMMIT
    assert manifest['local_regression']['default_export_bytes'] == len(exported)
    assert manifest['local_regression']['default_export_sha256'] == hashlib.sha256(exported).hexdigest(), hashlib.sha256(exported).hexdigest()
