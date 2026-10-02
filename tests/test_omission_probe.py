from __future__ import annotations

import json

from iccplus_tools.omission_probe import omission_probe_cases, write_omission_probe_suite
from iccplus_tools.validation import validate_complete


def _diff_count(a, b) -> int:
    if type(a) is not type(b):
        return 1
    if isinstance(a, dict):
        keys = set(a) | set(b)
        return sum(1 if key not in a or key not in b else _diff_count(a[key], b[key]) for key in keys)
    if isinstance(a, list):
        if len(a) != len(b):
            return 1
        return sum(_diff_count(x, y) for x, y in zip(a, b))
    return 0 if a == b else 1


def test_probe_cases_are_complete_and_isolate_one_change() -> None:
    cases = omission_probe_cases()
    assert len(cases) >= 30
    ids = [case['id'] for case in cases]
    assert len(ids) == len(set(ids))
    assert 'private-filter-unsel-satur-one' in ids
    assert any(case_id.startswith('viewer-config-') for case_id in ids)
    assert 'row-privateMultiChoiceIsOn' in ids
    assert 'choice-privateMultiChoiceIsOn' in ids

    for case in cases:
        assert validate_complete(case['baseline'])['valid'] is True, case['id']
        # Candidates intentionally omit optional/native fields under test, so
        # Creator completeness is not required after the omission.
        assert _diff_count(case['baseline'], case['candidate']) == 1, case['id']


def test_probe_suite_writes_manifest_and_pairs(tmp_path) -> None:
    manifest = write_omission_probe_suite(tmp_path)
    assert manifest['case_count'] == len(manifest['cases'])
    assert manifest['target']['icc_plus_version'] == '2.10.7'
    disk_manifest = json.loads((tmp_path / 'manifest.json').read_text(encoding='utf-8'))
    assert disk_manifest['case_count'] == manifest['case_count']
    assert (tmp_path / 'README.md').is_file()

    for case in manifest['cases']:
        baseline = tmp_path / case['baseline_file']
        candidate = tmp_path / case['candidate_file']
        assert baseline.is_file(), case['id']
        assert candidate.is_file(), case['id']
        assert json.loads(baseline.read_text(encoding='utf-8')) != json.loads(candidate.read_text(encoding='utf-8'))
