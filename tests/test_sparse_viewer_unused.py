from __future__ import annotations

from iccplus_tools.sparse_project import sparsify_project
from iccplus_tools.upstream_2106 import ICCPLUS_VERSION


def test_creator_edit_state_is_removed_even_when_nondefault() -> None:
    source = {
        'version': ICCPLUS_VERSION,
        'isEditModeOnAll': False,
        'rows': [{
            'id': 'row',
            'isEditModeOn': True,
            'isSimpleEditMode': True,
            'isRequirementOpen': True,
            'allowedChoices': 2,
            'objects': [{
                'id': 'choice',
                'isEditModeOn': True,
                'template': 2,
                'addons': [{
                    'id': '',
                    'isEditModeOn': True,
                    'template': 2,
                    'requireds': [{'type': 'id', 'reqId': 'keep'}],
                }],
            }],
        }],
    }

    sparse, report = sparsify_project(source, require_complete=False)
    row = sparse['rows'][0]
    choice = row['objects'][0]
    addon = choice['addons'][0]

    assert 'isEditModeOnAll' not in sparse
    assert 'isEditModeOn' not in row
    assert 'isSimpleEditMode' not in row
    assert 'isRequirementOpen' not in row
    assert 'isEditModeOn' not in choice
    assert 'isEditModeOn' not in addon

    # Adjacent Viewer behavior fields remain explicit.
    assert row['allowedChoices'] == 2
    assert choice['template'] == 2
    assert addon['template'] == 2
    assert addon['requireds'][0]['reqId'] == 'keep'
    assert report['removed_by_rule']['viewer_ignores_creator_edit_state'] == 6


def test_legacy_sfx_id_is_removed_only_when_enabled_directions_already_have_modern_ids() -> None:
    source = {
        'version': ICCPLUS_VERSION,
        'rows': [{
            'id': 'row',
            'objects': [
                {
                    'id': 'safe-choice',
                    'sfxId': 'legacy-safe',
                    'sfxOnSelect': True,
                    'sfxIdOnSelect': 'modern-select',
                    'sfxOnDeselect': True,
                    'sfxIdOnDeselect': '',
                    'addons': [{
                        'id': '',
                        'sfxId': 'legacy-addon-safe',
                        'sfxOnSelect': False,
                        'sfxOnDeselect': False,
                    }],
                },
                {
                    'id': 'needs-select-backfill',
                    'sfxId': 'legacy-select',
                    'sfxOnSelect': True,
                    'sfxOnDeselect': False,
                },
                {
                    'id': 'needs-deselect-backfill',
                    'sfxId': 'legacy-deselect',
                    'sfxOnSelect': False,
                    'sfxOnDeselect': True,
                },
            ],
        }],
    }

    sparse, report = sparsify_project(source, require_complete=False)
    safe, select_missing, deselect_missing = sparse['rows'][0]['objects']

    assert 'sfxId' not in safe
    assert safe['sfxIdOnSelect'] == 'modern-select'
    assert safe['sfxIdOnDeselect'] == ''
    assert 'sfxId' not in safe['addons'][0]

    assert select_missing['sfxId'] == 'legacy-select'
    assert deselect_missing['sfxId'] == 'legacy-deselect'
    assert report['removed_by_rule']['legacy_sfx_id_redundant_after_explicit_direction_ids'] == 2
