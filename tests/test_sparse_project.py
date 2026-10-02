from __future__ import annotations

import copy
import json

from iccplus_tools.sparse_project import main, runtime_project_text, sparsify_project
from iccplus_tools.project_integrity import hydrate_project
from iccplus_tools.upstream_2106 import ICCPLUS_VERSION, default_export_project


def test_complete_blank_project_uses_viewer_defaults_without_dropping_version() -> None:
    source = default_export_project()
    sparse, report = sparsify_project(source)

    assert source == default_export_project()
    assert sparse['version'] == ICCPLUS_VERSION
    assert 'rows' not in sparse
    assert 'viewerConfig' not in sparse
    assert 'styling' not in sparse
    assert 'backpack' not in sparse
    assert sparse['activated'] == ['']
    assert report['source_complete'] is True
    assert report['sparse_bytes'] < report['source_bytes']
    assert report['browser_verification_required_for_unproven_rules'] is True


def test_default_runtime_text_applies_proven_omissions() -> None:
    source = default_export_project()
    text, report = runtime_project_text(source)
    runtime = json.loads(text)

    assert runtime['version'] == ICCPLUS_VERSION
    assert 'rows' not in runtime
    assert 'viewerConfig' not in runtime
    assert 'styling' not in runtime
    assert report['removed_count'] > 0


def test_nested_loader_proven_omissions_are_narrow() -> None:
    source = {
        'version': ICCPLUS_VERSION,
        'defaultAddonJustify': 'start',
        'rows': [{
            'index': 0,
            'id': 'row-a',
            'allowedChoices': 1,
            'requireds': [],
            'objects': [{
                'index': 0,
                'id': 'choice-a',
                'requireds': [],
                'scores': [],
                'groups': [],
                'objectDesignGroups': [],
                'addonJustify': 'start',
                'addons': [{
                    'id': '',
                    'template': 1,
                    'parentId': 'wrong-but-viewer-overwrites-it',
                    'requireds': [],
                    'image': 'keep-me',
                    'title': 'keep-title',
                }],
            }],
        }],
        'pointTypes': [{'id': 'p1', 'startingSum': 3, 'initValue': 3, 'name': 'P'}],
        'words': [{'id': 'w1', 'replaceText': '', 'category': -1}],
        'rowDesignGroups': [{
            'id': 'rdg',
            'name': 'R',
            'activatedId': '',
            'elements': [],
            'backpackElements': [],
            'groupElements': [],
            'styling': {'rowMargin': 12},
        }],
        'objectDesignGroups': [{
            'id': 'odg',
            'name': 'O',
            'activatedId': '',
            'elements': [],
            'backpackElements': [],
            'groupElements': [],
            'styling': {'objectMargin': 12},
        }],
    }

    sparse, _ = sparsify_project(source, require_complete=False)
    row = sparse['rows'][0]
    choice = row['objects'][0]
    addon = choice['addons'][0]

    assert 'index' not in row
    assert row['allowedChoices'] == 1
    assert row['requireds'] == []
    assert 'index' not in choice
    assert choice['requireds'] == []
    assert choice['scores'] == []
    assert choice['groups'] == []
    assert choice['objectDesignGroups'] == []
    assert 'addonJustify' not in choice
    assert 'template' not in addon
    assert 'parentId' not in addon
    assert 'requireds' not in addon
    assert addon['image'] == 'keep-me'
    assert addon['title'] == 'keep-title'
    assert 'initValue' not in sparse['pointTypes'][0]
    assert 'replaceText' not in sparse['words'][0]
    for key in ('activatedId', 'elements', 'backpackElements', 'groupElements'):
        assert key not in sparse['rowDesignGroups'][0]
        assert key not in sparse['objectDesignGroups'][0]


def test_choice_conditional_rules_require_exact_derived_value() -> None:
    source = {
        'version': ICCPLUS_VERSION,
        'defaultAddonJustify': 'center',
        'rows': [{
            'id': 'r',
            'objects': [
                {
                    'id': 'a',
                    'addonJustify': 'center',
                    'isSelectableMultiple': True,
                    'numMultipleTimesMinus': 4,
                    'forcedActivated': False,
                    'initMultipleTimesMinus': 4,
                },
                {
                    'id': 'b',
                    'addonJustify': 'start',
                    'isSelectableMultiple': True,
                    'numMultipleTimesMinus': 4,
                    'forcedActivated': True,
                    'initMultipleTimesMinus': 0,
                },
                {
                    'id': 'c',
                    'addonJustify': 'center',
                    'isSelectableMultiple': True,
                    'numMultipleTimesMinus': 4,
                    'forcedActivated': False,
                    'initMultipleTimesMinus': 2,
                },
            ],
        }],
    }

    sparse, _ = sparsify_project(source, require_complete=False)
    a, b, c = sparse['rows'][0]['objects']
    assert 'addonJustify' not in a
    assert 'initMultipleTimesMinus' not in a
    assert b['addonJustify'] == 'start'
    assert 'initMultipleTimesMinus' not in b
    assert 'addonJustify' not in c
    assert c['initMultipleTimesMinus'] == 2


def test_custom_styling_only_strips_explicitly_proven_members() -> None:
    source = {
        'version': ICCPLUS_VERSION,
        'rows': [{'id': 'r', 'objects': []}],
        'styling': {
            'objectMargin': 25,
            'customMultiTextFont': False,
            'multiChoiceCounterPosition': 0,
            'multiChoiceCounterSize': 170,
            'multiChoiceTextFont': 'Times New Roman',
            'multiChoiceTextSize': 100,
            'unselFilterSatur': 1,
        },
    }

    sparse, report = sparsify_project(source, require_complete=False)
    assert sparse['styling'] == {'objectMargin': 25, 'unselFilterSatur': 1}
    assert report['private_style_inference_applied'] is False


def test_private_filter_uses_private_loader_defaults_not_global_defaults() -> None:
    source = {
        'version': ICCPLUS_VERSION,
        'rows': [{
            'id': 'r',
            'privateFilterIsOn': True,
            'styling': {
                'unselFilterBlurIsOn': False,
                'unselFilterBlur': 0,
                'unselFilterSaturIsOn': False,
                'unselFilterSatur': 0,
            },
            'objects': [{
                'id': 'c',
                'privateFilterIsOn': True,
                'styling': {
                    'unselFilterOpacIsOn': False,
                    'unselFilterOpac': 100,
                    'unselFilterSatur': 1,
                },
            }],
        }],
    }

    sparse, report = sparsify_project(source, require_complete=False)
    row = sparse['rows'][0]
    choice = row['objects'][0]

    assert row['privateFilterIsOn'] is True
    assert row['styling'] == {}
    assert choice['privateFilterIsOn'] is True
    assert choice['styling'] == {'unselFilterSatur': 1}
    assert report['removed_by_rule']['private_filter_explicit_loader_default'] == 6
    assert report['private_style_inference_applied'] is False


def test_runtime_discarded_fields_and_null_object_members_do_not_survive() -> None:
    source = {
        'version': ICCPLUS_VERSION,
        'rows': [{'id': 'r', 'objects': []}],
        'bgmTitle': 'ignored runtime value',
        'autoSaveInterval': 999,
        'custom': {'a': None, 'b': 1, 'nested': {'c': None, 'd': 2}},
        'array': [None, {'x': None, 'y': 3}],
    }

    sparse, report = sparsify_project(source, require_complete=False)
    assert 'bgmTitle' not in sparse
    assert 'autoSaveInterval' not in sparse
    assert sparse['custom'] == {'b': 1, 'nested': {'d': 2}}
    assert sparse['array'][0] is None
    assert sparse['array'][1] == {'y': 3}
    assert report['array_null_filtering_applied'] is False


def test_wrong_target_version_is_rejected() -> None:
    source = {'version': '2.10.8', 'rows': []}
    try:
        sparsify_project(source, require_complete=False)
    except ValueError as exc:
        assert 'pinned to ICC Plus 2.10.7' in str(exc)
    else:
        raise AssertionError('expected target-version rejection')



def test_sparse_hydrate_sparse_roundtrip_is_idempotent_for_saved_project(tmp_path) -> None:
    source = json.loads((__import__('pathlib').Path(__file__).parents[1] / 'examples' / 'demo_project.json').read_text(encoding='utf-8'))
    hydrate_project(source, upgrade_version=True)
    first, _ = sparsify_project(source)
    materialized = copy.deepcopy(first)
    hydrate_project(materialized, upgrade_version=True)
    second, _ = sparsify_project(materialized)
    assert second == first


def test_cli_writes_separate_sparse_artifact(tmp_path) -> None:
    source = tmp_path / 'source.json'
    output = tmp_path / 'release.json'
    project = default_export_project()
    source.write_text(json.dumps(project), encoding='utf-8')

    assert main([str(source), '-o', str(output)]) == 0
    assert json.loads(source.read_text(encoding='utf-8')) == project
    sparse = json.loads(output.read_text(encoding='utf-8'))
    assert sparse['version'] == ICCPLUS_VERSION
    assert 'rows' not in sparse
