from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'verification' / 'scripts' / 'verify_returned_results.py'
TEMPLATE = ROOT / 'verification' / 'results_template' / 'official_results.json'


def _module():
    spec = importlib.util.spec_from_file_location('verify_returned_results', SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _data():
    return json.loads(TEMPLATE.read_text(encoding='utf-8'))


def _write(tmp_path: Path, data: dict) -> Path:
    path = tmp_path / 'results.json'
    path.write_text(json.dumps(data), encoding='utf-8')
    return path


def test_pending_template_is_valid_but_incomplete(tmp_path, capsys):
    mod = _module()
    data = _data()
    data['official_gui_url_or_build'] = 'official ICC Plus 2.10.6'
    data['browser'] = 'test browser'
    code = mod.main([str(_write(tmp_path, data))])
    report = json.loads(capsys.readouterr().out)
    assert code == 3
    assert report['schema_ok'] is True
    assert report['complete'] is False


def test_local_tool_observation_cannot_claim_pass(tmp_path, capsys):
    mod = _module()
    data = _data()
    data['official_gui_url_or_build'] = 'official ICC Plus 2.10.6'
    data['browser'] = 'test browser'
    item = data['runtime_results']['R01']
    item['status'] = 'pass'
    item['observation_source'] = 'local_tool'
    code = mod.main([str(_write(tmp_path, data)), '--allow-incomplete'])
    report = json.loads(capsys.readouterr().out)
    assert code == 1
    assert any('R01 may only be pass/fail' in issue for issue in report['issues'])


def test_fixture_hash_mismatch_is_rejected(tmp_path, capsys):
    mod = _module()
    data = _data()
    data['official_gui_url_or_build'] = 'official ICC Plus 2.10.6'
    data['browser'] = 'test browser'
    data['runtime_results']['R01']['fixture_sha256'] = '0' * 64
    code = mod.main([str(_write(tmp_path, data)), '--allow-incomplete'])
    report = json.loads(capsys.readouterr().out)
    assert code == 1
    assert any('R01.fixture_sha256' in issue for issue in report['issues'])


def test_pass_without_official_observation_is_rejected(tmp_path, capsys):
    mod = _module()
    data = _data()
    data['official_gui_url_or_build'] = 'official ICC Plus 2.10.6'
    data['browser'] = 'test browser'
    item = data['runtime_results']['R01']
    item['status'] = 'pass'
    item['observation_source'] = 'official_gui'
    item['observed'] = {}
    item['artifacts'] = []
    code = mod.main([str(_write(tmp_path, data)), '--allow-incomplete'])
    report = json.loads(capsys.readouterr().out)
    assert code == 1
    assert any('R01.observed.snapshot' in issue for issue in report['issues'])


def test_wrong_official_gui_version_is_rejected(tmp_path, capsys):
    mod = _module()
    data = _data()
    data['official_gui_version'] = '2.10.5'
    data['official_gui_url_or_build'] = 'official ICC Plus'
    data['browser'] = 'test browser'
    code = mod.main([str(_write(tmp_path, data)), '--allow-incomplete'])
    report = json.loads(capsys.readouterr().out)
    assert code == 1
    assert any('official_gui_version' in issue for issue in report['issues'])


def _official_metadata(data: dict) -> None:
    data['official_gui_url_or_build'] = 'official ICC Plus 2.10.6'
    data['browser'] = 'test browser'
    data['finished_at'] = '2026-09-19T23:59:00+00:00'


def test_runtime_simulator_only_pass_is_rejected(tmp_path, capsys):
    mod = _module()
    data = _data(); _official_metadata(data)
    item = data['runtime_results']['R01']
    item['status'] = 'pass'
    item['observation_source'] = 'official_gui'
    item['observed'] = {'simulator_status': 'pass'}
    code = mod.main([str(_write(tmp_path, data)), '--allow-incomplete'])
    report = json.loads(capsys.readouterr().out)
    assert code == 1
    assert any('R01.observed.action_observations' in issue for issue in report['issues'])
    assert any('R01.observed.snapshot' in issue for issue in report['issues'])


def test_runtime_official_snapshot_mismatch_is_rejected(tmp_path, capsys):
    mod = _module()
    data = _data(); _official_metadata(data)
    item = data['runtime_results']['R01']
    item['status'] = 'pass'
    item['observation_source'] = 'official_gui'
    item['observed'] = {
        'action_observations': [{'step': 1, 'snapshot': {'entities': {'t01__a': {'active': False}, 't01__target': {'active': False}}, 'rows': {'t01__r': {'currentChoices': 1}}, 'build_string': 't01__a'}}],
        'snapshot': {'entities': {'t01__a': {'active': False}}},
    }
    code = mod.main([str(_write(tmp_path, data)), '--allow-incomplete'])
    report = json.loads(capsys.readouterr().out)
    assert code == 1
    assert any('R01.observed runtime mismatch' in issue for issue in report['issues'])


def test_runtime_official_snapshot_subset_can_satisfy_case(tmp_path, capsys):
    mod = _module()
    data = _data(); _official_metadata(data)
    item = data['runtime_results']['R01']
    item['status'] = 'pass'
    item['observation_source'] = 'official_gui'
    item['observed'] = {
        'action_observations': [{'step': 1, 'snapshot': {'entities': {'t01__a': {'active': True}, 't01__target': {'active': False}}, 'rows': {'t01__r': {'currentChoices': 1}}, 'build_string': 't01__a'}}],
        'snapshot': {'entities': {'t01__a': {'active': True}}},
    }
    code = mod.main([str(_write(tmp_path, data)), '--allow-incomplete'])
    report = json.loads(capsys.readouterr().out)
    assert code == 0
    assert not any('runtime_results.R01.' in issue for issue in report['issues'])


def test_incomplete_creator_pass_is_rejected(tmp_path, capsys):
    mod = _module()
    data = _data(); _official_metadata(data)
    artifact = tmp_path / 'returned_artifacts' / 'c02.json'
    artifact.parent.mkdir(parents=True)
    artifact.write_text('{}', encoding='utf-8')
    item = data['creator_results']['C02']
    item['status'] = 'pass'
    item['observation_source'] = 'official_gui'
    item['artifacts'] = ['returned_artifacts/c02.json']
    item['observed'] = {
        'completed_steps': [1, 2],
        'checks': [
            {'step': 1, 'status': 'pass', 'evidence': 'created nested entities'},
            {'step': 2, 'status': 'pass', 'evidence': 'attempted reorder'},
        ],
    }
    code = mod.main([str(_write(tmp_path, data)), '--allow-incomplete'])
    report = json.loads(capsys.readouterr().out)
    assert code == 1
    assert any('C02.observed.completed_steps' in issue for issue in report['issues'])
    assert any('C02.observed.checks does not cover every prescribed step' in issue for issue in report['issues'])


def test_claimed_artifact_must_exist(tmp_path, capsys):
    mod = _module()
    data = _data(); _official_metadata(data)
    item = data['creator_results']['C01']
    item['status'] = 'pass'
    item['observation_source'] = 'official_gui'
    item['artifacts'] = ['returned_artifacts/missing.json']
    item['observed'] = {
        'completed_steps': [1, 2, 3, 4],
        'checks': [
            {'step': 1, 'status': 'pass', 'evidence': 'loaded'},
            {'step': 2, 'status': 'pass', 'evidence': 'no edits'},
            {'step': 3, 'status': 'pass', 'artifact': 'returned_artifacts/missing.json'},
            {'step': 4, 'status': 'pass', 'evidence': 'recorded normalization'},
        ],
    }
    code = mod.main([str(_write(tmp_path, data)), '--allow-incomplete'])
    report = json.loads(capsys.readouterr().out)
    assert code == 1
    assert any('missing from the returned bundle' in issue for issue in report['issues'])


def test_zip_bundle_checks_declared_artifact_presence(tmp_path, capsys):
    import zipfile
    mod = _module()
    data = _data(); _official_metadata(data)
    item = data['creator_results']['C01']
    item['status'] = 'pass'
    item['observation_source'] = 'official_gui'
    item['artifacts'] = ['returned_artifacts/c01.json']
    item['observed'] = {
        'completed_steps': [1, 2, 3, 4],
        'checks': [
            {'step': 1, 'status': 'pass', 'evidence': 'loaded'},
            {'step': 2, 'status': 'pass', 'evidence': 'no edits'},
            {'step': 3, 'status': 'pass', 'artifact': 'returned_artifacts/c01.json'},
            {'step': 4, 'status': 'pass', 'evidence': 'normalization recorded'},
        ],
    }
    archive = tmp_path / 'results.zip'
    with zipfile.ZipFile(archive, 'w') as zf:
        zf.writestr('run/official_results.json', json.dumps(data))
        zf.writestr('run/returned_artifacts/c01.json', '{}')
    code = mod.main([str(archive), '--allow-incomplete'])
    report = json.loads(capsys.readouterr().out)
    assert code == 0
    assert report['bundle_kind'] == 'zip'
