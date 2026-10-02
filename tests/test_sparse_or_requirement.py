from __future__ import annotations

import copy

from iccplus_tools.sparse_project import sparsify_project
from iccplus_tools.upstream_2106 import ICCPLUS_VERSION


def _derived_child(parent: dict, req_id: str) -> dict:
    return {
        'required': True,
        'requireds': [],
        'orRequired': [],
        'orRequireds': [],
        'id': '',
        'type': 'id',
        'reqId': req_id,
        'reqId1': '',
        'reqId2': '',
        'reqId3': '',
        'reqPoints': 0,
        'selFromOperators': '1',
        'more': [],
        'showRequired': parent['showRequired'],
        'operator': parent['operator'],
        'afterText': parent['afterText'],
        'beforeText': parent['beforeText'],
        'orNum': parent['orNum'],
        'selNum': parent['selNum'],
    }


def _legacy_or(req_id: str = 'target') -> dict:
    req = {
        'required': True,
        'requireds': [],
        'orRequired': [{'req': req_id}],
        'orRequireds': [],
        'id': '',
        'type': 'or',
        'reqId': '',
        'reqId1': '',
        'reqId2': '',
        'reqId3': '',
        'reqPoints': 0,
        'showRequired': False,
        'operator': '1',
        'afterText': 'choice',
        'beforeText': 'Required:',
        'orNum': 1,
        'selNum': 1,
        'selFromOperators': '1',
        'more': [],
    }
    req['orRequireds'] = [_derived_child(req, req_id)]
    return req


def _id_requirement(*, nested: list[dict] | None = None) -> dict:
    return {
        'required': True,
        'requireds': copy.deepcopy(nested or []),
        'orRequired': [],
        'orRequireds': [],
        'id': '',
        'type': 'id',
        'reqId': 'target',
        'reqId1': '',
        'reqId2': '',
        'reqId3': '',
        'reqPoints': 0,
        'showRequired': False,
        'operator': '1',
        'afterText': 'choice',
        'beforeText': 'Required:',
        'orNum': 1,
        'selNum': 1,
        'selFromOperators': '1',
        'more': [],
    }


def test_exact_legacy_or_payload_is_stripped_only_in_loader_migrated_containers() -> None:
    source = {
        'version': ICCPLUS_VERSION,
        'rows': [{
            'id': 'row',
            'requireds': [_legacy_or('row-target')],
            'objects': [{
                'id': 'choice',
                'requireds': [_legacy_or('choice-target')],
                'scores': [{
                    'idx': 'choice-score',
                    'requireds': [_legacy_or('score-target')],
                }],
                'addons': [{
                    'id': '',
                    'requireds': [_legacy_or('addon-target')],
                    'scores': [{
                        'idx': 'addon-score',
                        'requireds': [_legacy_or('addon-score-target')],
                    }],
                }],
            }],
        }],
        'globalRequirements': [{
            'id': 'global',
            'requireds': [_legacy_or('global-target')],
        }],
        'soundEffects': [{
            'id': 'sfx',
            'requireds': [_legacy_or('sfx-target')],
            'groups': [],
        }],
    }

    sparse, report = sparsify_project(source, require_complete=False)
    row = sparse['rows'][0]
    choice = row['objects'][0]
    addon = choice['addons'][0]

    assert 'orRequireds' not in row['requireds'][0]
    assert 'orRequireds' not in choice['requireds'][0]
    assert 'orRequireds' not in choice['scores'][0]['requireds'][0]
    assert 'orRequireds' not in addon['requireds'][0]
    assert 'orRequireds' not in sparse['globalRequirements'][0]['requireds'][0]

    # initializeApp does not run the same OR migration for Sound Effect
    # requirements or Score requirements attached to selectable Addons.
    assert sparse['soundEffects'][0]['requireds'][0]['orRequireds']
    assert addon['scores'][0]['requireds'][0]['orRequireds']
    assert report['removed_by_rule']['requirement_or_requireds_legacy_derived'] == 5


def test_loader_supported_one_level_nested_or_is_stripped_but_deeper_or_is_not() -> None:
    one_level = _id_requirement(nested=[_legacy_or('nested-target')])
    two_levels = _id_requirement(nested=[_id_requirement(nested=[_legacy_or('deep-target')])])
    source = {
        'version': ICCPLUS_VERSION,
        'rows': [{
            'id': 'row',
            'requireds': [one_level, two_levels],
            'objects': [],
        }],
    }

    sparse, report = sparsify_project(source, require_complete=False)
    requireds = sparse['rows'][0]['requireds']

    assert 'orRequireds' not in requireds[0]['requireds'][0]
    assert requireds[1]['requireds'][0]['requireds'][0]['orRequireds']
    assert report['removed_by_rule']['requirement_or_requireds_legacy_derived'] == 1


def test_nonmatching_or_requireds_is_preserved() -> None:
    req = _legacy_or('target')
    req['orRequireds'][0]['reqId'] = 'intentionally-different'
    source = {
        'version': ICCPLUS_VERSION,
        'rows': [{'id': 'row', 'requireds': [req], 'objects': []}],
    }

    sparse, report = sparsify_project(source, require_complete=False)

    assert sparse['rows'][0]['requireds'][0]['orRequireds'][0]['reqId'] == 'intentionally-different'
    assert 'requirement_or_requireds_legacy_derived' not in report['removed_by_rule']
