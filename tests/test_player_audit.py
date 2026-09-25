from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from iccplus_tools.simulator import Simulator


def audit_project() -> dict:
    return {
        'version': '2.10.6',
        'styling': {'reqFilterVisibleIsOn': True},
        'pointTypes': [
            {'id': 'budget', 'name': 'Budget', 'startingSum': 10, 'belowZeroNotAllowed': True},
        ],
        'rows': [
            {
                'id': 'start', 'title': 'Start', 'titleText': 'Choose a key.', 'allowedChoices': 0, 'requireds': [],
                'objects': [
                    {
                        'id': 'key', 'title': 'Key', 'text': 'Unlocks the next section.', 'requireds': [], 'addons': [],
                        'scores': [{'idx': 'key_cost', 'id': 'budget', 'value': 3, 'requireds': [], 'showScore': True}],
                    },
                    {
                        'id': 'too_expensive', 'title': 'Too expensive', 'text': 'Visible but unaffordable.', 'requireds': [], 'addons': [],
                        'scores': [{'idx': 'big_cost', 'id': 'budget', 'value': 11, 'requireds': [], 'showScore': True}],
                    },
                ],
            },
            {
                'id': 'unlocked', 'title': 'Unlocked', 'titleText': 'Visible after Key.', 'allowedChoices': 0,
                'requireds': [{'id': '', 'type': 'id', 'required': True, 'reqId': 'key', 'requireds': []}],
                'objects': [
                    {
                        'id': 'cheap', 'title': 'Cheap', 'text': 'Costs two.', 'requireds': [], 'addons': [],
                        'scores': [{'idx': 'cheap_cost', 'id': 'budget', 'value': 2, 'requireds': [], 'showScore': True}],
                    },
                    {
                        'id': 'six_cost', 'title': 'Six cost', 'text': 'Affordable at seven, not at five.', 'requireds': [], 'addons': [],
                        'scores': [{'idx': 'six_cost_score', 'id': 'budget', 'value': 6, 'requireds': [], 'showScore': True}],
                    },
                ],
            },
            {
                'id': 'secret_row', 'title': 'SECRET ROW', 'titleText': 'SECRET DESCRIPTION', 'allowedChoices': 0,
                'requireds': [{'id': '', 'type': 'id', 'required': True, 'reqId': 'never_visible_gate', 'requireds': []}],
                'objects': [
                    {'id': 'secret_choice', 'title': 'SECRET CHOICE', 'text': 'SECRET TEXT', 'requireds': [], 'scores': [], 'addons': []},
                ],
            },
        ],
    }


def point_value(view: dict, ident: str) -> float:
    return next(p['value'] for p in view['points'] if p['id'] == ident)


def choice(view: dict, ident: str) -> dict:
    return next(c for row in view['rows'] for c in row['choices'] if c['id'] == ident)


def test_player_view_is_progressive_audit_surface():
    sim = Simulator(audit_project())

    initial = sim.player_view(verbose=True)
    assert point_value(initial, 'budget') == 10
    assert set(initial['available_choice_ids']) == {'key'}
    assert choice(initial, 'key')['can_select'] is True
    assert choice(initial, 'too_expensive')['can_select'] is False
    assert 'points.below_zero_not_allowed' in {e['code'] for e in choice(initial, 'too_expensive')['selection_errors']}
    raw = json.dumps(initial)
    assert 'SECRET ROW' not in raw
    assert 'SECRET CHOICE' not in raw
    assert 'secret_choice' not in raw

    assert sim.select('key').ok is True
    after_key = sim.player_view(verbose=True)
    assert point_value(after_key, 'budget') == 7
    assert 'key' in after_key['selected_ids']
    assert 'key' in after_key['deselectable_choice_ids']
    assert set(after_key['available_choice_ids']) == {'cheap', 'six_cost'}
    assert {row['id'] for row in after_key['rows']} == {'start', 'unlocked'}

    assert sim.select('cheap').ok is True
    after_cheap = sim.player_view(verbose=True)
    assert point_value(after_cheap, 'budget') == 5
    assert set(after_cheap['selected_ids']) == {'key', 'cheap'}
    assert 'six_cost' not in after_cheap['available_choice_ids']
    assert choice(after_cheap, 'six_cost')['can_select'] is False


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, '-m', 'iccplus_tools', *args],
        text=True,
        capture_output=True,
        cwd=Path(__file__).resolve().parents[1],
        env={**__import__('os').environ, 'PYTHONPATH': str(Path(__file__).resolve().parents[1])},
    )


def test_play_is_private_progressive_simulator_for_llm_audits(tmp_path: Path):
    project_path = tmp_path / 'project.json'
    state_path = tmp_path / 'run.state.json'
    project_path.write_text(json.dumps(audit_project()), encoding='utf-8')

    initial = run_cli('play', str(project_path), '--state', str(state_path), '--compact')
    assert initial.returncode == 0, initial.stderr
    value = json.loads(initial.stdout)
    assert value['mode'] == 'player_safe_play'
    assert value['view']['available_choice_ids'] == ['key']
    assert point_value(value['view'], 'budget') == 10
    assert 'runtime_state' not in value
    assert 'snapshot' not in value
    assert 'SECRET' not in initial.stdout

    selected = run_cli('play', str(project_path), '--state', str(state_path), '--select', 'key', '--compact')
    assert selected.returncode == 0, selected.stderr
    value = json.loads(selected.stdout)
    assert point_value(value['view'], 'budget') == 7
    assert set(value['view']['available_choice_ids']) == {'cheap', 'six_cost'}
    assert 'key' in value['view']['selected_ids']

    cheap = run_cli('play', str(project_path), '--state', str(state_path), '--select', 'cheap', '--compact')
    assert cheap.returncode == 0, cheap.stderr
    value = json.loads(cheap.stdout)
    assert point_value(value['view'], 'budget') == 5
    assert 'six_cost' not in value['view']['available_choice_ids']

    hidden = run_cli('play', str(project_path), '--state', str(state_path), '--select', 'secret_choice', '--compact')
    missing = run_cli('play', str(project_path), '--state', str(state_path), '--select', 'not_a_real_choice', '--compact')
    assert hidden.returncode == 3
    assert missing.returncode == 3
    hidden_value = json.loads(hidden.stdout)
    missing_value = json.loads(missing.stdout)
    assert hidden_value['results'][0]['event']['code'] == 'player.unavailable'
    assert missing_value['results'][0]['event']['code'] == 'player.unavailable'
    assert hidden_value['results'][0]['event']['message'] == missing_value['results'][0]['event']['message']
    assert 'SECRET' not in hidden.stdout
    assert 'secret_choice' not in json.dumps(hidden_value['view'])
    assert point_value(hidden_value['view'], 'budget') == 5


def test_play_multi_step_request_is_player_safe_and_self_auditing(tmp_path: Path):
    project_path = tmp_path / 'project.json'
    state_path = tmp_path / 'run.state.json'
    request_path = tmp_path / 'audit.json'
    project_path.write_text(json.dumps(audit_project()), encoding='utf-8')
    request_path.write_text(json.dumps({
        'steps': [
            {
                'select': 'key',
                'expect': {
                    'points': {'budget': 7},
                    'selected': ['key'],
                    'available': ['cheap', 'six_cost'],
                    'visible': ['unlocked', 'cheap', 'six_cost'],
                    'hidden': ['secret_row', 'secret_choice'],
                },
            },
            {
                'select': 'cheap',
                'expect': {
                    'points': {'budget': 5},
                    'selected': ['key', 'cheap'],
                    'not_available': ['six_cost'],
                    'hidden': ['secret_choice'],
                },
            },
        ],
    }), encoding='utf-8')

    result = run_cli('play', str(project_path), '@' + str(request_path), '--state', str(state_path), '--compact')
    assert result.returncode == 0, result.stderr
    value = json.loads(result.stdout)
    assert value['passed'] is True
    assert len(value['steps']) == 2
    assert all(step['ok'] for step in value['steps'])
    assert point_value(value['view'], 'budget') == 5
    assert 'runtime_state' not in value
    assert 'snapshot' not in value
    assert 'SECRET' not in result.stdout
    assert 'secret_choice' not in json.dumps(value['view'])


def test_player_view_exposes_rows_choices_and_parentage_as_separate_structures():
    sim = Simulator(audit_project())
    view = sim.player_view(verbose=False)

    assert view['row_ids'] == ['start']
    assert view['choice_ids'] == ['key', 'too_expensive']
    assert view['addon_ids'] == []
    assert view['rows'][0]['kind'] == 'row'
    assert view['rows'][0]['index'] == 0
    assert view['rows'][0]['choice_ids'] == ['key', 'too_expensive']
    assert view['rows'][0]['choices'] == ['key', 'too_expensive']

    by_id = {item['id']: item for item in view['choices']}
    assert by_id['key']['row_id'] == 'start'
    assert by_id['key']['index'] == 0
    assert by_id['key']['title'] == 'Key'
    assert by_id['too_expensive']['row_id'] == 'start'
    assert by_id['too_expensive']['index'] == 1
    assert view['available_selection_ids'] == ['key']
    assert view['available_direct_choice_ids'] == ['key']
    assert view['available_selectable_addon_ids'] == []

    assert sim.select('key').ok is True
    unlocked = sim.player_view(verbose=False)
    rows = {row['id']: row for row in unlocked['rows']}
    assert rows['unlocked']['choice_ids'] == ['cheap', 'six_cost']
    choices = {item['id']: item for item in unlocked['choices']}
    assert choices['cheap']['row_id'] == 'unlocked'
    assert choices['six_cost']['row_id'] == 'unlocked'


def test_play_expectations_can_assert_row_choice_structure(tmp_path: Path):
    project_path = tmp_path / 'project.json'
    request_path = tmp_path / 'audit.json'
    project_path.write_text(json.dumps(audit_project()), encoding='utf-8')
    request_path.write_text(json.dumps({
        'steps': [
            {
                'view': True,
                'expect': {
                    'row_choices': {'start': ['key', 'too_expensive']},
                    'choice_rows': {'key': 'start', 'too_expensive': 'start'},
                },
            },
            {
                'select': 'key',
                'expect': {
                    'row_choices': {
                        'start': ['key', 'too_expensive'],
                        'unlocked': ['cheap', 'six_cost'],
                    },
                    'choice_rows': {'cheap': 'unlocked', 'six_cost': 'unlocked'},
                },
            },
        ],
    }), encoding='utf-8')

    result = run_cli('play', str(project_path), '@' + str(request_path), '--compact-view', '--compact')
    assert result.returncode == 0, result.stderr
    value = json.loads(result.stdout)
    assert value['passed'] is True
    assert all(step['ok'] for step in value['steps'])
    assert any(check['name'] == 'row_choices:start' for check in value['steps'][0]['checks'])
    assert any(check['name'] == 'choice_row:cheap' for check in value['steps'][1]['checks'])


def test_player_view_exposes_addons_as_separate_children_without_flattening_them_into_choices():
    project = {
        'version': '2.10.6',
        'pointTypes': [],
        'rows': [{
            'id': 'row_a', 'title': 'Row A', 'titleText': '', 'allowedChoices': 0, 'requireds': [],
            'objects': [{
                'id': 'choice_a', 'title': 'Choice A', 'text': '', 'requireds': [], 'scores': [],
                'addons': [
                    {'id': 'info_a', 'title': 'Info', 'text': 'Read only', 'requireds': [], 'isSelectable': False},
                    {'id': 'addon_a', 'title': 'Selectable', 'text': '', 'requireds': [], 'scores': [], 'isSelectable': True},
                ],
            }],
        }],
    }
    view = Simulator(project).player_view(verbose=False)
    assert view['choice_ids'] == ['choice_a']
    assert view['addon_ids'] == ['info_a', 'addon_a']
    assert view['informational_addon_ids'] == ['info_a']
    assert view['selectable_addon_ids'] == ['addon_a']
    assert view['available_direct_choice_ids'] == ['choice_a']
    assert view['available_selectable_addon_ids'] == ['addon_a']

    choice_a = view['choices'][0]
    assert choice_a['row_id'] == 'row_a'
    assert choice_a['addon_ids'] == ['info_a', 'addon_a']
    assert choice_a['informational_addon_ids'] == ['info_a']
    assert choice_a['selectable_addon_ids'] == ['addon_a']

    addons = {item['id']: item for item in view['addons']}
    assert addons['info_a']['row_id'] == 'row_a'
    assert addons['info_a']['choice_id'] == 'choice_a'
    assert addons['info_a']['index'] == 0
    assert addons['addon_a']['row_id'] == 'row_a'
    assert addons['addon_a']['choice_id'] == 'choice_a'
    assert addons['addon_a']['index'] == 1
