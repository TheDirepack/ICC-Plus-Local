from __future__ import annotations

import json
import random
import subprocess
import sys
from pathlib import Path

from iccplus_tools.editor import make_entity, new_project
from iccplus_tools.simulator import Simulator
from iccplus_tools.upstream_2106 import default_export_bytes, default_project
from iccplus_tools.validation import validate


def project(*choices, points=None, groups=None, variables=None, words=None, global_requirements=None, rows=None):
    if rows is None:
        rows = [{
            'id': 'r', 'index': 0, 'title': 'R', 'titleText': '', 'allowedChoices': 0,
            'currentChoices': 0, 'requireds': [], 'objects': list(choices),
        }]
    return {
        'version': '2.10.7', 'defaultChoiceMaxNum': 99,
        'pointTypes': list(points or []), 'variables': list(variables or []),
        'words': list(words or []), 'groups': list(groups or []),
        'globalRequirements': list(global_requirements or []), 'rows': rows, 'backpack': [],
    }


def choice(ident: str, **extra):
    value = {
        'id': ident, 'index': 0, 'title': ident, 'text': '', 'isActive': False,
        'multipleUseVariable': 0, 'requireds': [], 'scores': [], 'addons': [], 'groups': [],
    }
    value.update(extra)
    return value


def point(ident: str, value: float, **extra):
    data = {'id': ident, 'name': ident, 'startingSum': value, 'initValue': value, 'activatedId': '', 'beforeText': '', 'afterText': ''}
    data.update(extra)
    return data


def test_new_project_is_exact_frozen_default_app():
    assert new_project() == default_project()
    p = new_project()
    assert p['version'] == '2.10.7'
    assert p['backpack'][0]['id'] == 'default_backpack_row'
    # Preserve upstream spelling bugs because project JSON compatibility is literal.
    assert 'barBacktroundImage' in p['styling']
    assert 'reqImgFilterBorderColor' in p['styling']


def test_default_cli_export_is_byte_identical_to_upstream_save_to_disk(tmp_path: Path):
    target = tmp_path / 'project.json'
    result = subprocess.run(
        [sys.executable, '-m', 'iccplus_tools', 'new', str(target)],
        cwd=Path(__file__).resolve().parents[1], text=True, capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    assert target.read_bytes() == default_export_bytes()
    data = json.loads(target.read_text('utf-8'))
    assert data['activated'] == ['']
    assert not target.read_bytes().endswith(b'\n')


def test_creator_structural_ids_match_upstream():
    p = new_project()
    addon = make_entity(p, 'addon', {}, parent='choice_x')
    req = make_entity(p, 'requirement', {})
    score = make_entity(p, 'score', {})
    assert addon['id'] == ''
    assert addon['parentId'] == 'choice_x'
    assert req['id'] == ''
    assert score['idx']
    assert score['id'] == ''




def test_identity_audit_ignores_structural_requirement_and_addon_ids():
    from iccplus_tools.cli import identity_report
    p = project(choice('x', addons=[{
        'id': '', 'title': 'A', 'text': '', 'template': 1, 'addonWidth': 'col-12',
        'image': '', 'requireds': [], 'parentId': 'x',
    }], requireds=[{
        'required': True, 'requireds': [], 'orRequired': [], 'orRequireds': [],
        'id': '', 'type': 'id', 'reqId': 'x', 'reqId1': '', 'reqId2': '',
        'reqId3': '', 'reqPoints': 0, 'showRequired': False, 'operator': '1',
        'afterText': '', 'beforeText': '', 'orNum': 1, 'selNum': 1,
        'selFromOperators': '1', 'more': [],
    }]))
    report = identity_report(p)
    assert report['ok']
    assert report['missing'] == []



def test_creator_backpack_row_uses_upstream_fixed_defaults():
    p = new_project()
    p['defaultRowTemplate'] = 7
    p['defaultRowAllowedChoices'] = 12
    p['defaultRowJustify'] = 'center'
    row = make_entity(p, 'backpack_row', {})
    assert row['isBackpack'] is True
    assert row['objectWidth'] == 'col-md-3'
    assert row['template'] == 1
    assert 'rowJustify' not in row
    assert row['allowedChoices'] == 0
    assert row['isResultRow'] is True
    assert row['isInfoRow'] is True
    assert row['buttonType'] is True
    assert row['buttonId'] == ''
    assert row['buttonText'] == 'Click'
    assert row['buttonRandom'] is False
    assert row['buttonRandomNumber'] == 1


def test_creator_selectable_addon_transition_has_only_upstream_eager_fields():
    p = new_project()
    addon = make_entity(p, 'selectable_addon', {}, parent='choice_x')
    assert addon['isSelectable'] is True
    assert addon['id']
    assert addon['scores'] == []
    assert 'groups' not in addon
    assert 'multipleUseVariable' not in addon
    assert 'isActive' not in addon

def test_validator_rejects_repeat_counter_without_upstream_mode():
    p = project(choice('x', isSelectableMultiple=True, numMultipleTimesMinus=0, numMultipleTimesPluss=9))
    report = validate(p)
    assert any(d['code'] == 'multiple.mode_missing' and d['severity'] == 'error' for d in report['diagnostics'])


def test_malformed_repeat_counter_is_runtime_noop():
    sim = Simulator(project(choice('x', isSelectableMultiple=True, numMultipleTimesMinus=0, numMultipleTimesPluss=9)))
    event = sim.select('x')
    assert event.ok
    assert event.code == 'selection.no_effect'
    assert sim._count('x') == 0
    assert not sim._active('x')


def test_point_backed_repeat_counter_does_not_activate_entity():
    p = project(
        choice('x', isSelectableMultiple=True, multipleScoreId='p', numMultipleTimesMinus=0, numMultipleTimesPluss=3),
        points=[point('p', 1)],
    )
    sim = Simulator(p)
    assert sim.select('x').ok
    assert sim.state.points['p'] == 2
    assert not sim._active('x')
    assert sim.deselect('x').ok
    assert sim.state.points['p'] == 1
    assert not sim._active('x')


def test_repeat_add_to_allow_choice_applies_each_counter_step():
    rows = [
        {'id': 'source_row', 'index': 0, 'title': '', 'titleText': '', 'allowedChoices': 0, 'currentChoices': 0, 'requireds': [], 'objects': [
            choice('x', isSelectableMultiple=True, isMultipleUseVariable=True, numMultipleTimesMinus=0, numMultipleTimesPluss=9,
                   addToAllowChoice=True, idOfAllowChoice=['target_row'], numbAddToAllowChoice=2)
        ]},
        {'id': 'target_row', 'index': 1, 'title': '', 'titleText': '', 'allowedChoices': 1, 'currentChoices': 0, 'requireds': [], 'objects': []},
    ]
    sim = Simulator(project(rows=rows))
    assert sim.select('x', times=2).ok
    assert sim._row_allowed(sim.index.one('target_row', 'row')) == 5
    assert sim.deselect('x').ok
    assert sim._row_allowed(sim.index.one('target_row', 'row')) == 3


def test_repeat_counter_does_not_run_point_modify_effects():
    p = project(
        choice('x', isSelectableMultiple=True, isMultipleUseVariable=True, numMultipleTimesMinus=0, numMultipleTimesPluss=9,
               multiplyPointtypeIsOn=True, pointTypeToMultiply=['p'], multiplyWithThis=2),
        points=[point('p', 5)],
    )
    sim = Simulator(p)
    assert sim.select('x').ok
    assert sim.state.points['p'] == 5


def test_initial_point_modifier_can_cross_below_zero_guard_like_viewer():
    p = project(
        choice('x', setPointtypeIsOn=True, pointTypeToSet=['p'], setWithThis='-2'),
        points=[point('p', 5, belowZeroNotAllowed=True)],
    )
    sim = Simulator(p)
    assert sim.choice_status('x').selectable
    event = sim.select('x')
    assert event.ok
    assert sim.state.points['p'] == -2
    assert sim._active('x')


def test_force_target_uses_javascript_parseint_prefix():
    p = project(
        choice('multi', isSelectableMultiple=True, isMultipleUseVariable=True, numMultipleTimesMinus=0, numMultipleTimesPluss=9),
        choice('source', activateOtherChoice=True, activateThisChoice='multi/ON#2junk'),
    )
    sim = Simulator(p)
    assert sim.select('source').ok
    assert sim._count('multi') == 2


def test_repeated_force_targets_are_not_deduplicated():
    p = project(
        choice('multi', isSelectableMultiple=True, isMultipleUseVariable=True, numMultipleTimesMinus=0, numMultipleTimesPluss=9),
        choice('source', activateOtherChoice=True, activateThisChoice='multi/ON#1,multi/ON#1'),
    )
    sim = Simulator(p)
    assert sim.select('source').ok
    assert sim._count('multi') == 2


def test_negative_forced_repeat_count_preserves_2106_noop_bug():
    p = project(
        choice('multi', isSelectableMultiple=True, isMultipleUseVariable=True, numMultipleTimesMinus=-9, numMultipleTimesPluss=9),
        choice('source', activateOtherChoice=True, activateThisChoice='multi/ON#-2'),
    )
    sim = Simulator(p)
    assert sim.select('source').ok
    assert sim._count('multi') == 0


def test_ordinary_self_deactivation_is_deferred_then_applied():
    p = project(choice('x', deactivateOtherChoice=True, deactivateThisChoice='x'))
    sim = Simulator(p)
    event = sim.select('x')
    assert event.ok
    assert not sim._active('x')


def test_repeat_self_deactivation_uses_only_positive_explicit_count():
    p = project(choice('x', isSelectableMultiple=True, isMultipleUseVariable=True, numMultipleTimesMinus=0, numMultipleTimesPluss=9,
                       deactivateOtherChoice=True, deactivateThisChoice='x/ON#1'))
    sim = Simulator(p)
    assert sim.select('x').ok
    assert sim._count('x') == 0
    assert not sim._active('x')


def test_negative_repeat_counts_cross_zero_and_change_row_occupancy():
    p = project(choice('x', isSelectableMultiple=True, isMultipleUseVariable=True, numMultipleTimesMinus=-2, numMultipleTimesPluss=2))
    sim = Simulator(p)
    assert sim.deselect('x').ok
    assert sim._count('x') == -1
    assert sim._active('x')
    assert sim.state.row_counts['r'] == 1
    assert sim.select('x').ok
    assert sim._count('x') == 0
    assert not sim._active('x')
    assert sim.state.row_counts['r'] == 0




def test_row_capacity_replacement_fully_clears_positive_repeatable():
    p = project(rows=[{
        'id': 'r', 'index': 0, 'title': 'R', 'titleText': '', 'allowedChoices': 1,
        'currentChoices': 0, 'requireds': [], 'objects': [
            choice('multi', isSelectableMultiple=True, isMultipleUseVariable=True, numMultipleTimesMinus=0, numMultipleTimesPluss=9),
            choice('next'),
        ],
    }])
    sim = Simulator(p)
    assert sim.select('multi', times=2).ok
    assert sim._count('multi') == 2
    assert sim.select('next').ok
    assert not sim._active('multi')
    assert sim._active('next')
    assert sim.state.row_counts['r'] == 1


def test_negative_repeat_is_not_row_capacity_replacement_candidate():
    p = project(rows=[{
        'id': 'r', 'index': 0, 'title': 'R', 'titleText': '', 'allowedChoices': 1,
        'currentChoices': 0, 'requireds': [], 'objects': [
            choice('multi', isSelectableMultiple=True, isMultipleUseVariable=True, numMultipleTimesMinus=-2, numMultipleTimesPluss=2),
            choice('next'),
        ],
    }])
    sim = Simulator(p)
    assert sim.deselect('multi').ok
    assert sim._count('multi') == -1
    status = sim.choice_status('next')
    assert not status.selectable
    assert status.would_deselect == []
    assert sim.select('next').ok is False
    assert sim._count('multi') == -1
    assert not sim._active('next')

def test_reset_uses_init_value_and_replays_auto_and_preserved_choices():
    p = project(
        choice('keep', notDeselectedByClean=True),
        choice('auto', isAutoActive=True),
        points=[point('p', 7, initValue=3)],
    )
    sim = Simulator(p)
    assert sim.select('keep').ok
    sim.state.points['p'] = 99
    sim.reset()
    assert sim.state.points['p'] == 3
    assert sim._active('auto')
    assert sim._active('keep')


def test_sel_from_groups_counts_overlap_per_group_membership():
    groups = [
        {'id': 'g1', 'name': 'g1', 'elements': ['a'], 'rowElements': []},
        {'id': 'g2', 'name': 'g2', 'elements': ['a'], 'rowElements': []},
    ]
    req = {'id': '', 'required': True, 'requireds': [], 'orRequired': [], 'orRequireds': [], 'type': 'selFromGroups',
           'reqId': '', 'reqId1': '', 'reqId2': '', 'reqId3': '', 'reqPoints': 0, 'showRequired': False,
           'operator': '1', 'afterText': '', 'beforeText': '', 'orNum': 1, 'selNum': 2,
           'selFromOperators': '2', 'selGroups': ['g1', 'g2'], 'more': []}
    p = project(choice('a'), choice('target', requireds=[req]), groups=groups)
    sim = Simulator(p)
    assert sim.select('a').ok
    assert sim.choice_status('target').selectable


def test_point_compare_preserves_explicit_priority_zero():
    req = {'id': '', 'required': True, 'requireds': [], 'orRequired': [], 'orRequireds': [], 'type': 'pointCompare',
           'reqId': 'a', 'reqId1': 'b', 'reqId2': '', 'reqId3': '', 'reqPoints': 0, 'showRequired': False,
           'operator': '1', 'afterText': '', 'beforeText': '', 'orNum': 1, 'selNum': 1, 'selFromOperators': '1',
           'more': [
               {'operator': '1', 'type': 'points', 'points': 2, 'priority': 0},
               {'operator': '3', 'type': 'points', 'points': 3, 'priority': 1},
           ]}
    p = project(choice('target', requireds=[req]), points=[point('a', 20), point('b', 10)])
    sim = Simulator(p)
    # Source evaluates (10 + 2) * 3 = 36 because explicit priority 0 is valid.
    assert not sim.choice_status('target').selectable


def test_deactivate_direct_list_processes_each_target_in_order():
    p = project(choice('a'), choice('b'), choice('source', deactivateOtherChoice=True, deactivateThisChoice='a,b'))
    sim = Simulator(p)
    assert sim.select('a').ok
    assert sim.select('b').ok
    assert sim.select('source').ok
    assert not sim._active('a')
    assert not sim._active('b')


def test_deactivate_group_expands_members():
    p = project(
        choice('a'), choice('b'), choice('source', deactivateOtherChoice=True, deactivateThisChoice='g'),
        groups=[{'id': 'g', 'name': 'G', 'category': -1, 'elements': ['a', 'b'], 'rowElements': []}],
    )
    sim = Simulator(p)
    assert sim.select('a').ok
    assert sim.select('b').ok
    assert sim.select('source').ok
    assert not sim._active('a')
    assert not sim._active('b')


def test_deactivate_explicit_repeat_count_only_removes_that_many():
    p = project(
        choice('multi', isSelectableMultiple=True, isMultipleUseVariable=True, numMultipleTimesMinus=0, numMultipleTimesPluss=9),
        choice('source', deactivateOtherChoice=True, deactivateThisChoice='multi/ON#2'),
    )
    sim = Simulator(p)
    for _ in range(4):
        assert sim.select('multi').ok
    assert sim.select('source').ok
    assert sim._count('multi') == 2


def test_deactivate_skips_forced_target():
    p = project(
        choice('target'),
        choice('forcer', activateOtherChoice=True, activateThisChoice='target'),
        choice('source', deactivateOtherChoice=True, deactivateThisChoice='target'),
    )
    sim = Simulator(p)
    assert sim.select('forcer').ok
    assert sim._active('target')
    assert sim.select('source').ok
    assert sim._active('target')


def test_target_lists_do_not_trim_whitespace_like_2106():
    p = project(choice('a'), choice('source', deactivateOtherChoice=True, deactivateThisChoice=' a'))
    sim = Simulator(p)
    assert sim.select('a').ok
    assert sim.select('source').ok
    assert sim._active('a')


def test_validator_uses_literal_target_tokens_like_2106():
    p = project(choice('a'), choice('source', deactivateOtherChoice=True, deactivateThisChoice=' a'))
    report = validate(p)
    errors = [d for d in report['diagnostics'] if d['code'] == 'effect.missing_target']
    assert len(errors) == 1
    assert "' a'" in errors[0]['message']


def test_selectable_addon_deselect_parent_matches_viewer():
    parent = choice('parent')
    parent['addons'] = [{
        'id': 'addon', 'title': 'A', 'text': '', 'template': 1, 'addonWidth': 'col-12',
        'image': '', 'requireds': [], 'parentId': 'parent', 'isSelectable': True,
        'scores': [], 'groups': [], 'multipleUseVariable': 0, 'isActive': False,
        'deselectParent': True,
    }]
    p = project(parent)
    sim = Simulator(p)
    assert sim.select('addon').ok
    assert sim._active('parent') and sim._active('addon')
    assert sim.deselect('addon').ok
    assert not sim._active('addon')
    assert not sim._active('parent')


def test_parent_deselect_when_no_addon_waits_for_last_active_addon():
    parent = choice('parent', deselectWhenNoAddon=True)
    parent['addons'] = [
        {'id': 'a1', 'title': 'A1', 'text': '', 'template': 1, 'addonWidth': 'col-12', 'image': '', 'requireds': [], 'parentId': 'parent', 'isSelectable': True, 'scores': [], 'groups': [], 'multipleUseVariable': 0, 'isActive': False},
        {'id': 'a2', 'title': 'A2', 'text': '', 'template': 1, 'addonWidth': 'col-12', 'image': '', 'requireds': [], 'parentId': 'parent', 'isSelectable': True, 'scores': [], 'groups': [], 'multipleUseVariable': 0, 'isActive': False},
    ]
    p = project(parent)
    sim = Simulator(p)
    assert sim.select('a1').ok
    assert sim.select('a2').ok
    assert sim.deselect('a1').ok
    assert sim._active('parent')
    assert sim.deselect('a2').ok
    assert not sim._active('parent')


def test_point_set_runs_after_deactivating_old_mutually_exclusive_preset():
    p = project(
        choice('standard', setPointtypeIsOn=True, pointTypeToSet=['p'], setWithThis='290',
               deactivateOtherChoice=True, deactivateThisChoice='generous'),
        choice('generous', setPointtypeIsOn=True, pointTypeToSet=['p'], setWithThis='370',
               deactivateOtherChoice=True, deactivateThisChoice='standard'),
        points=[point('p', 290)],
    )
    sim = Simulator(p)
    assert sim.select('standard').ok
    assert sim.state.points['p'] == 290
    assert sim.select('generous').ok
    assert not sim._active('standard')
    assert sim._active('generous')
    assert sim.state.points['p'] == 370


def test_creator_row_and_choice_defaults_match_2106_append_factories():
    p = new_project()
    row = make_entity(p, 'row', {})
    assert set(row) == {
        'index','id','title','titleText','debugTitle','objectWidth','image','template',
        'isButtonRow','isResultRow','resultGroupId','isInfoRow','defaultAspectWidth',
        'defaultAspectHeight','allowedChoices','currentChoices','rowJustify','requireds',
        'isEditModeOn','isRequirementOpen','objects','rowDesignGroups',
    }
    assert row['title'] == p['defaultRowTitle']
    assert row['titleText'] == p['defaultRowText']
    assert row['objectWidth'] == p['defaultRowWidth']
    assert row['template'] == p['defaultRowTemplate']
    assert row['allowedChoices'] == p['defaultRowAllowedChoices']
    assert row['rowJustify'] == p['defaultRowJustify']

    ch = make_entity(p, 'choice', {})
    assert set(ch) == {
        'index','id','title','text','debugTitle','image','template','objectWidth','isActive',
        'multipleUseVariable','initMultipleTimesMinus','selectedThisManyTimesProp','requireds',
        'addons','scores','groups','objectDesignGroups',
    }
    assert ch['title'] == p['defaultChoiceTitle']
    assert ch['text'] == p['defaultChoiceText']
    assert ch['template'] == p['defaultChoiceTemplate']
    assert ch['objectWidth'] == p['defaultChoiceWidth']


def test_creator_score_requirement_point_group_variable_word_defaults_match_2106():
    p = new_project()
    sc = make_entity(p, 'score', {})
    assert set(sc) == {'idx','id','value','type','requireds','beforeText','afterText','showScore'}
    assert sc['id'] == '' and sc['value'] == 0 and sc['type'] == ''
    assert sc['beforeText'] == p['defaultBeforePoint'] and sc['afterText'] == p['defaultAfterPoint']
    assert sc['showScore'] == p['defaultUseShowScore']

    req = make_entity(p, 'requirement', {})
    assert set(req) == {
        'required','requireds','orRequired','orRequireds','id','type','reqId','reqId1','reqId2','reqId3',
        'reqPoints','showRequired','operator','afterText','beforeText','orNum','selNum','selFromOperators','more',
    }
    assert req['id'] == '' and req['type'] == 'id' and req['operator'] == '1'
    assert req['orNum'] == 1 and req['selNum'] == 1 and req['selFromOperators'] == '1'

    pt = make_entity(p, 'point', {})
    assert {k: pt[k] for k in ('name','startingSum','initValue','activatedId','beforeText','afterText','category')} == {
        'name':'Point 1','startingSum':0,'initValue':0,'activatedId':'','beforeText':'Point 1:','afterText':'','category':-1,
    }
    group = make_entity(p, 'group', {})
    assert {k: group[k] for k in ('name','category','elements','rowElements')} == {'name':'Group 1','category':-1,'elements':[],'rowElements':[]}
    variable = make_entity(p, 'variable', {})
    assert {k: variable[k] for k in ('isTrue','category')} == {'isTrue':False,'category':-1}
    word = make_entity(p, 'word', {})
    assert {k: word[k] for k in ('replaceText','category')} == {'replaceText':'','category':-1}
    global_req = make_entity(p, 'global_requirement', {})
    assert {k: global_req[k] for k in ('name','category','requireds')} == {'name':'Requirement 1','category':-1,'requireds':[]}


def test_live_parity_fixture_set_is_unique_and_covers_current_core_cases():
    from iccplus_tools.live_parity import live_cases, local_results
    cases = live_cases()
    names = [case['name'] for case in cases]
    assert len(names) == len(set(names))
    assert len(cases) >= 32
    for required in (
        'basic_score_cost', 'below_zero_blocks_score_cost', 'multiply_by_times_one_based',
        'selectable_addon_activates_parent', 'forced_nonselectable_target',
        'forced_allow_deselect', 'requirement_cleanup_after_linked_deactivation',
        'variable_toggle_and_word_change', 'requirement_type_matrix', 'random_activate_all_and_release',
    ):
        assert required in names
    results = local_results()
    assert set(results) == set(names)


def test_live_parity_fixtures_keep_runtime_state_consistent_across_sequences():
    from iccplus_tools.live_parity import live_cases

    def comparable_snapshot(sim: Simulator) -> dict:
        value = sim.snapshot(include_choice_status=False)
        value.pop('events', None)
        return value

    for case_index, case in enumerate(live_cases()):
        ids = [x.id for x in Simulator(case['project']).index.selectables()]
        if not ids:
            continue
        for seed in range(4):
            rng = random.Random(case_index * 1000 + seed)
            sim = Simulator(case['project'], seed=seed)
            for _ in range(12):
                ident = rng.choice(ids)
                if rng.random() < 0.55:
                    sim.select(ident)
                else:
                    sim.deselect(ident)
                assert sim.runtime_state_issues() == [], case['name']
                restored = Simulator.from_state(case['project'], sim.export_state())
                assert comparable_snapshot(restored) == comparable_snapshot(sim), case['name']



def test_native_project_schema_accepts_exact_pinned_default_export():
    from jsonschema import Draft202012Validator
    from iccplus_tools.field_types import json_schema_for_kind
    from iccplus_tools.upstream_2106 import default_export_project

    schema = json_schema_for_kind('project', mode='native')
    errors = list(Draft202012Validator(schema).iter_errors(default_export_project()))
    assert errors == []


def test_generated_choice_types_are_self_contained(tmp_path: Path):
    from iccplus_tools.field_types import python_typeddicts, typescript_declarations

    py_src = python_typeddicts(['choice'], mode='native')
    compile(py_src, '<iccplus-native-types>', 'exec')
    ts_src = typescript_declarations(['choice'], mode='native')
    target = tmp_path / 'types.ts'
    target.write_text(ts_src, encoding='utf-8')
    result = subprocess.run(
        ['tsc', '--noEmit', '--skipLibCheck', '--target', 'ES2020', str(target)],
        text=True, capture_output=True,
    )
    assert result.returncode == 0, result.stderr or result.stdout
