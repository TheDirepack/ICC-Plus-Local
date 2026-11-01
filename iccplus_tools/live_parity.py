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

    # Single-source dynamic discounts: source before purchase, after purchase,
    # then source removal. Each input is tested against pinned Viewer behavior.
    for case_name, actions in (
        ('dynamic_discount_before_purchase_21015', [
            {'op': 'select', 'id': 'coupon'}, {'op': 'select', 'id': 'purchase'},
        ]),
        ('dynamic_discount_after_purchase_21015', [
            {'op': 'select', 'id': 'purchase'}, {'op': 'select', 'id': 'coupon'},
        ]),
        ('dynamic_discount_remove_source_21015', [
            {'op': 'select', 'id': 'purchase'}, {'op': 'select', 'id': 'coupon'},
            {'op': 'deselect', 'id': 'coupon'},
        ]),
        ('dynamic_discount_refund_after_source_21015', [
            {'op': 'select', 'id': 'coupon'}, {'op': 'select', 'id': 'purchase'},
            {'op': 'deselect', 'id': 'purchase'},
        ]),
    ):
        cases.append({
            'name': case_name,
            'check_action_trace': True,
            'project': _project(
                rows=[_row('r', [
                    _choice('coupon', discountOther=True, isDisChoices=True,
                            discountChoices=['purchase'], discountOperator='1', discountValue=2),
                    _choice('purchase', scores=[{
                        'idx': 'discount-score', 'id': 'p', 'value': 8,
                        'requireds': [], 'showScore': True,
                    }]),
                ])],
                points=[_point('p', 20)],
            ),
            'actions': actions,
        })

    # Different native discount operators, integer rounding, clamp and point
    # targeting. These do not introduce discount stacks or count allocation.
    operator_cases = (
        ('discount_half_after_purchase_21015', '3', 0.5, {}, [
            {'op': 'select', 'id': 'purchase'}, {'op': 'select', 'id': 'coupon'},
        ]),
        ('discount_half_before_purchase_21015', '3', 0.5, {}, [
            {'op': 'select', 'id': 'coupon'}, {'op': 'select', 'id': 'purchase'},
        ]),
        ('discount_low_limit_21015', '1', 10, {
            'discountLowLimitIsOn': True, 'discountLowLimit': 3,
        }, [
            {'op': 'select', 'id': 'coupon'}, {'op': 'select', 'id': 'purchase'},
        ]),
        ('discount_point_filter_excludes_21015', '1', 2, {
            'discountPointTypes': ['other'],
        }, [
            {'op': 'select', 'id': 'coupon'}, {'op': 'select', 'id': 'purchase'},
        ]),
        ('discount_fixed_override_21015', '5', 3, {}, [
            {'op': 'select', 'id': 'purchase'}, {'op': 'select', 'id': 'coupon'},
        ]),
    )
    for name, operator, value, extra, actions in operator_cases:
        cases.append({
            'name': name,
            'check_action_trace': True,
            'project': _project(
                rows=[_row('r', [
                    _choice('coupon', discountOther=True, isDisChoices=True,
                            discountChoices=['purchase'], discountOperator=operator,
                            discountValue=value, **extra),
                    _choice('purchase', scores=[{
                        'idx': 'discount-score', 'id': 'p', 'value': 9,
                        'requireds': [], 'showScore': True,
                    }]),
                ])],
                points=[_point('p', 20)],
            ),
            'actions': actions,
        })

    # Native Row and Group targeting use the same single-provider discount
    # calculation but traverse different Viewer targeting paths.
    routed_cases = (
        ('dynamic_discount_row_target_21015', True, [
            {'op': 'select', 'id': 'purchase'}, {'op': 'select', 'id': 'coupon'},
        ]),
        ('dynamic_discount_group_target_21015', False, [
            {'op': 'select', 'id': 'coupon'}, {'op': 'select', 'id': 'purchase'},
        ]),
        ('dynamic_discount_group_remove_21015', False, [
            {'op': 'select', 'id': 'purchase'}, {'op': 'select', 'id': 'coupon'},
            {'op': 'deselect', 'id': 'coupon'},
        ]),
    )
    for name, by_row, actions in routed_cases:
        source = _choice('coupon', discountOther=True, isDisChoices=by_row,
                         discountRows=['purchase-row'] if by_row else [],
                         discountGroups=[] if by_row else ['purchase-group'],
                         discountOperator='1', discountValue=2)
        purchase = _choice('purchase', scores=[{
            'idx': 'discount-score', 'id': 'p', 'value': 8,
            'requireds': [], 'showScore': True,
        }])
        groups = [] if by_row else [{
            'id': 'purchase-group', 'name': 'Discounted Purchases',
            'category': -1, 'elements': ['purchase'], 'rowElements': [],
        }]
        rows = (
            [_row('coupon-row', [source]), _row('purchase-row', [purchase])]
            if by_row else [_row('r', [source, purchase])]
        )
        cases.append({
            'name': name,
            'check_action_trace': True,
            'project': _project(rows=rows, points=[_point('p', 20)], groups=groups),
            'actions': actions,
        })

    # State-dependent multi-provider discount arbitration. Pin both orderings
    # and each transition: two non-stackable providers, compatible stacks, and
    # a stacked provider competing with a non-stackable alternative.
    # Keep these as real Viewer action traces, not assumed formula outputs.
    multi_scenarios = (
        ('multi_nonstack_stronger_21015', False, False, 2, 5, [
            'purchase', 'weak', 'strong']),
        ('multi_nonstack_weaker_21015', False, False, 2, 5, [
            'purchase', 'strong', 'weak']),
        ('multi_nonstack_remove_strong_21015', False, False, 2, 5, [
            'purchase', 'weak', 'strong', '-strong']),
        ('multi_nonstack_remove_weak_21015', False, False, 2, 5, [
            'purchase', 'weak', 'strong', '-weak']),
        ('multi_nonstack_before_purchase_21015', False, False, 2, 5, [
            'weak', 'strong', 'purchase']),
        ('multi_stack_after_purchase_21015', True, True, 2, 3, [
            'purchase', 'weak', 'strong']),
        ('multi_stack_before_purchase_21015', True, True, 2, 3, [
            'weak', 'strong', 'purchase']),
        ('multi_stack_remove_first_21015', True, True, 2, 3, [
            'purchase', 'weak', 'strong', '-weak']),
        ('multi_stack_remove_last_21015', True, True, 2, 3, [
            'purchase', 'weak', 'strong', '-strong']),
        ('multi_mixed_stack_then_single_21015', True, False, 2, 6, [
            'purchase', 'weak', 'strong']),
        ('multi_mixed_single_then_stack_21015', False, True, 6, 2, [
            'purchase', 'weak', 'strong']),
        ('multi_mixed_replace_stack_21015', True, False, 2, 6, [
            'purchase', 'weak', 'strong', '-strong']),
    )
    for name, first_stack, second_stack, first_value, second_value, sequence in multi_scenarios:
        actions = [
            {'op': 'deselect' if token.startswith('-') else 'select',
             'id': token.removeprefix('-')}
            for token in sequence
        ]
        sources = [
            _choice('weak', discountOther=True, isDisChoices=True,
                    discountChoices=['purchase'], discountOperator='1',
                    discountValue=first_value, stackableDiscount=first_stack),
            _choice('strong', discountOther=True, isDisChoices=True,
                    discountChoices=['purchase'], discountOperator='1',
                    discountValue=second_value, stackableDiscount=second_stack),
        ]
        cases.append({
            'name': name,
            'check_action_trace': True,
            'project': _project(
                rows=[_row('r', [
                    *sources,
                    _choice('purchase', scores=[{
                        'idx': 'discount-score', 'id': 'p', 'value': 10,
                        'requireds': [], 'showScore': True,
                    }]),
                ])],
                points=[_point('p', 30)],
            ),
            'actions': actions,
        })

    # Limited-use provider allocation across independent, nonrepeatable
    # purchases. Official Viewer maintains appliedDisChoices and FULL states;
    # these traces establish what really happens before implementing it.
    quota_scenarios = (
        ('quota_one_two_purchases_21015', 1,
         ['coupon', 'a', 'b']),
        ('quota_one_after_two_purchases_21015', 1,
         ['a', 'b', 'coupon']),
        ('quota_one_remove_first_21015', 1,
         ['coupon', 'a', 'b', '-a']),
        ('quota_one_remove_first_then_reselect_21015', 1,
         ['coupon', 'a', 'b', '-a', 'a']),
        ('quota_one_remove_source_21015', 1,
         ['coupon', 'a', 'b', '-coupon']),
        ('quota_two_three_purchases_21015', 2,
         ['coupon', 'a', 'b', 'c']),
        ('quota_two_remove_middle_21015', 2,
         ['coupon', 'a', 'b', 'c', '-b']),
        ('quota_one_purchase_refund_21015', 1,
         ['coupon', 'a', '-a', 'b']),
    )
    for name, limit, sequence in quota_scenarios:
        purchases = [
            _choice(ident, scores=[{
                'idx': f'score-{ident}', 'id': 'p', 'value': 8,
                'requireds': [], 'showScore': True,
            }])
            for ident in ('a', 'b', 'c')
        ]
        coupon = _choice(
            'coupon', discountOther=True, isDisChoices=True,
            discountChoices=['a', 'b', 'c'], discountOperator='1',
            discountValue=3, useDiscountCount=True, discountCount=limit,
        )
        cases.append({
            'name': name,
            'check_action_trace': True,
            'project': _project(
                rows=[_row('r', [coupon, *purchases])],
                points=[_point('p', 50)],
            ),
            'actions': [
                {'op': 'deselect' if token.startswith('-') else 'select',
                 'id': token.removeprefix('-')}
                for token in sequence
            ],
        })

    # Two independent limited-use providers target different Point Types on
    # the *same* multi-Score purchases, exercising concurrent quota accounting
    # without two coupons competing for the same native Score.
    separate_point_quotas = (
        ('dual_independent_quota_coupon_first_21016',
         ['coupon_p', 'coupon_q', 'a', 'b', '-a', 'a']),
        ('dual_independent_quota_purchase_first_21016',
         ['a', 'b', 'coupon_p', 'coupon_q', '-a']),
        ('dual_independent_quota_source_removal_21016',
         ['coupon_q', 'coupon_p', 'a', 'b', '-coupon_p', '-coupon_q', '-a', 'a']),
    )
    for name, sequence in separate_point_quotas:
        purchases = [_choice(ident, scores=[
            {'idx': f'{ident}-p', 'id': 'p', 'value': 10,
             'requireds': [], 'showScore': True},
            {'idx': f'{ident}-q', 'id': 'q', 'value': 7,
             'requireds': [], 'showScore': True},
        ]) for ident in ('a', 'b')]
        coupons = [
            _choice('coupon_p', discountOther=True, isDisChoices=True,
                    discountChoices=['a', 'b'], discountOperator='1',
                    discountValue=3, discountPointTypes=['p'],
                    useDiscountCount=True, discountCount=1),
            _choice('coupon_q', discountOther=True, isDisChoices=True,
                    discountChoices=['a', 'b'], discountOperator='1',
                    discountValue=2, discountPointTypes=['q'],
                    useDiscountCount=True, discountCount=1),
        ]
        cases.append({
            'name': name, 'check_action_trace': True,
            'project': _project(
                rows=[_row('r', [*coupons, *purchases])],
                points=[_point('p', 50), _point('q', 50)]),
            'actions': [
                {'op': 'deselect' if token.startswith('-') else 'select',
                 'id': token.removeprefix('-')}
                for token in sequence
            ],
        })

    # One finite-use coupon targeting precisely one Score on each multi-Score
    # Choice. The remaining Score is unrelated, either due to the Point Type
    # filter or explicit isNotDiscountable; test native per-Score allocation.
    multi_score_quota_cases = (
        ('quota_multi_score_filtered_21016', False,
         ['coupon', 'a', 'b', '-a', 'a']),
        ('quota_multi_score_selected_first_21016', False,
         ['a', 'b', 'coupon', '-a']),
        ('quota_multi_score_same_point_21016', True,
         ['coupon', 'a', 'b', '-a']),
    )
    for name, same_point, sequence in multi_score_quota_cases:
        purchases = [
            _choice(ident, scores=[
                {'idx': f'{ident}-main', 'id': 'p', 'value': 8,
                 'requireds': [], 'showScore': True},
                {'idx': f'{ident}-other', 'id': 'p' if same_point else 'q',
                 'value': 4, 'requireds': [], 'showScore': True,
                 **({'isNotDiscountable': True} if same_point else {})},
            ]) for ident in ('a', 'b')
        ]
        coupon = _choice('coupon', discountOther=True, isDisChoices=True,
                         discountChoices=['a', 'b'], discountOperator='1',
                         discountValue=3, discountPointTypes=['p'],
                         useDiscountCount=True, discountCount=1)
        cases.append({
            'name': name, 'check_action_trace': True,
            'project': _project(rows=[_row('r', [coupon, *purchases])],
                                points=[_point('p', 50), _point('q', 25)]),
            'actions': [
                {'op': 'deselect' if token.startswith('-') else 'select',
                 'id': token.removeprefix('-')}
                for token in sequence
            ],
        })

    # Quota allocation routed via native Rows and Groups: same finite coupon
    # accounting, different source targeting in selectDiscountOther/addCount.
    routed_quota = (
        ('quota_row_two_purchases_21015', True, ['coupon', 'a', 'b']),
        ('quota_row_reallocate_21015', True, ['coupon', 'a', 'b', '-a']),
        ('quota_group_two_purchases_21015', False, ['a', 'b', 'coupon']),
        ('quota_group_reallocate_21015', False, ['coupon', 'a', 'b', '-a']),
    )
    for name, row_target, sequence in routed_quota:
        a = _choice('a', scores=[{
            'idx': 'score-a', 'id': 'p', 'value': 8,
            'requireds': [], 'showScore': True,
        }])
        b = _choice('b', scores=[{
            'idx': 'score-b', 'id': 'p', 'value': 8,
            'requireds': [], 'showScore': True,
        }])
        coupon = _choice(
            'coupon', discountOther=True, isDisChoices=row_target,
            discountRows=['purchases'] if row_target else [],
            discountGroups=[] if row_target else ['discounted'],
            discountOperator='1', discountValue=3,
            useDiscountCount=True, discountCount=1,
        )
        rows = (
            [_row('coupon-row', [coupon]), _row('purchases', [a, b])]
            if row_target else [_row('r', [coupon, a, b])]
        )
        groups = [] if row_target else [{
            'id': 'discounted', 'name': 'Discounted', 'category': -1,
            'elements': ['a', 'b'], 'rowElements': [],
        }]
        cases.append({
            'name': name,
            'check_action_trace': True,
            'project': _project(rows=rows, points=[_point('p', 50)], groups=groups),
            'actions': [
                {'op': 'deselect' if token.startswith('-') else 'select',
                 'id': token.removeprefix('-')}
                for token in sequence
            ],
        })

    # 2.10.16: loadActivated must NOT re-create a missing force-selected
    # Choice when the source permits ordinary deselection.
    for name, allow, actions, by_group in (
        ('restore_allow_deselect_21016', True, [
            {'op': 'select', 'id': 'source'}, {'op': 'deselect', 'id': 'target'},
            {'op': 'load_build', 'value': 'source'},
        ], False),
        ('restore_protected_force_21016', False, [
            {'op': 'select', 'id': 'source'}, {'op': 'load_build', 'value': 'source'},
        ], False),
        ('restore_allow_explicit_target_21016', True, [
            {'op': 'load_build', 'value': 'source,target'},
        ], False),
        ('restore_allow_group_21016', True, [
            {'op': 'load_build', 'value': 'source'},
        ], True),
    ):
        cases.append({
            'name': name, 'check_action_trace': True,
            'project': _project(
                rows=[_row('r', [
                    _choice('source', activateOtherChoice=True,
                            activateThisChoice='g' if by_group else 'target',
                            isAllowDeselect=allow),
                    _choice('target'),
                ])],
                groups=[{'id': 'g', 'name': 'g', 'category': -1,
                         'elements': ['target'], 'rowElements': []}] if by_group else [],
            ),
            'actions': actions,
        })

    # Three-provider source arbitration. Probes capture transition order and
    # refund/point re-pricing; the native Viewer, not formula intuition, defines
    # the expected results. All use fixed Scores and positive subtraction only.
    triple_scenarios = (
        ('triple_nonstack_increasing_21016', (False, False, False), (1, 3, 5),
         ['purchase', 'a', 'b', 'c']),
        ('triple_nonstack_decreasing_21016', (False, False, False), (5, 3, 1),
         ['purchase', 'a', 'b', 'c']),
        ('triple_nonstack_before_purchase_21016', (False, False, False), (1, 3, 5),
         ['a', 'b', 'c', 'purchase']),
        ('triple_nonstack_remove_best_21016', (False, False, False), (1, 3, 5),
         ['purchase', 'a', 'b', 'c', '-c']),
        ('triple_nonstack_remove_weakest_21016', (False, False, False), (1, 3, 5),
         ['purchase', 'a', 'b', 'c', '-a']),
        ('triple_stack_all_21016', (True, True, True), (1, 3, 5),
         ['purchase', 'a', 'b', 'c']),
        ('triple_stack_before_21016', (True, True, True), (1, 3, 5),
         ['a', 'b', 'c', 'purchase']),
        ('triple_stack_remove_middle_21016', (True, True, True), (1, 3, 5),
         ['purchase', 'a', 'b', 'c', '-b']),
        ('triple_stack_remove_first_21016', (True, True, True), (1, 3, 5),
         ['purchase', 'a', 'b', 'c', '-a']),
        ('triple_mixed_single_wins_21016', (True, False, True), (1, 7, 3),
         ['purchase', 'a', 'b', 'c']),
        ('triple_mixed_stack_wins_21016', (True, False, True), (3, 2, 4),
         ['purchase', 'a', 'b', 'c']),
        ('triple_mixed_remove_single_21016', (True, False, True), (1, 7, 3),
         ['purchase', 'a', 'b', 'c', '-b']),
    )
    for name, stack_flags, values, sequence in triple_scenarios:
        sources = [
            _choice(ident, discountOther=True, isDisChoices=True,
                    discountChoices=['purchase'], discountOperator='1',
                    discountValue=amount, stackableDiscount=stacking)
            for ident, amount, stacking in zip('abc', values, stack_flags)
        ]
        purchase = _choice('purchase', scores=[{
            'idx': 'purchase-score', 'id': 'p', 'value': 12,
            'requireds': [], 'showScore': True,
        }])
        cases.append({
            'name': name, 'check_action_trace': True,
            'debug_discounts': name == 'triple_nonstack_remove_best_21016',
            'project': _project(rows=[_row('r', [*sources, purchase])],
                                points=[_point('p', 40)]),
            'actions': [
                {'op': 'deselect' if token.startswith('-') else 'select',
                 'id': token.removeprefix('-')}
                for token in sequence
            ],
        })

    # Four and five compatible stackable fixed-cost sources. These must be
    # compared per action to pinned Chromium, not inferred solely from sums.
    extended_stack_scenarios = (
        ('quad_stack_after_purchase_21016', 'abcd', [1, 2, 3, 4],
         ['purchase', 'a', 'b', 'c', 'd', '-b', '-d', 'b', '-purchase']),
        ('quad_stack_before_purchase_21016', 'abcd', [1, 2, 3, 4],
         ['a', 'b', 'c', 'd', 'purchase', '-c', '-purchase']),
        ('five_stack_refund_reselect_21016', 'abcde', [1, 2, 3, 4, 5],
         ['purchase', 'a', 'b', 'c', 'd', 'e', '-e', '-a', 'e', '-purchase']),
    )
    for name, ids, values, sequence in extended_stack_scenarios:
        coupons = [
            _choice(ident, discountOther=True, isDisChoices=True,
                    discountChoices=['purchase'], discountOperator='1',
                    discountValue=value, stackableDiscount=True)
            for ident, value in zip(ids, values)
        ]
        purchase = _choice('purchase', scores=[{
            'idx': 'purchase-score', 'id': 'p', 'value': 20,
            'requireds': [], 'showScore': True,
        }])
        cases.append({
            'name': name, 'check_action_trace': True,
            'project': _project(rows=[_row('r', [*coupons, purchase])],
                                points=[_point('p', 60)]),
            'actions': [
                {'op': 'deselect' if token.startswith('-') else 'select',
                 'id': token.removeprefix('-')}
                for token in sequence
            ],
        })

    # Follow-up transitions after the official 2.10.16 three-nonstackable
    # strongest-provider-removal quirk. Verify whether its full-price state
    # persists through unrelated actions, refund, and provider changes.
    stale_sequences = (
        ('triple_nonstack_stale_neutral_21016',
         ['purchase', 'a', 'b', 'c', '-c', 'neutral']),
        ('triple_nonstack_stale_remove_middle_21016',
         ['purchase', 'a', 'b', 'c', '-c', '-b']),
        ('triple_nonstack_stale_remove_weak_21016',
         ['purchase', 'a', 'b', 'c', '-c', '-a']),
        ('triple_nonstack_stale_reselect_best_21016',
         ['purchase', 'a', 'b', 'c', '-c', 'c']),
        ('triple_nonstack_stale_refund_21016',
         ['purchase', 'a', 'b', 'c', '-c', '-purchase']),
    )
    for name, sequence in stale_sequences:
        sources = [
            _choice(ident, discountOther=True, isDisChoices=True,
                    discountChoices=['purchase'], discountOperator='1',
                    discountValue=value, stackableDiscount=False)
            for ident, value in zip('abc', (1, 3, 5))
        ]
        purchase = _choice('purchase', scores=[{
            'idx': 'purchase-score', 'id': 'p', 'value': 12,
            'requireds': [], 'showScore': True,
        }])
        cases.append({
            'name': name,
            'check_action_trace': True,
            'project': _project(
                rows=[_row('r', [*sources, purchase, _choice('neutral')])],
                points=[_point('p', 40)],
            ),
            'actions': [
                {'op': 'deselect' if token.startswith('-') else 'select',
                 'id': token.removeprefix('-')}
                for token in sequence
            ],
        })

    # PR review regression: fixed multi-Score purchases aggregate charges by
    # Point ID. A provider can target only one Score, or two Scores can charge
    # the same Point. A fractional raw Score must be floored *before* discount
    # arithmetic when its Point Type does not allow floats.
    accounting_cases = (
        ('review_two_score_point_filter_21016', [
            {'idx': 'sp', 'id': 'p', 'value': 8, 'requireds': [], 'showScore': True},
            {'idx': 'sq', 'id': 'q', 'value': 4, 'requireds': [], 'showScore': True},
        ], ['p'], '1', 2, False, ['purchase', 'coupon', '-coupon']),
        ('review_two_score_before_purchase_21016', [
            {'idx': 'sp', 'id': 'p', 'value': 8, 'requireds': [], 'showScore': True},
            {'idx': 'sq', 'id': 'q', 'value': 4, 'requireds': [], 'showScore': True},
        ], ['p'], '1', 2, False, ['coupon', 'purchase']),
        ('review_two_score_same_point_21016', [
            {'idx': 'sp1', 'id': 'p', 'value': 8, 'requireds': [], 'showScore': True},
            {'idx': 'sp2', 'id': 'p', 'value': 6, 'requireds': [], 'showScore': True},
        ], ['p'], '1', 2, False, ['purchase', 'coupon', '-coupon']),
        ('review_two_score_not_discountable_21016', [
            {'idx': 'sp', 'id': 'p', 'value': 8, 'requireds': [], 'showScore': True},
            {'idx': 'sq', 'id': 'q', 'value': 4, 'requireds': [], 'showScore': True,
             'isNotDiscountable': True},
        ], ['p', 'q'], '1', 2, False, ['purchase', 'coupon', '-coupon']),
        ('review_fractional_float_point_21016', [
            {'idx': 'sp', 'id': 'p', 'value': 8.9, 'requireds': [], 'showScore': True},
        ], ['p'], '2', 0.5, True, ['purchase', 'coupon', 'neutral', '-coupon']),
    )
    for name, scores, point_ids, operator, value, allow_float, sequence in accounting_cases:
        purchase = _choice('purchase', scores=scores)
        coupon = _choice(
            'coupon', discountOther=True, isDisChoices=True,
            discountChoices=['purchase'], discountOperator=operator,
            discountValue=value, discountPointTypes=point_ids,
        )
        cases.append({
            'name': name,
            'check_action_trace': True,
            'project': _project(
                rows=[_row('r', [purchase, coupon, _choice('neutral')])],
                points=[_point('p', 50, allowFloat=allow_float),
                        _point('q', 25, allowFloat=False)],
            ),
            'actions': [
                {'op': 'deselect' if token.startswith('-') else 'select',
                 'id': token.removeprefix('-')} for token in sequence
            ],
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

    # The pre-applied empty-discount test above checks the special refund
    # path. This separate fixture exercises the *other-choice* branch inside
    # selectUpdateScore(): a live coupon changes a previously selected target,
    # creating isChangeDiscount/tmpDisScore before a different Choice triggers
    # its reconciliation. Compare the complete and sparse versions after
    # every activation and refund.
    dynamic = copy.deepcopy(points)
    dynamic['rows'][0]['objects'][0]['scores'][0].update({
        'isChangeDiscount': True, 'tmpDisScore': 2,
    })
    dynamic['rows'][0]['objects'].append(make_entity(dynamic, 'choice', {
        'id': 'probe-discount-source', 'title': 'Discount source', 'index': 1,
        'discountOther': True, 'isDisChoices': True,
        'discountChoices': ['probe-choice'],
        'discountOperator': '1', 'discountValue': 2,
    }))
    originals.append(('dynamic_other_choice_discount_refund', dynamic, [
        {'op': 'select', 'id': 'probe-choice'},
        {'op': 'select', 'id': 'probe-discount-source'},
        {'op': 'deselect', 'id': 'probe-discount-source'},
        {'op': 'deselect', 'id': 'probe-choice'},
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


def run_local_case_trace(case: dict[str, Any]) -> list[dict[str, Any]]:
    """Capture the initial state and each action for official Viewer comparison."""
    sim = Simulator(case['project'], clean=False)
    check = [str(x) for x in case.get('check_requirements', [])]
    snapshots = [_local_snapshot(sim, check)]
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
        elif op == 'load_build':
            sim.load_build_string(str(action['value']))
        else:
            raise ValueError(f'unsupported live parity action: {op}')
        snapshots.append(_local_snapshot(sim, check))
    return snapshots


def run_local_case(case: dict[str, Any]) -> dict[str, Any]:
    return run_local_case_trace(case)[-1]

def local_results() -> dict[str, Any]:
    return {case['name']: run_local_case(case) for case in live_cases()}
