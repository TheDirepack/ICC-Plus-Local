from __future__ import annotations

from iccplus_tools.live_parity import live_cases, run_local_case_trace
from iccplus_tools.simulator import Simulator


EXPECTED = {
    'dual_independent_quota_coupon_first_21016': [
        (50, 50), (50, 50), (50, 50), (43, 45), (33, 38), (43, 45), (33, 38)
    ],
    'dual_independent_quota_purchase_first_21016': [
        (50, 50), (40, 43), (30, 36), (33, 36), (33, 38), (43, 45)
    ],
    'dual_independent_quota_source_removal_21016': [
        (50, 50), (50, 50), (50, 50), (43, 45), (33, 38), (30, 38),
        (30, 36), (40, 43), (30, 36)
    ],
}


def test_independent_coupons_all_action_checkpoints():
    cases = {case['name']: case for case in live_cases()}
    for name, points in EXPECTED.items():
        case = cases[name]
        sim = Simulator(case['project'])
        assert sim.choice_status('a').unsupported_effects == [], name
        trace = run_local_case_trace(case)
        got = [(round(s['points']['p'], 8), round(s['points']['q'], 8)) for s in trace]
        assert got == points, (name, got)


def test_independent_coupons_resume_and_refund():
    case = next(c for c in live_cases()
                if c['name'] == 'dual_independent_quota_source_removal_21016')
    sim = Simulator(case['project'])
    actions = case['actions']
    for action in actions[:5]:
        event = sim.select(action['id']) if action['op'] == 'select' else sim.deselect(action['id'])
        assert event.ok
    restored = Simulator.from_state(case['project'], sim.export_state())
    for action in actions[5:]:
        for instance in (sim, restored):
            ev = instance.select(action['id']) if action['op'] == 'select' else instance.deselect(action['id'])
            assert ev.ok
    assert restored.state.points == sim.state.points == {'p': 30.0, 'q': 36.0}


def test_two_providers_targeting_same_score_remain_unsupported():
    case = next(c for c in live_cases()
                if c['name'] == 'dual_independent_quota_coupon_first_21016')
    source = next(x for x in case['project']['rows'][0]['objects']
                  if x['id'] == 'coupon_q')
    source['discountPointTypes'] = ['p']
    sim = Simulator(case['project'])
    assert 'discount:competing_quota_or_provider' in sim.choice_status('a').unsupported_effects
    target = sim.index.one('a', 'choice')
    assert sim._direct_discount_value(target, target.value['scores'][0], 10) is None
