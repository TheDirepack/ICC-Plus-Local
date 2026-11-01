from __future__ import annotations

from iccplus_tools.live_parity import live_cases, run_local_case_trace
from iccplus_tools.simulator import Simulator


def test_two_quotas_preliminary_checkpoint_balances():
    expected = {
        'two_quotas_identical_targets': [100, 100, 100, 94, 84, 74, 84, 82, 72, 70],
        'two_quotas_overlapping_targets': [100, 100, 100, 92, 86, 76, 84, 94, 90, 82],
        'two_quotas_purchases_first': [100, 90, 80, 70, 72, 76, 84, 74],
    }
    cases = {case['name']: case for case in live_cases()}
    for name, points in expected.items():
        case = cases[name]
        trace = run_local_case_trace(case)
        assert [round(state['points']['p'], 6) for state in trace] == points, name


def test_two_quotas_state_continuation():
    case = next(case for case in live_cases()
                if case['name'] == 'two_quotas_identical_targets')
    sim = Simulator(case['project'])
    for action in case['actions'][:5]:
        assert sim.select(action['id']).ok
    resumed = Simulator.from_state(case['project'], sim.export_state())
    for action in case['actions'][5:]:
        for replica in (sim, resumed):
            result = replica.select(action['id']) if action['op'] == 'select' else replica.deselect(action['id'])
            assert result.ok
    assert sim.state.points == resumed.state.points
    assert resumed.state.points['p'] == 70


def test_unsupported_paired_quotas_still_reject_stacking_and_repeatable():
    from copy import deepcopy
    case = next(case for case in live_cases()
                if case['name'] == 'two_quotas_identical_targets')
    project = deepcopy(case['project'])
    provider = next(x for x in project['rows'][0]['objects'] if x['id'] == 'weak')
    provider['stackableDiscount'] = True
    target = next(x for x in project['rows'][0]['objects'] if x['id'] == 'a')
    sim = Simulator(project)
    assert sim._direct_discount_value(sim.index.one('a','choice'), target['scores'][0], 10) is None

    provider['stackableDiscount'] = False
    target['isSelectableMultiple'] = True
    sim = Simulator(project)
    assert sim._direct_discount_value(sim.index.one('a','choice'), target['scores'][0], 10) is None
