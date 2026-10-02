from __future__ import annotations

from iccplus_tools.sparse_project import sparsify_project
from iccplus_tools.upstream_2106 import ICCPLUS_VERSION


def test_creator_categories_and_entity_category_indices_are_not_serialized_to_viewer() -> None:
    source = {
        'version': ICCPLUS_VERSION,
        'categories': [
            {'idx': 0, 'name': 'Points', 'type': 'point'},
            {'idx': 4, 'name': 'Groups', 'type': 'group'},
        ],
        'pointTypes': [{
            'id': 'p', 'name': 'P', 'startingSum': 0, 'initValue': 1,
            'activatedId': '', 'beforeText': 'P:', 'afterText': '', 'category': 0,
        }],
        'variables': [{'id': 'v', 'isTrue': False, 'category': 3}],
        'words': [{'id': 'w', 'replaceText': 'keep', 'category': 2}],
        'groups': [{
            'id': 'g', 'name': 'G', 'category': 4,
            'elements': ['keep-choice'], 'rowElements': ['keep-row'],
        }],
        'globalRequirements': [{
            'id': 'gr', 'name': 'Global', 'category': 5, 'requireds': [],
        }],
        'rowDesignGroups': [{
            'id': 'rdg', 'name': 'Row design', 'category': 6,
            'activatedId': 'keep-activation', 'elements': ['keep-row'],
            'backpackElements': [], 'groupElements': [], 'styling': {'rowMargin': 12},
        }],
        'objectDesignGroups': [{
            'id': 'odg', 'name': 'Choice design', 'category': 7,
            'activatedId': 'keep-activation', 'elements': ['keep-choice'],
            'backpackElements': [], 'groupElements': [], 'styling': {'objectMargin': 12},
        }],
    }

    sparse, report = sparsify_project(source, require_complete=False)

    assert 'categories' not in sparse
    for collection in (
        'pointTypes', 'variables', 'words', 'groups', 'globalRequirements',
        'rowDesignGroups', 'objectDesignGroups',
    ):
        assert 'category' not in sparse[collection][0]

    # Prove this rule does not erase adjacent runtime-bearing data.
    assert sparse['pointTypes'][0]['initValue'] == 1
    assert sparse['variables'][0]['isTrue'] is False
    assert sparse['words'][0]['replaceText'] == 'keep'
    assert sparse['groups'][0]['elements'] == ['keep-choice']
    assert sparse['groups'][0]['rowElements'] == ['keep-row']
    assert sparse['rowDesignGroups'][0]['activatedId'] == 'keep-activation'
    assert sparse['rowDesignGroups'][0]['elements'] == ['keep-row']
    assert sparse['objectDesignGroups'][0]['activatedId'] == 'keep-activation'
    assert sparse['objectDesignGroups'][0]['elements'] == ['keep-choice']

    assert report['removed_by_rule']['viewer_ignores_creator_categories'] == 1
    assert report['removed_by_rule']['viewer_ignores_creator_category_metadata'] == 7
