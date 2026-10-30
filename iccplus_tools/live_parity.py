from __future__ import annotations

import copy
from typing import Any

from .model import ProjectIndex
from .requirements import RequirementEngine
from .simulator import Simulator
from .upstream_2106 import default_project


def _choice(ident: str, **extra: Any) -> dict[str, Any]:
    out: dict[str, Any] = {
        'id': ident,
        'index': 0,
        'title': ident,
        'text': '',
        'debugTitle': '',
        'image': '',
        'template': 1,
        'objectWidth': '',
        'isActive': False,
        'multipleUseVariable': 0,
        'initMultipleTimesMinus': 0,
        'selectedThisManyTimesProp': 0,
        'requireds': [],
        'addons': [],
        'scores': [],
        'groups': [],
        'objectDesignGroups': [],
    }
    out.update(extra)
    return out


def _row(ident: str, objects: list[dict[str, Any]], *, allowed: int = 0) -> dict[str, Any]:
    return {
        'index': 0,
        'id': ident,
        'title': ident,
        'titleText': '',
        'debugTitle': '',
        'objectWidth': 'col-md-3',
        'image': '',
        'template': 1,
        'isButtonRow': False,
        'isResultRow': False,
        'resultGroupId': '',
        'isInfoRow': False,
        'defaultAspectWidth': 1,
        'defaultAspectHeight': 1,
        'allowedChoices': allowed,
        'currentChoices': 0,
        'rowJustify': 'start',
        'requireds': [],
        'isEditModeOn': False,
        'isRequirementOpen': False,
        'objects': objects,
        'rowDesignGroups': [],
    }


def _point(ident: str, value: float, **extra: Any) -> dict[str, Any]:
    out: dict[str, Any] = {
        'id': ident,
        'name': ident,
        'startingSum': value,
        'initValue': value,
        'activatedId': '',
        'beforeText': '',
        'afterText': '',
        'category': -1,
    }
    out.update(extra)
    return out


def _req(typ: str, **extra: Any) -> dict[str, Any]:
    out: dict[str, Any] = {
        'required': True,
        'requireds': [],
        'orRequired': [],
        'orRequireds': [],
        'id': '',
        'type': typ,
        'reqId': '',
        'reqId1': '',
        'reqId2': '',
        'reqId3': '',
        'reqPoints': 0,
        'showRequired': False,
        'operator': '1',
        'afterText': '',
        'beforeText': '',
        'orNum': 1,
        'selNum': 1,
        'selFromOperators': '1',
        'more': [],
    }
    out.update(extra)
    return out


def _project(*, rows: list[dict[str, Any]], points: list[dict[str, Any]] | None = None,
             groups: list[dict[str, Any]] | None = None, variables: list[dict[str, Any]] | None = None,
             words: list[dict[str, Any]] | None = None,
             global_requirements: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    p = default_project()
    p['rows'] = copy.deepcopy(rows)
    for i, row in enumerate(p['rows']):
        row['index'] = i
        for j, obj in enumerate(row.get('objects', [])):
            obj['index'] = j
    p['pointTypes'] = copy.deepcopy(points or [])
    p['groups'] = copy.deepcopy(groups or [])
    p['variables'] = copy.deepcopy(variables or [])
    p['words'] = copy.deepcopy(words or [])
    p['globalRequirements'] = copy.deepcopy(global_requirements or [])
    p['activated'] = []
    return p


def live_cases() -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []

    groups = [
        {'id': 'g1', 'name': 'g1', 'category': -1, 'elements': ['a'], 'rowElements': []},
        {'id': 'g2', 'name': 'g2', 'category': -1, 'elements': ['a'], 'rowElements': []},
    ]
    req_overlap = _req('selFromGroups', selNum=2, selFromOperators='2', selGroups=['g1', 'g2'])
    cases.append({
        'name': 'sel_from_groups_overlap',
        'project': _project(rows=[_row('r', [_choice('a'), _choice('target', requireds=[req_overlap])])], groups=groups),
        'actions': [{'op': 'select', 'id': 'a'}],
        'check_requirements': ['target'],
    })

    req_pc = _req('pointCompare', reqId='a', reqId1='b', operator='1', more=[
        {'operator': '1', 'type': 'points', 'points': 2, 'priority': 0},
        {'operator': '3', 'type': 'points', 'points': 3, 'priority': 1},
    ])
    cases.append({
        'name': 'point_compare_priority_zero',
        'project': _project(rows=[_row('r', [_choice('target', requireds=[req_pc])])], points=[_point('a', 20), _point('b', 10)]),
        'actions': [],
        'check_requirements': ['target'],
    })

    cases.append({
        'name': 'malformed_repeat_noop',
        'project': _project(rows=[_row('r', [_choice('x', isSelectableMultiple=True, numMultipleTimesMinus=0, numMultipleTimesPluss=9)])]),
        'actions': [{'op': 'select', 'id': 'x'}],
    })

    cases.append({
        'name': 'point_backed_repeat',
        'project': _project(
            rows=[_row('r', [_choice('x', isSelectableMultiple=True, multipleScoreId='p', numMultipleTimesMinus=0, numMultipleTimesPluss=3)])],
            points=[_point('p', 1)],
        ),
        'actions': [{'op': 'select', 'id': 'x'}, {'op': 'deselect', 'id': 'x'}],
    })

    cases.append({
        'name': 'negative_repeat_cross_zero',
        'project': _project(rows=[_row('r', [_choice('x', isSelectableMultiple=True, isMultipleUseVariable=True, numMultipleTimesMinus=-2, numMultipleTimesPluss=2)])]),
        'actions': [{'op': 'deselect', 'id': 'x'}, {'op': 'select', 'id': 'x'}],
    })

    source = _choice(
        'x', isSelectableMultiple=True, isMultipleUseVariable=True,
        numMultipleTimesMinus=0, numMultipleTimesPluss=9,
        addToAllowChoice=True, idOfAllowChoice=['target_row'], numbAddToAllowChoice=2,
    )
    cases.append({
        'name': 'repeat_add_to_allow',
        'project': _project(rows=[_row('source_row', [source]), _row('target_row', [], allowed=1)]),
        'actions': [{'op': 'select', 'id': 'x'}, {'op': 'select', 'id': 'x'}, {'op': 'deselect', 'id': 'x'}],
    })

    cases.append({
        'name': 'repeat_does_not_run_point_modifier',
        'project': _project(
            rows=[_row('r', [_choice('x', isSelectableMultiple=True, isMultipleUseVariable=True,
                                    numMultipleTimesMinus=0, numMultipleTimesPluss=9,
                                    multiplyPointtypeIsOn=True, pointTypeToMultiply=['p'], multiplyWithThis=2)])],
            points=[_point('p', 5)],
        ),
        'actions': [{'op': 'select', 'id': 'x'}],
    })

    cases.append({
        'name': 'point_modifier_can_cross_negative_guard',
        'project': _project(
            rows=[_row('r', [_choice('x', setPointtypeIsOn=True, pointTypeToSet=['p'], setWithThis='-2')])],
            points=[_point('p', 5, belowZeroNotAllowed=True)],
        ),
        'actions': [{'op': 'select', 'id': 'x'}],
    })

    cases.append({
        'name': 'forced_parseint_prefix',
        'project': _project(rows=[_row('r', [
            _choice('multi', isSelectableMultiple=True, isMultipleUseVariable=True, numMultipleTimesMinus=0, numMultipleTimesPluss=9),
            _choice('source', activateOtherChoice=True, activateThisChoice='multi/ON#2junk'),
        ])]),
        'actions': [{'op': 'select', 'id': 'source'}],
    })

    cases.append({
        'name': 'repeated_force_targets',
        'project': _project(rows=[_row('r', [
            _choice('multi', isSelectableMultiple=True, isMultipleUseVariable=True, numMultipleTimesMinus=0, numMultipleTimesPluss=9),
            _choice('source', activateOtherChoice=True, activateThisChoice='multi/ON#1,multi/ON#1'),
        ])]),
        'actions': [{'op': 'select', 'id': 'source'}],
    })

    cases.append({
        'name': 'negative_forced_repeat_2106_noop',
        'project': _project(rows=[_row('r', [
            _choice('multi', isSelectableMultiple=True, isMultipleUseVariable=True, numMultipleTimesMinus=-9, numMultipleTimesPluss=9),
            _choice('source', activateOtherChoice=True, activateThisChoice='multi/ON#-2'),
        ])]),
        'actions': [{'op': 'select', 'id': 'source'}],
    })

    cases.append({
        'name': 'ordinary_self_deactivate',
        'project': _project(rows=[_row('r', [_choice('x', deactivateOtherChoice=True, deactivateThisChoice='x')])]),
        'actions': [{'op': 'select', 'id': 'x'}],
    })

    cases.append({
        'name': 'repeat_self_deactivate',
        'project': _project(rows=[_row('r', [_choice(
            'x', isSelectableMultiple=True, isMultipleUseVariable=True,
            numMultipleTimesMinus=0, numMultipleTimesPluss=9,
            deactivateOtherChoice=True, deactivateThisChoice='x/ON#1',
        )])]),
        'actions': [{'op': 'select', 'id': 'x'}],
    })

    cases.append({
        'name': 'row_capacity_clears_positive_repeat',
        'project': _project(rows=[_row('r', [
            _choice('multi', isSelectableMultiple=True, isMultipleUseVariable=True, numMultipleTimesMinus=0, numMultipleTimesPluss=9),
            _choice('next'),
        ], allowed=1)]),
        'actions': [{'op': 'select', 'id': 'multi'}, {'op': 'select', 'id': 'multi'}, {'op': 'select', 'id': 'next'}],
    })

    cases.append({
        'name': 'negative_repeat_cannot_free_row_capacity',
        'project': _project(rows=[_row('r', [
            _choice('multi', isSelectableMultiple=True, isMultipleUseVariable=True, numMultipleTimesMinus=-2, numMultipleTimesPluss=2),
            _choice('next'),
        ], allowed=1)]),
        'actions': [{'op': 'deselect', 'id': 'multi'}, {'op': 'select', 'id': 'next'}],
    })

    cases.append({
        'name': 'preset_deactivate_then_set_order',
        'project': _project(
            rows=[_row('r', [
                _choice('standard', setPointtypeIsOn=True, pointTypeToSet=['p'], setWithThis='290', deactivateOtherChoice=True, deactivateThisChoice='generous'),
                _choice('generous', setPointtypeIsOn=True, pointTypeToSet=['p'], setWithThis='370', deactivateOtherChoice=True, deactivateThisChoice='standard'),
            ])],
            points=[_point('p', 290)],
        ),
        'actions': [{'op': 'select', 'id': 'standard'}, {'op': 'select', 'id': 'generous'}],
    })

    cases.append({
        'name': 'deactivate_direct_list',
        'project': _project(rows=[_row('r', [
            _choice('a'), _choice('b'),
            _choice('source', deactivateOtherChoice=True, deactivateThisChoice='a,b'),
        ])]),
        'actions': [{'op': 'select', 'id': 'a'}, {'op': 'select', 'id': 'b'}, {'op': 'select', 'id': 'source'}],
    })

    cases.append({
        'name': 'deactivate_group',
        'project': _project(
            rows=[_row('r', [_choice('a'), _choice('b'), _choice('source', deactivateOtherChoice=True, deactivateThisChoice='g')])],
            groups=[{'id': 'g', 'name': 'G', 'category': -1, 'elements': ['a', 'b'], 'rowElements': []}],
        ),
        'actions': [{'op': 'select', 'id': 'a'}, {'op': 'select', 'id': 'b'}, {'op': 'select', 'id': 'source'}],
    })

    cases.append({
        'name': 'deactivate_repeat_count',
        'project': _project(rows=[_row('r', [
            _choice('multi', isSelectableMultiple=True, isMultipleUseVariable=True, numMultipleTimesMinus=0, numMultipleTimesPluss=9),
            _choice('source', deactivateOtherChoice=True, deactivateThisChoice='multi/ON#2'),
        ])]),
        'actions': [
            {'op': 'select', 'id': 'multi'}, {'op': 'select', 'id': 'multi'},
            {'op': 'select', 'id': 'multi'}, {'op': 'select', 'id': 'multi'},
            {'op': 'select', 'id': 'source'},
        ],
    })

    cases.append({
        'name': 'basic_score_cost',
        'project': _project(
            rows=[_row('r', [_choice('x', scores=[{'idx': 's', 'id': 'p', 'value': 3, 'requireds': [], 'showScore': True}])])],
            points=[_point('p', 10, belowZeroNotAllowed=True)],
        ),
        'actions': [{'op': 'select', 'id': 'x'}],
    })

    cases.append({
        'name': 'below_zero_blocks_score_cost',
        'project': _project(
            rows=[_row('r', [_choice('x', scores=[{'idx': 's', 'id': 'p', 'value': 2, 'requireds': [], 'showScore': True}])])],
            points=[_point('p', 1, belowZeroNotAllowed=True)],
        ),
        'actions': [{'op': 'select', 'id': 'x'}],
    })

    cases.append({
        'name': 'multiply_by_times_one_based',
        'project': _project(
            rows=[_row('r', [_choice(
                'multi', isSelectableMultiple=True, isMultipleUseVariable=True,
                numMultipleTimesMinus=0, numMultipleTimesPluss=5,
                scores=[{'idx': 's', 'id': 'p', 'value': 2, 'multiplyByTimes': True, 'requireds': [], 'showScore': True}],
            )])],
            points=[_point('p', 20, belowZeroNotAllowed=True)],
        ),
        'actions': [{'op': 'select', 'id': 'multi'}, {'op': 'select', 'id': 'multi'}, {'op': 'select', 'id': 'multi'}],
    })

    addon_parent = _choice('parent')
    addon_parent['addons'] = [{
        'id': 'addon', 'title': 'addon', 'text': '', 'template': 1, 'addonWidth': 'col-12',
        'image': '', 'requireds': [], 'parentId': 'parent', 'isSelectable': True,
        'scores': [], 'groups': [], 'multipleUseVariable': 0, 'isActive': False,
    }]
    cases.append({
        'name': 'selectable_addon_activates_parent',
        'project': _project(rows=[_row('r', [addon_parent])]),
        'actions': [{'op': 'select', 'id': 'addon'}],
    })

    addon_parent = _choice('parent')
    addon_parent['addons'] = [{
        'id': 'addon', 'title': 'addon', 'text': '', 'template': 1, 'addonWidth': 'col-12',
        'image': '', 'requireds': [], 'parentId': 'parent', 'isSelectable': True,
        'scores': [], 'groups': [], 'multipleUseVariable': 0, 'isActive': False,
        'deselectParent': True,
    }]
    cases.append({
        'name': 'selectable_addon_deselect_parent',
        'project': _project(rows=[_row('r', [addon_parent])]),
        'actions': [{'op': 'select', 'id': 'addon'}, {'op': 'deselect', 'id': 'addon'}],
    })

    cases.append({
        'name': 'forced_nonselectable_target',
        'project': _project(rows=[_row('r', [
            _choice('target', isNotSelectable=True),
            _choice('source', activateOtherChoice=True, activateThisChoice='target'),
        ])]),
        'actions': [{'op': 'select', 'id': 'source'}],
    })

    cases.append({
        'name': 'forced_nonselectable_target_blocked',
        'project': _project(rows=[_row('r', [
            _choice('target', isNotSelectable=True),
            _choice('source', activateOtherChoice=True, activateThisChoice='target', isNotActiveUnselectable=True),
        ])]),
        'actions': [{'op': 'select', 'id': 'source'}],
    })

    cases.append({
        'name': 'forced_allow_deselect',
        'project': _project(rows=[_row('r', [
            _choice('target', isNotSelectable=True),
            _choice('source', activateOtherChoice=True, activateThisChoice='target', isAllowDeselect=True),
        ])]),
        'actions': [{'op': 'select', 'id': 'source'}, {'op': 'deselect', 'id': 'target'}],
    })

    cleanup_req = _req('id', reqId='gate')
    cases.append({
        'name': 'requirement_cleanup_after_linked_deactivation',
        'project': _project(rows=[_row('r', [
            _choice('gate'),
            _choice('target', requireds=[cleanup_req]),
            _choice('source', deactivateOtherChoice=True, deactivateThisChoice='gate'),
        ])]),
        'actions': [{'op': 'select', 'id': 'gate'}, {'op': 'select', 'id': 'target'}, {'op': 'select', 'id': 'source'}],
        'check_requirements': ['target'],
    })

    cases.append({
        'name': 'variable_toggle_and_word_change',
        'project': _project(
            rows=[_row('r', [_choice(
                'x', isChangeVariables=True, changedVariables=['v'], changeType='3',
                textfieldIsOn=True, idOfTheTextfieldWord='w', wordChangeSelect='selected', wordChangeDeselect='deselected',
            )])],
            variables=[{'id': 'v', 'name': 'v', 'isTrue': False, 'category': -1}],
            words=[{'id': 'w', 'name': 'w', 'replaceText': 'start', 'category': -1}],
        ),
        'actions': [{'op': 'select', 'id': 'x'}, {'op': 'deselect', 'id': 'x'}],
    })

    reqs = [
        _choice('a'),
        _choice('id_req', requireds=[_req('id', reqId='a')]),
        _choice('neg_id_req', requireds=[_req('id', required=False, reqId='missing')]),
        _choice('points_req', requireds=[_req('points', reqId='p', reqPoints=4, operator='2')]),
        _choice('or_req', requireds=[_req('or', orNum=1, orRequireds=[_req('id', reqId='a'), _req('id', reqId='missing')])]),
        _choice('row_req', requireds=[_req('selFromRows', selRows=['r'], selNum=1, selFromOperators='1')]),
        _choice('whole_req', requireds=[_req('selFromWhole', selNum=1, selFromOperators='1')]),
        _choice('gid_req', requireds=[_req('gid', reqId='global')]),
        _choice('word_req', requireds=[_req('word', reqId='w', orRequired=[{'req': 'yes'}])]),
    ]
    cases.append({
        'name': 'requirement_type_matrix',
        'project': _project(
            rows=[_row('r', reqs)],
            points=[_point('p', 5)],
            words=[{'id': 'w', 'name': 'w', 'replaceText': 'yes', 'category': -1}],
            global_requirements=[{'id': 'global', 'name': 'global', 'category': -1, 'requireds': [_req('id', reqId='a')]}],
        ),
        'actions': [{'op': 'select', 'id': 'a'}],
        'check_requirements': ['id_req', 'neg_id_req', 'points_req', 'or_req', 'row_req', 'whole_req', 'gid_req', 'word_req'],
    })

    cases.append({
        'name': 'random_activate_all_and_release',
        'project': _project(rows=[_row('r', [
            _choice('a'), _choice('b'),
            _choice('source', activateOtherChoice=True, activateThisChoice='a,b', isActivateRandom=True, numActivateRandom=2),
        ])]),
        'actions': [{'op': 'select', 'id': 'source'}, {'op': 'deselect', 'id': 'source'}],
    })

    cases.append({
        'name': 'reset_init_auto_preserve',
        'project': _project(
            rows=[_row('r', [_choice('keep', notDeselectedByClean=True), _choice('auto', isAutoActive=True)])],
            points=[_point('p', 7, initValue=3)],
        ),
        'actions': [{'op': 'select', 'id': 'keep'}, {'op': 'set_point', 'id': 'p', 'value': 99}, {'op': 'reset'}],
    })

    # 2.10.14: activated selections can deliberately survive lost Requirements.
    # A normal neighboring choice must still be cleaned.
    cases.append({
        'name': 'protected_requirements_cleanup_21014',
        'project': _project(rows=[_row('r', [
            _choice('gate'),
            _choice('protected', requireds=[_req('id', reqId='gate')], notDeselectedByReq=True),
            _choice('ordinary', requireds=[_req('id', reqId='gate')]),
        ])]),
        'actions': [
            {'op': 'select', 'id': 'gate'},
            {'op': 'select', 'id': 'protected'},
            {'op': 'select', 'id': 'ordinary'},
            {'op': 'deselect', 'id': 'gate'},
        ],
        'check_requirements': ['protected', 'ordinary'],
    })

    # The 2.10.14 checkSelectable path also avoids row-cap replacement of a
    # protected selection; explicit manual deselection remains a separate rule.
    cases.append({
        'name': 'protected_row_capacity_21014',
        'project': _project(rows=[_row('r', [
            _choice('protected', notDeselectedByReq=True),
            _choice('next'),
        ], allowed=1)]),
        'actions': [
            {'op': 'select', 'id': 'protected'},
            {'op': 'select', 'id': 'next'},
        ],
    })

    cases.append({
        'name': 'protected_selectable_addon_requirements_21014',
        'project': _project(rows=[_row('r', [
            _choice('gate'),
            _choice('parent', addons=[{
                'id': 'sub', 'title': 'Sub', 'text': '', 'image': '',
                'template': 1, 'addonWidth': 'col-12', 'parentId': 'parent',
                'isSelectable': True, 'scores': [], 'groups': [],
                'multipleUseVariable': 0, 'isActive': False,
                'requireds': [_req('id', reqId='gate')],
                'notDeselectedByReq': True,
            }]),
        ])]),
        'actions': [
            {'op': 'select', 'id': 'gate'},
            {'op': 'select', 'id': 'parent'},
            {'op': 'select', 'id': 'sub'},
            {'op': 'deselect', 'id': 'gate'},
        ],
        'check_requirements': ['sub'],
    })

    # Discount values already applied on a Score are supported natively by
    # Local. Verify charged and refunded points against the official Viewer;
    # dynamic discount stacking and discount-source updates remain separate.
    fixed_score = {
        'idx': 'discount-score', 'id': 'p', 'value': 8,
        'requireds': [], 'showScore': True,
        'discountIsOn': True, 'appliedDiscount': True,
        'discountScore': 2, 'discounts': [],
    }
    for name, actions in (
        ('preapplied_discount_charge_21015', [{'op': 'select', 'id': 'purchase'}]),
        ('preapplied_discount_refund_21015', [
            {'op': 'select', 'id': 'purchase'},
            {'op': 'deselect', 'id': 'purchase'},
        ]),
    ):
        cases.append({
            'name': name,
            'project': _project(
                rows=[_row('r', [_choice('purchase', scores=[copy.deepcopy(fixed_score)])])],
                points=[_point('p', 20)],
            ),
            'actions': actions,
        })

    return cases



def sparse_equivalence_cases() -> list[dict[str, Any]]:
    """Compare canonical Local sparse files with Creator-complete originals in
    the actual pinned official Viewer, not just the Python hydration path.
    """
    from .omission_probe import _base_project
    from .editor import make_entity
    from .sparse_project import sparsify_project
    from .upstream_2106 import default_export_project

    cases: list[dict[str, Any]] = []
    originals = [
        ('empty_default', default_export_project(), []),
        ('single_choice_unselected', _base_project(), []),
        ('single_choice_selected', _base_project(), [{'op': 'select', 'id': 'probe-choice'}]),
    ]
    protected = _base_project()
    protected['rows'][0]['objects'][0]['notDeselectedByReq'] = True
    originals.append(('protected_choice_selected', protected, [{'op': 'select', 'id': 'probe-choice'}]))

    # Exercise sparse transformations in realistic, stateful content: costs,
    # row limits, selectable Addons, repeat counters and requirements.
    points = _base_project()
    points['pointTypes'].append(make_entity(points, 'point', {
        'id': 'probe-points', 'name': 'Points', 'startingSum': 20, 'initValue': 20,
    }))
    points['rows'][0]['objects'][0]['scores'].append(make_entity(points, 'score', {
        'idx': 'probe-score', 'id': 'probe-points', 'value': 4,
    }))
    originals.append(('point_cost_selected', points, [{'op': 'select', 'id': 'probe-choice'}]))
    originals.append(('point_cost_refunded', copy.deepcopy(points), [
        {'op': 'select', 'id': 'probe-choice'}, {'op': 'deselect', 'id': 'probe-choice'},
    ]))

    # An already-applicable fixed discount is exercised separately from
    # unimplemented dynamic discounts and stacking in the headless simulator.
    applied = copy.deepcopy(points)
    applied_score = applied['rows'][0]['objects'][0]['scores'][0]
    applied_score.update({
        'discountIsOn': True, 'appliedDiscount': True,
        'discountScore': 2, 'discounts': [],
    })
    originals.append(('applied_discount_selected', applied, [
        {'op': 'select', 'id': 'probe-choice'},
    ]))
    originals.append(('applied_discount_refunded', copy.deepcopy(applied), [
        {'op': 'select', 'id': 'probe-choice'}, {'op': 'deselect', 'id': 'probe-choice'},
    ]))

    limited = _base_project()
    limited['rows'][0]['allowedChoices'] = 1
    limited['rows'][0]['objects'].append(make_entity(limited, 'choice', {
        'id': 'probe-second', 'title': 'Replacement', 'index': 1,
    }))
    originals.append(('row_cap_replacement', limited, [
        {'op': 'select', 'id': 'probe-choice'}, {'op': 'select', 'id': 'probe-second'},
    ]))

    repeat = _base_project()
    repeat_choice = repeat['rows'][0]['objects'][0]
    repeat_choice.update({
        'isSelectableMultiple': True, 'isMultipleUseVariable': True,
        'numMultipleTimesMinus': 0, 'numMultipleTimesPluss': 3,
    })
    originals.append(('multiple_choice_selected_twice', repeat, [
        {'op': 'select', 'id': 'probe-choice'}, {'op': 'select', 'id': 'probe-choice'},
    ]))

    gated = _base_project()
    gated['rows'][0]['objects'].insert(0, make_entity(gated, 'choice', {
        'id': 'probe-gate', 'title': 'Gate', 'index': 0,
    }))
    gated['rows'][0]['objects'][1]['index'] = 1
    gated['rows'][0]['objects'][1]['requireds'].append(
        make_entity(gated, 'requirement', {'type': 'id', 'reqId': 'probe-gate'})
    )
    originals.append(('requirement_activation_cleanup', gated, [
        {'op': 'select', 'id': 'probe-gate'},
        {'op': 'select', 'id': 'probe-choice'},
        {'op': 'deselect', 'id': 'probe-gate'},
    ]))

    addon_project = _base_project()
    addon = make_entity(addon_project, 'selectable_addon', {
        'id': 'probe-addon', 'title': 'Selectable Addon',
        'multipleUseVariable': 0, 'isActive': False, 'groups': [],
    }, parent='probe-choice')
    addon_project['rows'][0]['objects'][0]['addons'].append(addon)
    originals.append(('selectable_addon_selected', addon_project, [
        {'op': 'select', 'id': 'probe-choice'},
        {'op': 'select', 'id': 'probe-addon'},
    ]))

    for name, original, actions in originals:
        candidate, receipt = sparsify_project(original)
        if candidate == original or receipt['removed_count'] == 0:
            raise AssertionError(f'{name}: sparse serializer produced no measurable output')
        cases.append({
            'name': name, 'baseline': original, 'candidate': candidate,
            'actions': actions, 'check_requirements': [],
        })
    return cases


def _local_snapshot(sim: Simulator, check_requirements: list[str]) -> dict[str, Any]:
    entities = sim.index.selectables()
    entity_state = {
        ent.id: {'active': sim._active(ent.id), 'multiple': sim._count(ent.id)}
        for ent in entities
    }
    reqs: dict[str, bool] = {}
    for ident in check_requirements:
        ent = sim.index.one(ident, 'choice') or sim.index.one(ident, 'selectable_addon')
        if ent is not None:
            reqs[ident] = sim.req.evaluate(ent.value.get('requireds', []), sim.state)[0]
    return {
        'entities': entity_state,
        'points': {k: float(v) for k, v in sorted(sim.state.points.items())},
        'variables': dict(sorted(sim.state.variables.items())),
        'words': dict(sorted(sim.state.words.items())),
        'rows': {
            ent.id: {
                'currentChoices': int(sim.state.row_counts.get(ent.id, 0)),
                'allowedChoices': int(sim._row_allowed(ent)),
            }
            for ent in sim.index.by_kind.get('row', []) + sim.index.by_kind.get('backpack_row', [])
        },
        'requirements': reqs,
        'buildString': sim.export_build_string(),
    }


def run_local_case(case: dict[str, Any]) -> dict[str, Any]:
    # initializeApp() itself does not perform a clean/reset pass, so avoid the
    # simulator's initial auto-active convenience here. Cases that exercise reset
    # invoke it explicitly, which then queues isAutoActive exactly like Viewer.
    sim = Simulator(case['project'], clean=False)
    for action in case.get('actions', []):
        op = action['op']
        if op == 'select':
            sim.select(str(action['id']))
        elif op == 'deselect':
            sim.deselect(str(action['id']))
        elif op == 'set_point':
            sim.state.points[str(action['id'])] = float(action['value'])
        elif op == 'reset':
            sim.reset()
        else:
            raise ValueError(f'unsupported live parity action: {op}')
    return _local_snapshot(sim, [str(x) for x in case.get('check_requirements', [])])


def local_results() -> dict[str, Any]:
    return {case['name']: run_local_case(case) for case in live_cases()}
