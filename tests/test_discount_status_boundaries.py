from __future__ import annotations

import json
from pathlib import Path

from iccplus_tools.simulator import Simulator

EXAMPLE = Path(__file__).resolve().parents[1] / 'examples' / 'demo_project.json'


def make_project(provider_count: int, *, operator='1', quota=False,
                 repeat=False, multi_score=False):
    project = json.loads(EXAMPLE.read_text())
    target = project['rows'][0]['objects'][0]
    target['scores'] = [{'idx': 'main_score', 'id': 'budget', 'value': 4, 'requireds': []}]
    if repeat:
        target.update(isSelectableMultiple=True, isMultipleUseVariable=True,
                      numMultipleTimesPluss=4)
    if multi_score:
        target['scores'].append({'idx': 'second_score', 'id': 'budget',
                                 'value': 2, 'requireds': []})
    for i in range(provider_count):
        project['rows'][0]['objects'].append({
            'id': f'coupon_{i}', 'title': f'Coupon {i}',
            'discountOther': True, 'isDisChoices': True,
            'discountChoices': [target['id']], 'discountRows': [],
            'discountOperator': operator if i == 0 else '1',
            'discountValue': i + 1, 'useDiscountCount': quota,
            'discountCount': 1, 'scores': [], 'requireds': [],
        })
    return project, target['id']


def test_four_provider_status_is_observational_and_player_safe():
    project, target = make_project(4)
    sim = Simulator(project)
    state_before = sim.snapshot()
    rng_before = sim.rng.getstate()
    assert sim.choice_status(target).unsupported_effects == [
        'discount:four_or_more_providers'
    ]
    assert sim.snapshot() == state_before
    assert sim.rng.getstate() == rng_before
    assert sim.choice_status(target).unsupported_effects == ['discount:four_or_more_providers']
    assert 'discount:four_or_more_providers' not in json.dumps(sim.player_view())


def test_inapplicable_provider_filter_is_excluded():
    project, target = make_project(4)
    for source in project['rows'][0]['objects']:
        if source.get('discountOther'):
            source['discountPointTypes'] = ['other_point']
    assert Simulator(project).choice_status(target).unsupported_effects == []


def test_supported_three_provider_case_keeps_native_charge():
    project, target = make_project(3)
    sim = Simulator(project)
    assert sim.choice_status(target).unsupported_effects == []
    assert sim.select('coupon_0').ok
    assert sim.select(target).ok
    assert sim.state.points['budget'] == 7


def test_competing_operator_and_quota_boundaries():
    project, target = make_project(2, operator='2')
    assert Simulator(project).choice_status(target).unsupported_effects == [
        'discount:multi_provider_nonstandard_offer'
    ]
    project, target = make_project(2, quota=True)
    assert Simulator(project).choice_status(target).unsupported_effects == [
        'discount:competing_quota_or_provider'
    ]
    project, target = make_project(1, quota=True)
    assert Simulator(project).choice_status(target).unsupported_effects == []
    project, target = make_project(1, quota=True, multi_score=True)
    assert Simulator(project).choice_status(target).unsupported_effects == [
        'discount:quota_on_repeat_or_multi_score_target'
    ]


def test_repeatable_and_per_selection_quotas_are_reported():
    project, target = make_project(1, quota=True, repeat=True)
    assert Simulator(project).choice_status(target).unsupported_effects == [
        'discount:dynamic_score_or_repeat',
        'discount:quota_on_repeat_or_multi_score_target',
    ]
    project, target = make_project(1)
    project['rows'][0]['objects'][-1]['countPerSelection'] = True
    assert Simulator(project).choice_status(target).unsupported_effects == [
        'discount:repeatable_or_per_selection_quota'
    ]


def test_multi_provider_nonfinite_offer_is_reported_not_crashed():
    project, target = make_project(2)
    project['rows'][0]['objects'][-1]['discountValue'] = float('inf')
    assert Simulator(project).choice_status(target).unsupported_effects == [
        'discount:multi_provider_nonstandard_offer'
    ]


def test_fractional_score_integer_point_discrepancy_is_diagnostic_only():
    """Native 2.10.16 uses an unfloored Score in later discount deltas.

    Do not mistake the locally floored fixed-cost repricing for Viewer parity.
    The supported float-enabled example has a separate official action trace.
    """
    project, target = make_project(1, operator='2')
    score = project['rows'][0]['objects'][0]['scores'][0]
    score['value'] = 8.9
    source = project['rows'][0]['objects'][-1]
    source['discountValue'] = 0.5
    sim = Simulator(project)
    before = sim.snapshot()
    assert sim.choice_status(target).unsupported_effects == [
        'discount:fractional_score_integer_point'
    ]
    assert sim.snapshot() == before
    assert 'discount:fractional_score_integer_point' not in json.dumps(sim.player_view())

    # No warning on a floating Point Type; that path has Chromium coverage.
    project['pointTypes'][0]['allowFloat'] = True
    assert Simulator(project).choice_status(target).unsupported_effects == []

    # A discount provider targeting a different Point Type cannot influence it.
    project['pointTypes'][0]['allowFloat'] = False
    source['discountPointTypes'] = ['not_budget']
    assert Simulator(project).choice_status(target).unsupported_effects == []

    # Integer Scores have no raw-versus-floored discrepancy.
    source['discountPointTypes'] = ['budget']
    score['value'] = 8
    assert Simulator(project).choice_status(target).unsupported_effects == []


def test_fractional_score_flag_does_not_override_static_discount():
    project, target = make_project(1)
    score = project['rows'][0]['objects'][0]['scores'][0]
    score.update(value=8.9, discountIsOn=True, appliedDiscount=True,
                 discountScore=7)
    assert Simulator(project).choice_status(target).unsupported_effects == []
