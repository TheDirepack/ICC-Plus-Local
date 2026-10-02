from __future__ import annotations

from iccplus_tools.sparse_project import sparsify_project
from iccplus_tools.upstream_2106 import ICCPLUS_VERSION


def test_viewer_unused_fields_and_score_internal_ids_are_omitted() -> None:
    source = {
        'version': ICCPLUS_VERSION,
        'pointTypes': [{
            'id': 'points',
            'name': 'Points',
            'startingSum': 10,
            'initValue': 7,
            'image': 'point.png',
            'imageIsURL': True,
        }],
        'rows': [{
            'id': 'row',
            'title': 'Row',
            'image': 'row.png',
            'imageIsUrl': True,
            'width': False,
            'objects': [{
                'id': 'choice',
                'title': 'Choice',
                'selectedThisManyTimesProp': 123,
                'scores': [{
                    'idx': 'creator-score-id',
                    'id': 'points',
                    'type': 'creator-score-type',
                    'value': 4,
                    'requireds': [],
                }],
                'addons': [{
                    'id': 'addon',
                    'title': 'Addon',
                    'template': 2,
                    'skipIndex': False,
                    'scores': [{
                        'idx': 'creator-addon-score-id',
                        'id': 'points',
                        'type': 'creator-addon-score-type',
                        'value': 2,
                        'requireds': [],
                    }],
                }],
            }],
        }],
    }

    sparse, report = sparsify_project(source, require_complete=False)
    point = sparse['pointTypes'][0]
    row = sparse['rows'][0]
    choice = row['objects'][0]
    choice_score = choice['scores'][0]
    addon = choice['addons'][0]
    addon_score = addon['scores'][0]

    assert 'imageIsURL' not in point
    assert point['image'] == 'point.png'
    assert point['initValue'] == 7

    assert 'imageIsUrl' not in row
    assert 'width' not in row
    assert row['image'] == 'row.png'

    assert 'selectedThisManyTimesProp' not in choice
    assert choice['title'] == 'Choice'

    for score in (choice_score, addon_score):
        assert 'idx' not in score
        assert 'type' not in score
        assert score['id'] == 'points'
        assert score['value'] > 0

    assert 'skipIndex' not in addon
    assert addon['template'] == 2

    assert report['removed_by_rule']['viewer_ignores_entity_field'] == 4
    assert report['removed_by_rule']['score_index_rebuilt_on_load'] == 2
    assert report['removed_by_rule']['row_false_width_is_missing_equivalent'] == 1
    assert report['removed_by_rule']['addon_false_skip_index_is_missing_equivalent'] == 1


def test_true_width_and_skip_index_remain_behavior_bearing() -> None:
    source = {
        'version': ICCPLUS_VERSION,
        'rows': [{
            'id': 'row',
            'width': True,
            'objects': [{
                'id': 'choice',
                'addons': [{
                    'id': 'addon',
                    'template': 2,
                    'skipIndex': True,
                }],
            }],
        }],
    }

    sparse, report = sparsify_project(source, require_complete=False)
    row = sparse['rows'][0]
    addon = row['objects'][0]['addons'][0]

    assert row['width'] is True
    assert addon['skipIndex'] is True
    assert 'row_false_width_is_missing_equivalent' not in report['removed_by_rule']
    assert 'addon_false_skip_index_is_missing_equivalent' not in report['removed_by_rule']
