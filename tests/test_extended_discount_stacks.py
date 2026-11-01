from __future__ import annotations

import copy
from iccplus_tools.live_parity import live_cases, run_local_case_trace
from iccplus_tools.simulator import Simulator


def _case(name):
    return copy.deepcopy(next(x for x in live_cases() if x['name'] == name))


def _gameplay_snapshot(sim):
    return {k: v for k, v in sim.snapshot().items() if k != 'events'}


def test_extended_stack_action_ledger():
    expected = {
        'quad_stack_after_purchase_21016': [60, 40, 41, 43, 46, 50, 48, 44, 46, 60],
        'quad_stack_before_purchase_21016': [60, 60, 60, 60, 60, 50, 47, 60],
        'five_stack_refund_reselect_21016': [60, 40, 41, 43, 46, 50, 55, 50, 49, 54, 60],
    }
    for name, points in expected.items():
        case = _case(name)
        assert Simulator(case['project']).choice_status('purchase').unsupported_effects == []
        assert [round(t['points']['p'], 8) for t in run_local_case_trace(case)] == points, name


def test_extended_stack_state_export_and_continuation():
    case = _case('five_stack_refund_reselect_21016')
    actions = case['actions']
    original = Simulator(case['project'])
    for action in actions[:6]:
        assert original.select(action['id']).ok
    document = original.export_state()
    restored = Simulator.from_state(case['project'], document)
    assert _gameplay_snapshot(restored) == _gameplay_snapshot(original)
    for action in actions[6:]:
        for sim in (original, restored):
            event = sim.select(action['id']) if action['op'] == 'select' else sim.deselect(action['id'])
            assert event.ok, event
    assert _gameplay_snapshot(original) == _gameplay_snapshot(restored)
    assert restored.state.points['p'] == 60


def test_four_nonstack_and_quota_remain_unsupported():
    case = _case('quad_stack_after_purchase_21016')
    project = case['project']
    providers = [x for x in project['rows'][0]['objects'] if x['id'] != 'purchase']
    providers[1]['stackableDiscount'] = False
    assert 'discount:four_or_more_providers' in Simulator(project).choice_status('purchase').unsupported_effects
    providers[1]['stackableDiscount'] = True
    providers[1]['useDiscountCount'] = True
    providers[1]['discountCount'] = 2
    status = Simulator(project).choice_status('purchase').unsupported_effects
    assert 'discount:four_or_more_providers' in status
    assert 'discount:competing_quota_or_provider' in status


def test_fourth_provider_point_filter_keeps_three_eligible():
    case = _case('quad_stack_after_purchase_21016')
    project = case['project']
    fourth = next(x for x in project['rows'][0]['objects'] if x['id'] == 'd')
    fourth['discountPointTypes'] = ['different_point_type']
    assert Simulator(project).choice_status('purchase').unsupported_effects == []
    sim = Simulator(project)
    assert sim.select('purchase').ok
    for ident in 'abcd':
        assert sim.select(ident).ok
    assert sim.state.points['p'] == 46
