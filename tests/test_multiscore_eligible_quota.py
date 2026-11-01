from __future__ import annotations

import copy
from iccplus_tools.live_parity import live_cases, run_local_case_trace
from iccplus_tools.simulator import Simulator


def _case(name):
    return copy.deepcopy(next(c for c in live_cases() if c['name'] == name))


def test_filtered_multi_score_quota_per_step():
    cases = {
        'quota_multi_score_filtered_21016': [(50,25),(50,25),(45,21),(37,17),(45,21),(37,17)],
        'quota_multi_score_selected_first_21016': [(50,25),(42,21),(34,17),(37,17),(45,21)],
        'quota_multi_score_same_point_21016': [(50,25),(50,25),(41,25),(29,25),(41,25)],
    }
    for name, expected in cases.items():
        case = _case(name)
        sim = Simulator(case['project'])
        assert sim.choice_status('a').unsupported_effects == [], name
        trace = run_local_case_trace(case)
        observed = [(round(step['points']['p'], 6), round(step['points']['q'], 6)) for step in trace]
        assert observed == expected, (name, observed)


def test_multi_score_quota_resume():
    case = _case('quota_multi_score_filtered_21016')
    sim = Simulator(case['project'])
    for action in case['actions'][:3]:
        assert sim.select(action['id']).ok
    restarted = Simulator.from_state(case['project'], sim.export_state())
    for action in case['actions'][3:]:
        for obj in (sim, restarted):
            result = obj.select(action['id']) if action['op'] == 'select' else obj.deselect(action['id'])
            assert result.ok
    assert sim.state.points == restarted.state.points
    assert sim.state.points == {'p': 37.0, 'q': 17.0}


def test_two_discountable_scores_stays_unsupported():
    case = _case('quota_multi_score_same_point_21016')
    c = case['project']['rows'][0]['objects'][1]
    c['scores'][1].pop('isNotDiscountable')
    sim = Simulator(case['project'])
    assert 'discount:quota_on_repeat_or_multi_score_target' in sim.choice_status('a').unsupported_effects
    assert sim._direct_discount_value(sim.index.one('a', 'choice'), c['scores'][0], 8) is None


def test_dynamic_second_score_stays_unsupported():
    case = _case('quota_multi_score_filtered_21016')
    c = case['project']['rows'][0]['objects'][1]
    c['scores'][1]['useExpression'] = True
    sim = Simulator(case['project'])
    assert 'discount:quota_on_repeat_or_multi_score_target' in sim.choice_status('a').unsupported_effects
    assert sim._direct_discount_value(sim.index.one('a', 'choice'), c['scores'][0], 8) is None
