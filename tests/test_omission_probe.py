from __future__ import annotations

import json

from iccplus_tools.omission_probe import main, omission_probe_cases, write_omission_probe_suite
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


def test_core_probe_cases_isolate_one_change_and_use_valid_controls() -> None:
    cases = omission_probe_cases(exhaustive=False)
    assert len(cases) >= 30
    ids = [case['id'] for case in cases]
    assert len(ids) == len(set(ids))
    assert 'private-filter-unsel-satur-one' in ids
    assert any(case_id.startswith('viewer-config-') for case_id in ids)
    assert 'row-privateMultiChoiceIsOn' in ids
    assert 'choice-privateMultiChoiceIsOn' in ids

    for case in cases:
        if case['category'] == 'remove-nulls-array-filtering':
            assert validate_complete(case['baseline'])['valid'] is False, case['id']
            assert validate_complete(case['candidate'])['valid'] is True, case['id']
        else:
            assert validate_complete(case['baseline'])['valid'] is True, case['id']
        assert _diff_count(case['baseline'], case['candidate']) == 1, case['id']

    array_cases = {case['id']: case for case in cases if case['id'].startswith('array-')}
    assert set(array_cases) == {'array-null-entry', 'array-empty-object-entry'}
    for case in array_cases.values():
        assert case['path'] == '/mdObjects/0'
        assert len(case['baseline']['mdObjects']) == 2
        assert case['candidate']['mdObjects'] == ['probe-md']


def test_exhaustive_probe_inventory_covers_unproven_style_fallbacks() -> None:
    cases = omission_probe_cases(exhaustive=True)
    ids = [case['id'] for case in cases]
    categories = {case['category'] for case in cases}

    assert len(cases) > 500
    assert len(ids) == len(set(ids))
    assert 'retained-global-styling-member' in categories
    assert 'private-style-member-fallback' in categories
    assert 'runtime-state-empty-build' in categories
    assert 'global-styling-unselFilterSatur' in ids
    assert 'private-choice-privateTextIsOn-objectTitle' in ids
    assert 'top-level-activated-empty-build' in ids

    for category in ('retained-global-styling-member', 'private-style-member-fallback', 'runtime-state-empty-build'):
        case = next(item for item in cases if item['category'] == category)
        assert validate_complete(case['baseline'])['valid'] is True, case['id']
        assert _diff_count(case['baseline'], case['candidate']) == 1, case['id']


def test_probe_suite_writes_manifest_pairs_and_results_ledger(tmp_path) -> None:
    sample = omission_probe_cases(exhaustive=False)[:5]
    manifest = write_omission_probe_suite(tmp_path, cases=sample)
    assert manifest['format_version'] == 2
    assert manifest['case_count'] == len(sample)
    assert manifest['case_count'] == len(manifest['cases'])
    assert manifest['target']['icc_plus_version'] == '2.10.7'
    assert sum(manifest['category_counts'].values()) == manifest['case_count']
    disk_manifest = json.loads((tmp_path / 'manifest.json').read_text(encoding='utf-8'))
    results = json.loads((tmp_path / 'results.json').read_text(encoding='utf-8'))
    assert disk_manifest['case_count'] == manifest['case_count']
    assert len(results['results']) == manifest['case_count']
    assert {item['status'] for item in results['results']} == {'untested'}
    assert (tmp_path / 'README.md').is_file()

    for case in manifest['cases']:
        baseline = tmp_path / case['baseline_file']
        candidate = tmp_path / case['candidate_file']
        assert baseline.is_file(), case['id']
        assert candidate.is_file(), case['id']
        assert json.loads(baseline.read_text(encoding='utf-8')) != json.loads(candidate.read_text(encoding='utf-8'))


def test_probe_cli_can_filter_to_one_core_category(tmp_path) -> None:
    out = tmp_path / 'filtered'
    assert main([
        '--core-only',
        '--category', 'known-private-default-mismatch',
        '-o', str(out),
    ]) == 0
    manifest = json.loads((out / 'manifest.json').read_text(encoding='utf-8'))
    assert manifest['case_count'] == 1
    assert manifest['cases'][0]['id'] == 'private-filter-unsel-satur-one'
    assert (out / 'private-filter-unsel-satur-one' / 'baseline.json').is_file()
    assert (out / 'private-filter-unsel-satur-one' / 'candidate.json').is_file()
