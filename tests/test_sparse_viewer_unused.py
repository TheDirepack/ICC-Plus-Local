from __future__ import annotations

import copy

from iccplus_tools.sparse_project import CREATOR_ONLY_TOP_LEVEL, sparsify_project
from iccplus_tools.upstream_2106 import DEFAULT_APP, ICCPLUS_VERSION


def _nondefault(value):
    if isinstance(value, bool):
        return not value
    if isinstance(value, int):
        return value + 7
    if isinstance(value, float):
        return value + 7.0
    if isinstance(value, str):
        return value + ' CUSTOM'
    if isinstance(value, list):
        return ['creator-only-noise']
    if isinstance(value, dict):
        return {'creator-only-noise': True}
    return 'creator-only-noise'


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


def test_all_creator_only_top_level_fields_are_removed_even_when_customized() -> None:
    source = {'version': ICCPLUS_VERSION, 'rows': [{'id': 'row', 'objects': []}]}
    for key in CREATOR_ONLY_TOP_LEVEL:
        assert key in DEFAULT_APP, key
        source[key] = _nondefault(copy.deepcopy(DEFAULT_APP[key]))

    # These nearby app defaults are Viewer-sensitive and must survive when
    # customized rather than being swept up with Creator construction state.
    source.update({
        'defaultChoiceMaxNum': 17,
        'defaultAddonJustify': 'end',
        'orderOrReqText': '1',
        'defaultOrReq': 'custom-of',
        'orderSelReqText': '1',
        'defaultSelReq': 'custom-choice-from',
        'cropperPosition': 2,
        'tooltipDelay': 321,
    })

    sparse, report = sparsify_project(source, require_complete=False)

    for key in CREATOR_ONLY_TOP_LEVEL:
        assert key not in sparse, key

    assert sparse['defaultChoiceMaxNum'] == 17
    assert sparse['defaultAddonJustify'] == 'end'
    assert sparse['orderOrReqText'] == '1'
    assert sparse['defaultOrReq'] == 'custom-of'
    assert sparse['orderSelReqText'] == '1'
    assert sparse['defaultSelReq'] == 'custom-choice-from'
    assert sparse['cropperPosition'] == 2
    assert sparse['tooltipDelay'] == 321
    assert report['removed_by_rule']['viewer_ignores_creator_edit_state'] >= len(CREATOR_ONLY_TOP_LEVEL)


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
