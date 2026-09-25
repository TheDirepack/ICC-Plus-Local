from __future__ import annotations

import json
from pathlib import Path

import pytest

from iccplus_tools.build_pipeline import build_from_manifest
from iccplus_tools.phase_ops import apply_phase_script, validate_phase_script
from iccplus_tools.upstream_2106 import default_export_project


def structure_script(*operations):
    return {
        'format': 'iccplus-structure-ops',
        'format_version': 1,
        'strict_fields': True,
        'operations': list(operations),
    }


def rules_script(*operations):
    return {
        'format': 'iccplus-rules-ops',
        'format_version': 1,
        'strict_fields': True,
        'operations': list(operations),
    }


def test_structure_phase_adds_sections_and_content():
    project = default_export_project()
    script = structure_script(
        {'op': 'add', 'kind': 'row', 'values': {'id': 'row_origin', 'title': 'Origin'}},
        {'op': 'add', 'kind': 'choice', 'parent': 'row_origin', 'values': {'id': 'origin_human', 'title': 'Human', 'text': 'Baseline.'}},
    )
    updated, result = apply_phase_script(project, script, 'structure')
    assert result['ok'] is True
    row = next(x for x in updated['rows'] if x['id'] == 'row_origin')
    assert row['title'] == 'Origin'
    assert row['objects'][0]['id'] == 'origin_human'
    assert row['objects'][0]['text'] == 'Baseline.'


def test_structure_phase_rejects_rules_and_style_fields():
    with pytest.raises(ValueError, match='structure phase does not allow choice field'):
        validate_phase_script(structure_script(
            {'op': 'add', 'kind': 'choice', 'parent': 'row_origin', 'values': {'id': 'x', 'title': 'X', 'scores': []}},
        ), 'structure')
    with pytest.raises(ValueError, match='structure phase does not allow row field'):
        validate_phase_script(structure_script(
            {'op': 'add', 'kind': 'row', 'values': {'id': 'r', 'title': 'R', 'styling': {}}},
        ), 'structure')


def test_rules_phase_adds_mechanics_and_rejects_content_edits():
    project, _ = apply_phase_script(default_export_project(), structure_script(
        {'op': 'add', 'kind': 'row', 'values': {'id': 'row_origin', 'title': 'Origin'}},
        {'op': 'add', 'kind': 'choice', 'parent': 'row_origin', 'values': {'id': 'origin_human', 'title': 'Human'}},
    ), 'structure')
    updated, result = apply_phase_script(project, rules_script(
        {'op': 'add', 'kind': 'point', 'values': {'id': 'budget', 'name': 'Budget', 'startingSum': 10, 'belowZeroNotAllowed': True}},
        {'op': 'score_many', 'target': 'origin_human', 'point': 'budget', 'value': -2},
        {'op': 'update', 'kind': 'row', 'ref': 'row_origin', 'values': {'allowedChoices': 1}},
    ), 'rules')
    assert result['ok'] is True
    assert updated['pointTypes'][0]['id'] == 'budget'
    row = next(x for x in updated['rows'] if x['id'] == 'row_origin')
    assert row['allowedChoices'] == 1
    assert row['objects'][0]['scores'][0]['id'] == 'budget'
    assert row['objects'][0]['scores'][0]['value'] == -2

    with pytest.raises(ValueError, match='rules phase does not allow choice field'):
        validate_phase_script(rules_script(
            {'op': 'update', 'kind': 'choice', 'ref': 'origin_human', 'values': {'title': 'Changed'}},
        ), 'rules')


def test_build_v2_uses_explicit_phase_tools(tmp_path: Path):
    (tmp_path / '10-structure.json').write_text(json.dumps(structure_script(
        {'op': 'add', 'kind': 'row', 'values': {'id': 'row_origin', 'title': 'Origin'}},
        {'op': 'add', 'kind': 'choice', 'parent': 'row_origin', 'values': {'id': 'origin_human', 'title': 'Human'}},
    )), encoding='utf-8')
    (tmp_path / '20-rules.json').write_text(json.dumps(rules_script(
        {'op': 'add', 'kind': 'point', 'values': {'id': 'budget', 'name': 'Budget', 'startingSum': 10}},
        {'op': 'score_many', 'target': 'origin_human', 'point': 'budget', 'value': -2},
    )), encoding='utf-8')
    (tmp_path / '90-style.json').write_text(json.dumps({
        'format': 'iccplus-visual-manifest',
        'format_version': 1,
        'items': [{'ref': 'origin_human', 'template': 2, 'width': 'col-md-4'}],
    }), encoding='utf-8')
    manifest = {
        'format': 'iccplus-build',
        'format_version': 2,
        'steps': [
            {'name': 'sections', 'phase': 'structure', 'script': '10-structure.json'},
            {'name': 'mechanics', 'phase': 'rules', 'script': '20-rules.json'},
            {'name': 'presentation', 'phase': 'style', 'script': '90-style.json'},
        ],
    }
    project, result = build_from_manifest(manifest, base=tmp_path)
    assert result['ok'] is True
    assert [x['phase'] for x in result['steps']] == ['structure', 'rules', 'style']
    row = next(x for x in project['rows'] if x['id'] == 'row_origin')
    choice = row['objects'][0]
    assert choice['scores'][0]['id'] == 'budget'
    assert choice['template'] == 2
    assert choice['objectWidth'] == 'col-md-4'


def test_build_v2_rejects_wrong_phase_file(tmp_path: Path):
    (tmp_path / 'bad.json').write_text(json.dumps(rules_script(
        {'op': 'add', 'kind': 'point', 'values': {'id': 'budget', 'name': 'Budget', 'startingSum': 10}},
    )), encoding='utf-8')
    manifest = {
        'format': 'iccplus-build',
        'format_version': 2,
        'steps': [{'phase': 'structure', 'script': 'bad.json'}],
    }
    with pytest.raises(ValueError, match='format must be'):
        build_from_manifest(manifest, base=tmp_path)


def test_phase_boundaries_cover_delete_and_rename_context():
    project, _ = apply_phase_script(default_export_project(), structure_script(
        {'op': 'add', 'kind': 'row', 'values': {'id': 'row_origin', 'title': 'Origin'}},
        {'op': 'add', 'kind': 'choice', 'parent': 'row_origin', 'values': {'id': 'origin_human', 'title': 'Human'}},
    ), 'structure')
    project, _ = apply_phase_script(project, rules_script(
        {'op': 'add', 'kind': 'point', 'values': {'id': 'budget', 'name': 'Budget', 'startingSum': 10}},
    ), 'rules')

    with pytest.raises(ValueError, match='rules may delete only rule entities'):
        validate_phase_script(rules_script(
            {'op': 'delete', 'kind': 'choice', 'ref': 'origin_human'},
        ), 'rules', project=project)

    with pytest.raises(ValueError, match='not a structure entity'):
        validate_phase_script(structure_script(
            {'op': 'rename', 'old': 'budget', 'new': 'budget2'},
        ), 'structure', project=project)


def test_structure_same_add_path_supports_bulk_rows_and_choices():
    project = default_export_project()
    project, result = apply_phase_script(project, structure_script(
        {'op': 'add', 'kind': 'row', 'items': [
            {'id': 'row_a', 'title': 'A'},
            {'id': 'row_b', 'title': 'B'},
            {'id': 'row_c', 'title': 'C'},
        ]},
        {'op': 'add', 'kind': 'choice', 'parent': 'row_a', 'items': [
            {'id': 'a1', 'title': 'A1'},
            {'id': 'a2', 'title': 'A2'},
            {'id': 'a3', 'title': 'A3'},
        ]},
    ), 'structure')
    assert result['ok'] is True
    assert result['requested_operation_count'] == 2
    assert result['executed_operation_count'] == 6
    assert [r['id'] for r in project['rows'][-3:]] == ['row_a', 'row_b', 'row_c']
    row_a = next(r for r in project['rows'] if r['id'] == 'row_a')
    assert [c['id'] for c in row_a['objects']] == ['a1', 'a2', 'a3']


def test_structure_same_update_path_supports_refs_and_selectors():
    project, _ = apply_phase_script(default_export_project(), structure_script(
        {'op': 'add', 'kind': 'row', 'values': {'id': 'row_a', 'title': 'A'}},
        {'op': 'add', 'kind': 'choice', 'parent': 'row_a', 'items': [
            {'id': 'a1', 'title': 'One'}, {'id': 'a2', 'title': 'Two'}, {'id': 'a3', 'title': 'Three'},
        ]},
    ), 'structure')
    project, first = apply_phase_script(project, structure_script(
        {'op': 'update', 'kind': 'choice', 'refs': ['a1', 'a2'], 'values': {'text': 'Batch text'}, 'expect': 2},
    ), 'structure')
    assert first['ok'] is True
    row = next(r for r in project['rows'] if r['id'] == 'row_a')
    assert [c.get('text') for c in row['objects'][:2]] == ['Batch text', 'Batch text']
    assert row['objects'][2]['text'] != 'Batch text'

    project, second = apply_phase_script(project, structure_script(
        {'op': 'update', 'kind': 'choice', 'where': {'row': 'row_a'}, 'values': {'debugTitle': 'audited'}, 'expect': 3},
    ), 'structure')
    assert second['ok'] is True
    row = next(r for r in project['rows'] if r['id'] == 'row_a')
    assert all(c['debugTitle'] == 'audited' for c in row['objects'])


def test_phase_scripts_reject_separate_bulk_verbs():
    with pytest.raises(ValueError, match='not allowed in the structure phase'):
        validate_phase_script(structure_script(
            {'op': 'update_many', 'kind': 'choice', 'refs': ['a', 'b'], 'values': {'text': 'x'}},
        ), 'structure')
