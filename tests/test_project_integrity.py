from __future__ import annotations

import copy

from iccplus_tools.generation import build_project
from iccplus_tools.project_integrity import completeness_summary, hydrate_project
from iccplus_tools.upstream_2106 import ICCPLUS_VERSION, default_export_project
from iccplus_tools.validation import validate, validate_complete


def test_official_blank_export_is_creator_complete():
    project = default_export_project()
    report = validate_complete(project)
    assert report['valid'] is True
    assert report['mode'] == 'complete'
    assert completeness_summary(project)['complete'] is True


def test_sparse_rows_only_project_remains_readable_but_is_not_complete():
    project = {'rows': []}
    compat = validate(project)
    complete = validate_complete(project)
    assert compat['valid'] is True
    assert complete['valid'] is False
    assert any(d['code'] == 'complete.missing_field' for d in complete['diagnostics'])


def test_hydration_fills_official_sections_and_upgrades_version_without_overwriting_values():
    project = {
        'version': '2.10.6',
        'rows': [],
        'viewerConfig': {'title': 'My CYOA'},
        'styling': {'backgroundColor': '#123456FF'},
    }
    changes = hydrate_project(project, upgrade_version=True)
    assert changes
    assert project['version'] == ICCPLUS_VERSION
    assert project['viewerConfig']['title'] == 'My CYOA'
    assert project['viewerConfig']['loadingType'] == default_export_project()['viewerConfig']['loadingType']
    assert project['styling']['backgroundColor'] == '#123456FF'
    assert 'objectBorderWidth' in project['styling']
    assert 'pointTypes' in project
    assert 'backpack' in project
    assert validate_complete(project)['valid'] is True


def test_hydration_repairs_sparse_entities_but_never_invents_missing_identity():
    project = {
        'version': ICCPLUS_VERSION,
        'rows': [{
            'id': 'row_a',
            'title': 'A',
            'objects': [{'id': 'choice_a', 'title': 'A'}],
        }],
    }
    hydrate_project(project, upgrade_version=True)
    row = project['rows'][0]
    choice = row['objects'][0]
    assert row['title'] == 'A'
    assert row['image'] == ''
    assert row['requireds'] == []
    assert choice['title'] == 'A'
    assert choice['scores'] == []
    assert choice['addons'] == []
    assert validate_complete(project)['valid'] is True

    broken = copy.deepcopy(project)
    del broken['rows'][0]['objects'][0]['id']
    hydrate_project(broken, upgrade_version=True)
    assert 'id' not in broken['rows'][0]['objects'][0]
    report = validate_complete(broken)
    assert report['valid'] is False
    assert any(d['code'] in {'id.missing', 'complete.entity_missing_field'} for d in report['diagnostics'])


def test_hydration_never_downgrades_a_future_project_version():
    project = default_export_project()
    project['version'] = '2.11.0'
    changes = hydrate_project(project, upgrade_version=True)
    assert project['version'] == '2.11.0'
    assert not any(x.get('path') == '/version' and x.get('action') == 'upgraded' for x in changes)
    report = validate_complete(project)
    assert report['valid'] is False
    assert any(d['code'] == 'complete.target_version' for d in report['diagnostics'])


def test_hydration_does_not_overwrite_wrong_types_so_validation_can_report_them():
    project = default_export_project()
    project['viewerConfig']['loadingType'] = []
    hydrate_project(project, upgrade_version=True)
    assert project['viewerConfig']['loadingType'] == []
    report = validate_complete(project)
    assert report['valid'] is False
    assert any(d['code'] in {'complete.wrong_type', 'complete.field_type'} for d in report['diagnostics'])


def test_compact_generation_deep_merges_project_sections_over_official_defaults():
    project = build_project({
        'viewerConfig': {'title': 'Generated'},
        'styling': {'backgroundColor': '#ABCDEF01'},
        'rows': [{
            'id': 'row_one',
            'title': 'One',
            'objects': [{'id': 'choice_one', 'title': 'One'}],
        }],
    })
    assert project['viewerConfig']['title'] == 'Generated'
    assert project['viewerConfig']['loadingType'] == default_export_project()['viewerConfig']['loadingType']
    assert project['styling']['backgroundColor'] == '#ABCDEF01'
    assert 'objectBorderWidth' in project['styling']
    assert validate_complete(project)['valid'] is True


def test_score_remove_space_is_valid_2107_native_field():
    project = default_export_project()
    project['pointTypes'].append({
        'id': 'p', 'name': 'P', 'startingSum': 10, 'initValue': 10,
        'activatedId': '', 'beforeText': 'P:', 'afterText': '', 'category': -1,
    })
    project['rows'].append({
        'id': 'r', 'index': 0, 'title': 'R', 'titleText': '', 'debugTitle': '',
        'objectWidth': 'col-md-3', 'image': '', 'template': 1,
        'isButtonRow': False, 'isResultRow': False, 'resultGroupId': '',
        'isInfoRow': False, 'defaultAspectWidth': 1, 'defaultAspectHeight': 1,
        'allowedChoices': 0, 'currentChoices': 0, 'rowJustify': 'start',
        'requireds': [], 'isEditModeOn': False, 'isRequirementOpen': False,
        'rowDesignGroups': [], 'objects': [{
            'id': 'c', 'index': 0, 'title': 'C', 'text': '', 'debugTitle': '',
            'image': '', 'template': 1, 'objectWidth': '', 'isActive': False,
            'multipleUseVariable': 0, 'initMultipleTimesMinus': 0,
            'selectedThisManyTimesProp': 0, 'requireds': [], 'addons': [],
            'groups': [], 'objectDesignGroups': [], 'scores': [{
                'idx': 's', 'id': 'p', 'value': 2, 'type': '',
                'requireds': [], 'beforeText': 'Cost:', 'afterText': 'points',
                'showScore': True, 'removeSpace': True,
            }],
        }],
    })
    assert validate_complete(project)['valid'] is True
