from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from iccplus_tools import FIELD_CATALOG, STYLE_FIELD_GROUPS, ProjectEditor, Simulator, apply_operation_script, build_project, capabilities, explore, run_scenario, validate
from iccplus_tools.validation import RUNTIME_EFFECT_FIELDS

ROOT = Path(__file__).resolve().parents[1]
PROJECT = json.loads((ROOT / 'examples/demo_project.json').read_text())
SCENARIO = json.loads((ROOT / 'examples/demo_scenario.json').read_text())


class ToolTests(unittest.TestCase):
    def test_capabilities_are_machine_readable(self):
        value = capabilities()
        self.assertEqual(value['interface'], 'command-line')
        self.assertIn('generate', value['command_kinds'])
        self.assertIn('gate', value['operation_kinds'])
        self.assertIn('choice', value['entity_kinds'])
        self.assertEqual(value['hide_content_codes']['unmet_addon'], '10')
        self.assertTrue(value['write_model']['apply_is_atomic'])

    def test_static_and_runtime_advanced_effect_sets_stay_aligned(self):
        self.assertEqual(RUNTIME_EFFECT_FIELDS, Simulator.ADVANCED)

    def test_field_catalog_has_unique_searchable_native_names(self):
        for kind, fields in FIELD_CATALOG.items():
            self.assertEqual(len(fields), len(set(fields)), kind)
            self.assertTrue(all(isinstance(name, str) and name for name in fields), kind)
        self.assertIn('discountOther', FIELD_CATALOG['choice'])
        self.assertIn('allowedChoices', FIELD_CATALOG['row'])
        self.assertIn('belowZeroNotAllowed', FIELD_CATALOG['point'])
        self.assertIn('reqFilterVisibleIsOn', STYLE_FIELD_GROUPS['filter'])

    def test_operation_schema_accepts_all_json_input_forms(self):
        try:
            import jsonschema
        except ImportError:
            self.skipTest('jsonschema not installed')
        schema = json.loads((ROOT / 'schemas' / 'operation-script.schema.json').read_text())
        operation = {'op': 'update', 'ref': 'sword', 'title': 'Blade'}
        jsonschema.validate(operation, schema)
        jsonschema.validate([operation], schema)
        jsonschema.validate({'operations': [operation]}, schema)

    def test_exported_runtime_state_matches_runtime_schema(self):
        try:
            import jsonschema
        except ImportError:
            self.skipTest('jsonschema not installed')
        schema = json.loads((ROOT / 'schemas' / 'runtime-state.schema.json').read_text())
        sim = Simulator(PROJECT)
        self.assertTrue(sim.select('sword').ok)
        self.assertTrue(sim.select('sharp').ok)
        jsonschema.validate(sim.export_state(include_events=True), schema)

    def test_tool_schema_lists_every_capability_command(self):
        schema = json.loads((ROOT / 'tool.schema.json').read_text())
        value = capabilities()
        self.assertEqual(set(schema['properties']['command']['enum']), set(value['command_kinds']))
        operation_schema = (ROOT / 'schemas' / 'operation-script.schema.json').read_text()
        for op in value['operation_kinds']:
            self.assertIn(f'"const": "{op}"', operation_schema)


    def test_atomic_row_bulk_operations_and_design_import(self):
        project = copy.deepcopy(PROJECT)
        gear = next(row for row in project['rows'] if row['id'] == 'gear')
        gear['objects'][0]['text'] = 'long text here'
        gear['objects'][1]['text'] = 'x'
        gear['objects'][2]['text'] = 'medium'
        script = {
            'operations': [
                {'op': 'row_sort', 'row': 'gear', 'by': 'text-longest'},
                {'op': 'row_copy_choices', 'source': 'gear', 'target': 'element'},
                {'op': 'row_move_choices', 'source': 'onepick', 'target': 'element'},
                {'op': 'design_import', 'target': 'gear', 'design': {
                    'version': '2.10.7',
                    'styling': {'rowMargin': '12', 'barTextSize': 99, 'backgroundColor': '#010203FF'},
                }},
            ]
        }
        updated, result = apply_operation_script(project, script)
        self.assertTrue(result['ok'], result)
        gear2 = next(row for row in updated['rows'] if row['id'] == 'gear')
        element = next(row for row in updated['rows'] if row['id'] == 'element')
        onepick = next(row for row in updated['rows'] if row['id'] == 'onepick')
        self.assertEqual([c['id'] for c in gear2['objects']], ['sword', 'elite', 'shield'])
        self.assertEqual(len(element['objects']), 9)
        self.assertEqual(onepick['objects'], [])
        copied_ids = [c['id'] for c in element['objects'][4:7]]
        self.assertTrue(all(x not in {'sword', 'elite', 'shield'} for x in copied_ids))
        self.assertEqual(element['objects'][-2:][0]['id'], 'a')
        self.assertEqual(element['objects'][-1]['id'], 'b')
        self.assertEqual(gear2['styling']['rowMargin'], 12)
        self.assertNotIn('barTextSize', gear2['styling'])
        self.assertNotIn('backgroundColor', gear2['styling'])

    def test_new_atomic_operations_validate_against_published_schema(self):
        try:
            import jsonschema
        except ImportError:
            self.skipTest('jsonschema not installed')
        schema = json.loads((ROOT / 'schemas' / 'operation-script.schema.json').read_text())
        operations = [
            {'op': 'row_sort', 'row': 'gear', 'by': 'width-biggest'},
            {'op': 'row_copy_choices', 'source': 'gear', 'target': 'element'},
            {'op': 'row_move_choices', 'source': 'onepick', 'target': 'element'},
            {'op': 'design_import', 'target': 'global', 'design': {'version': '2.10.7', 'styling': {'rowMargin': 4}}},
        ]
        jsonschema.validate({'operations': operations}, schema)

    def test_validation(self):
        report = validate(copy.deepcopy(PROJECT))
        self.assertTrue(report['valid'], report)

    def test_points_and_affordability(self):
        sim = Simulator(PROJECT)
        self.assertTrue(sim.select('sword').ok)
        self.assertEqual(sim.state.points['budget'], 6)
        status = sim.choice_status('shield')
        self.assertFalse(status.selectable)
        self.assertTrue(any('below zero' in x for x in status.reasons))

    def test_requirement_gate(self):
        sim = Simulator(PROJECT)
        self.assertFalse(sim.choice_status('elite').selectable)
        sim.select('sword')
        self.assertTrue(sim.choice_status('elite').selectable)

    def test_negative_requirement_and_cleanup(self):
        sim = Simulator(PROJECT)
        sim.select('water')
        self.assertIn('water', sim.snapshot(False)['selected_ids'])
        sim.select('fire')
        selected = sim.snapshot(False)['selected_ids']
        self.assertIn('fire', selected)
        self.assertNotIn('water', selected)

    def test_variable_effect(self):
        sim = Simulator(PROJECT)
        self.assertFalse(sim.choice_status('flagged').selectable)
        sim.select('switcher')
        self.assertTrue(sim.state.variables['flag'])
        self.assertTrue(sim.choice_status('flagged').selectable)
        sim.deselect('switcher')
        self.assertFalse(sim.state.variables['flag'])

    def test_selectable_addon_selects_parent(self):
        sim = Simulator(PROJECT)
        sim.select('sharp')
        self.assertEqual(sim.state.points['budget'], 5)
        self.assertIn('sword', sim.snapshot(False)['selected_ids'])
        self.assertIn('sharp', sim.snapshot(False)['selected_ids'])

    def test_row_capacity_replacement(self):
        sim = Simulator(PROJECT)
        sim.select('a')
        status = sim.choice_status('b')
        self.assertTrue(status.selectable)
        self.assertEqual(status.would_deselect, ['a'])
        sim.select('b')
        selected = sim.snapshot(False)['selected_ids']
        self.assertNotIn('a', selected)
        self.assertIn('b', selected)

    def test_pairwise(self):
        sim = Simulator(PROJECT)
        result = sim.pair('water', 'fire')
        self.assertFalse(result['coexist'])
        self.assertTrue(result['second_survives'])
        self.assertFalse(result['first_survives'])

    def test_explore(self):
        result = explore(PROJECT, max_depth=3, max_states=500)
        self.assertIn('sword', result['reachable_choice_ids'])
        self.assertIn('flagged', result['reachable_choice_ids'])
        self.assertGreater(result['states_visited'], 1)

    def test_scenario(self):
        result = run_scenario(PROJECT, SCENARIO)
        self.assertTrue(result['passed'], result)

    def test_editor_rename_rewrites_requirement(self):
        project = copy.deepcopy(PROJECT)
        editor = ProjectEditor(project)
        editor.rename('sword', 'blade')
        elite = next(x for x in project['rows'][0]['objects'] if x['id'] == 'elite')
        self.assertEqual(elite['requireds'][0]['reqId'], 'blade')
        self.assertEqual(project['groups'][0]['elements'], ['blade'])

    def test_runtime_state_roundtrip_continues_exactly(self):
        sim = Simulator(PROJECT)
        self.assertTrue(sim.select('sword').ok)
        state = sim.export_state()
        restored = Simulator.from_state(PROJECT, state)
        self.assertEqual(restored.snapshot(False)['selected_ids'], ['sword'])
        self.assertEqual(restored.state.points['budget'], 6)
        self.assertTrue(restored.deselect('sword').ok)
        self.assertEqual(restored.state.points['budget'], 10)

    def test_runtime_state_preserves_random_sequence(self):
        project = copy.deepcopy(PROJECT)
        element = next(row for row in project['rows'] if row['id'] == 'element')
        fire = next(choice for choice in element['objects'] if choice['id'] == 'fire')
        switcher = next(choice for choice in element['objects'] if choice['id'] == 'switcher')
        fire['scores'] = [{'idx': 'rf', 'id': 'budget', 'value': 0, 'isRandom': True, 'minValue': 1, 'maxValue': 3, 'requireds': [], 'showScore': True}]
        switcher['scores'] = [{'idx': 'rs', 'id': 'budget', 'value': 0, 'isRandom': True, 'minValue': 1, 'maxValue': 3, 'requireds': [], 'showScore': True}]

        uninterrupted = Simulator(project, seed=77)
        uninterrupted.select('fire')
        saved = uninterrupted.export_state()
        uninterrupted.select('switcher')
        final_a = uninterrupted.snapshot(False)

        restored = Simulator.from_state(project, saved)
        restored.select('switcher')
        final_b = restored.snapshot(False)
        self.assertEqual(final_a['points'], final_b['points'])
        self.assertEqual(final_a['selected_ids'], final_b['selected_ids'])

    def test_runtime_state_rejects_other_project(self):
        sim = Simulator(PROJECT)
        state = sim.export_state()
        changed = copy.deepcopy(PROJECT)
        changed['rows'][0]['title'] = 'Different project revision'
        with self.assertRaises(ValueError):
            Simulator.from_state(changed, state)

    def test_runtime_state_rejects_contradictory_selected_order(self):
        sim = Simulator(PROJECT)
        self.assertTrue(sim.select('sword').ok)
        state = sim.export_state()
        state['runtime']['selected_order'] = []
        with self.assertRaisesRegex(ValueError, 'selected_order does not match active selectables'):
            Simulator.from_state(PROJECT, state)

    def test_runtime_state_rejects_wrong_row_counts(self):
        sim = Simulator(PROJECT)
        self.assertTrue(sim.select('sword').ok)
        state = sim.export_state()
        state['runtime']['row_counts']['gear'] = 0
        with self.assertRaisesRegex(ValueError, 'row_counts do not match active row-counted selections'):
            Simulator.from_state(PROJECT, state)

    def test_runtime_state_rejects_unknown_activation_and_bad_scalar_types(self):
        state = Simulator(PROJECT).export_state()
        state['runtime']['activations']['ghost'] = 0
        with self.assertRaisesRegex(ValueError, 'activations contain unknown IDs'):
            Simulator.from_state(PROJECT, state)

        state = Simulator(PROJECT).export_state()
        state['runtime']['variables']['flag'] = 'false'
        with self.assertRaisesRegex(ValueError, 'must be a boolean'):
            Simulator.from_state(PROJECT, state)

        state = Simulator(PROJECT).export_state()
        state['runtime']['points']['budget'] = float('nan')
        with self.assertRaisesRegex(ValueError, 'must be a finite number'):
            Simulator.from_state(PROJECT, state)

    def test_runtime_state_import_is_transactional_when_rng_or_seed_is_invalid(self):
        baseline = Simulator(PROJECT, seed=11)
        before = baseline.snapshot(False)
        before_state = baseline.export_state()

        donor = Simulator(PROJECT, seed=22)
        self.assertTrue(donor.select('sword').ok)
        broken_rng = donor.export_state()
        broken_rng['rng_state'] = ['not', 'a', 'python', 'rng', 'state']
        with self.assertRaisesRegex(ValueError, 'invalid rng_state'):
            baseline.import_state(broken_rng)
        self.assertEqual(baseline.snapshot(False), before)
        self.assertEqual(baseline.export_state(), before_state)

        broken_seed = donor.export_state()
        broken_seed['seed'] = True
        with self.assertRaisesRegex(ValueError, 'seed must be an integer'):
            baseline.import_state(broken_seed)
        self.assertEqual(baseline.snapshot(False), before)
        self.assertEqual(baseline.export_state(), before_state)

    def test_runtime_state_integrity_report_is_empty_for_normal_run(self):
        sim = Simulator(PROJECT)
        self.assertTrue(sim.select('sword').ok)
        self.assertTrue(sim.select('sharp').ok)
        self.assertEqual(sim.runtime_state_issues(), [])

    def test_apply_actions_for_llm_session(self):
        sim = Simulator(PROJECT)
        results = sim.apply_actions([
            {'action': 'select', 'id': 'sword'},
            {'action': 'status', 'id': 'elite'},
            {'action': 'snapshot', 'include_choice_status': False},
        ])
        self.assertTrue(results[0]['event']['ok'])
        self.assertTrue(results[1]['status']['selectable'])
        self.assertIn('sword', results[2]['snapshot']['selected_ids'])


    def test_selectable_addon_under_nonselectable_parent_matches_viewer(self):
        project = {
            'version': '2.10.7',
            'pointTypes': [],
            'rows': [{
                'id': 'row_test', 'title': 'Test', 'titleText': '', 'allowedChoices': 0, 'requireds': [],
                'objects': [{
                    'id': 'axis_container', 'title': 'Axis', 'text': '', 'isNotSelectable': True,
                    'isCountDisabled': True, 'requireds': [], 'scores': [],
                    'addons': [{
                        'id': 'axis_option_a', 'parentId': 'axis_container', 'isSelectable': True,
                        'title': 'Option A', 'text': '', 'requireds': [], 'scores': [],
                    }],
                }],
            }],
        }
        sim = Simulator(project)
        self.assertFalse(sim.choice_status('axis_container').selectable)
        self.assertTrue(sim.choice_status('axis_option_a').selectable)
        event = sim.select('axis_option_a')
        self.assertTrue(event.ok, event)
        self.assertIn('axis_container', sim.snapshot(False)['selected_ids'])
        self.assertIn('axis_option_a', sim.snapshot(False)['selected_ids'])
        self.assertEqual(sim.state.row_counts['row_test'], 0)

    def test_forced_activation_of_nonselectable_choice_matches_viewer(self):
        project = {
            'version': '2.10.7', 'pointTypes': [],
            'rows': [{'id': 'r', 'title': 'R', 'titleText': '', 'allowedChoices': 0, 'requireds': [], 'objects': [
                {'id': 'target', 'title': 'Target', 'text': '', 'isNotSelectable': True, 'requireds': [], 'scores': [], 'addons': []},
                {'id': 'source', 'title': 'Source', 'text': '', 'requireds': [], 'scores': [], 'addons': [], 'activateOtherChoice': True, 'activateThisChoice': 'target'},
            ]}],
        }
        sim = Simulator(project)
        self.assertTrue(sim.select('source').ok)
        self.assertTrue(sim._active('target'))
        self.assertIn('source', sim.state.forced_by['target'])

        blocked = copy.deepcopy(project)
        blocked['rows'][0]['objects'][1]['isNotActiveUnselectable'] = True
        sim = Simulator(blocked)
        self.assertTrue(sim.select('source').ok)
        self.assertFalse(sim._active('target'))

    def test_allow_deselect_forced_activation_does_not_lock_target(self):
        project = {
            'version': '2.10.7', 'pointTypes': [],
            'rows': [{'id': 'r', 'title': 'R', 'titleText': '', 'allowedChoices': 0, 'requireds': [], 'objects': [
                {'id': 'target', 'title': 'Target', 'text': '', 'isNotSelectable': True, 'requireds': [], 'scores': [], 'addons': []},
                {'id': 'source', 'title': 'Source', 'text': '', 'requireds': [], 'scores': [], 'addons': [], 'activateOtherChoice': True, 'activateThisChoice': 'target', 'isAllowDeselect': True},
            ]}],
        }
        sim = Simulator(project)
        self.assertTrue(sim.select('source').ok)
        self.assertTrue(sim._active('target'))
        self.assertNotIn('target', sim.state.forced_by)
        self.assertTrue(sim.deselect('target').ok)
        self.assertFalse(sim._active('target'))

    def test_auto_active_allow_deselect_provider_leaves_target_editable(self):
        project = {
            'version': '2.10.7', 'pointTypes': [],
            'rows': [{'id': 'r', 'title': 'R', 'titleText': '', 'allowedChoices': 0, 'requireds': [], 'objects': [
                {'id': 'target', 'title': 'Target', 'text': '', 'isNotSelectable': True, 'requireds': [], 'scores': [], 'addons': []},
                {'id': 'source', 'title': 'Source', 'text': '', 'requireds': [], 'scores': [], 'addons': [],
                 'isAutoActive': True, 'activateOtherChoice': True, 'activateThisChoice': 'target', 'isAllowDeselect': True},
            ]}],
        }
        sim = Simulator(project)
        self.assertTrue(sim._active('source'))
        self.assertTrue(sim._active('target'))
        self.assertIn('__auto__', sim.state.forced_by['source'])
        self.assertNotIn('target', sim.state.forced_by)
        self.assertTrue(sim.deselect('target').ok)
        self.assertFalse(sim._active('target'))

    def test_multiply_by_times_is_one_based(self):
        project = {
            'version': '2.10.7',
            'pointTypes': [{'id': 'p', 'name': 'P', 'startingSum': 20, 'belowZeroNotAllowed': True}],
            'rows': [{'id': 'r', 'title': 'R', 'titleText': '', 'allowedChoices': 0, 'requireds': [], 'objects': [{
                'id': 'multi', 'title': 'Multi', 'text': '', 'requireds': [], 'addons': [],
                'isSelectableMultiple': True, 'isMultipleUseVariable': True, 'numMultipleTimesPluss': 5,
                'scores': [{'idx': 's', 'id': 'p', 'value': 2, 'multiplyByTimes': True, 'requireds': [], 'showScore': True}],
            }]}],
        }
        sim = Simulator(project)
        self.assertTrue(sim.select('multi').ok)
        self.assertEqual(sim.state.points['p'], 18)
        self.assertTrue(sim.select('multi').ok)
        self.assertEqual(sim.state.points['p'], 14)
        self.assertTrue(sim.select('multi').ok)
        self.assertEqual(sim.state.points['p'], 8)

    def test_negative_points_are_allowed_unless_point_type_forbids_them(self):
        project = {
            'version': '2.10.7',
            'pointTypes': [{'id': 'p', 'name': 'P', 'startingSum': 1, 'belowZeroNotAllowed': False}],
            'rows': [{'id': 'r', 'title': 'R', 'titleText': '', 'allowedChoices': 0, 'requireds': [], 'objects': [{
                'id': 'x', 'title': 'X', 'text': '', 'requireds': [], 'addons': [],
                'scores': [{'idx': 's', 'id': 'p', 'value': 5, 'requireds': [], 'showScore': True}],
            }]}],
        }
        sim = Simulator(project)
        status = sim.choice_status('x')
        self.assertTrue(status.selectable, status)
        self.assertEqual(status.point_preview['p'], -4)
        self.assertTrue(sim.select('x').ok)
        self.assertEqual(sim.state.points['p'], -4)

    def test_below_zero_not_allowed_is_semantic_and_transactional(self):
        project = {
            'version': '2.10.7',
            'pointTypes': [{'id': 'p', 'name': 'P', 'startingSum': 1, 'belowZeroNotAllowed': True}],
            'rows': [{'id': 'r', 'title': 'R', 'titleText': '', 'allowedChoices': 0, 'requireds': [], 'objects': [{
                'id': 'x', 'title': 'X', 'text': '', 'requireds': [], 'addons': [],
                'scores': [{'idx': 's', 'id': 'p', 'value': 5, 'requireds': [], 'showScore': True}],
            }]}],
        }
        sim = Simulator(project)
        event = sim.select('x')
        self.assertFalse(event.ok)
        self.assertEqual(event.code, 'points.below_zero_not_allowed')
        self.assertEqual(sim.state.points['p'], 1)
        self.assertNotIn('x', sim.state.activations)

    def test_point_requirement_can_reject_result_even_when_negative_balance_is_allowed(self):
        project = {
            'version': '2.10.7',
            'pointTypes': [{'id': 'p', 'name': 'P', 'startingSum': 1, 'belowZeroNotAllowed': False}],
            'rows': [{'id': 'r', 'title': 'R', 'titleText': '', 'allowedChoices': 0, 'requireds': [], 'objects': [{
                'id': 'x', 'title': 'X', 'text': '',
                'requireds': [{'id': 'reqp', 'type': 'points', 'required': True, 'reqId': 'p', 'reqPoints': 0, 'operator': '2'}],
                'addons': [], 'scores': [{'idx': 's', 'id': 'p', 'value': 2, 'requireds': [], 'showScore': True}],
            }]}],
        }
        sim = Simulator(project)
        self.assertTrue(sim.choice_status('x').selectable)
        event = sim.select('x')
        self.assertTrue(event.ok)
        self.assertEqual(event.code, 'selection.processed')
        self.assertEqual(sim.state.points['p'], 1)
        self.assertFalse(sim._active('x'))

    def test_failed_addon_selection_rolls_back_internal_parent_activation(self):
        project = {
            'version': '2.10.7',
            'pointTypes': [{'id': 'p', 'name': 'P', 'startingSum': 2, 'belowZeroNotAllowed': True}],
            'rows': [{'id': 'r', 'title': 'R', 'titleText': '', 'allowedChoices': 0, 'requireds': [], 'objects': [{
                'id': 'container', 'title': 'Container', 'text': '', 'isNotSelectable': True, 'isCountDisabled': True,
                'requireds': [], 'scores': [{'idx': 'sp', 'id': 'p', 'value': 1, 'requireds': [], 'showScore': True}],
                'addons': [{'id': 'answer', 'parentId': 'container', 'isSelectable': True, 'title': 'Answer', 'text': '', 'requireds': [],
                    'scores': [{'idx': 'sa', 'id': 'p', 'value': 2, 'requireds': [], 'showScore': True}]}],
            }]}],
        }
        sim = Simulator(project)
        event = sim.select('answer')
        self.assertFalse(event.ok)
        self.assertEqual(sim.state.points['p'], 2)
        self.assertFalse(sim._active('container'))
        self.assertFalse(sim._active('answer'))

    def test_player_view_hides_invisible_choices_and_ignores_images(self):
        project = {
            'version': '2.10.7',
            'styling': {'reqFilterVisibleIsOn': True},
            'pointTypes': [],
            'rows': [{'id': 'r', 'title': 'R', 'titleText': 'Description', 'allowedChoices': 0, 'requireds': [], 'objects': [
                {'id': 'hidden', 'title': 'Secret', 'text': 'Do not leak', 'image': 'SECRET_IMAGE',
                 'requireds': [{'id': 'rh', 'type': 'id', 'required': True, 'reqId': 'gate'}], 'scores': [], 'addons': []},
                {'id': 'visible', 'title': 'Visible', 'text': 'Shown', 'image': 'VISIBLE_IMAGE', 'requireds': [], 'scores': [], 'addons': []},
            ]}],
        }
        sim = Simulator(project)
        view = sim.player_view(verbose=True)
        raw = json.dumps(view)
        self.assertNotIn('hidden', [c['id'] for c in view['rows'][0]['choices']])
        self.assertNotIn('Do not leak', raw)
        self.assertNotIn('SECRET_IMAGE', raw)
        self.assertNotIn('VISIBLE_IMAGE', raw)
        event = sim.select('hidden')
        self.assertFalse(event.ok)
        self.assertEqual(event.code, 'visibility.hidden')

    def test_player_view_selected_ids_do_not_leak_selected_filter_hidden_choices(self):
        project = {
            'version': '2.10.7',
            'styling': {'selFilterVisibleIsOn': True},
            'pointTypes': [],
            'rows': [{'id': 'r', 'title': 'R', 'titleText': '', 'allowedChoices': 0, 'requireds': [], 'objects': [{
                'id': 'secret_selected', 'title': 'Secret selected', 'text': 'Hidden after selection',
                'requireds': [], 'scores': [], 'addons': [], 'isAutoActive': True,
            }]}],
        }
        sim = Simulator(project)
        self.assertTrue(sim._active('secret_selected'))
        view = sim.player_view(verbose=True)
        self.assertEqual(view['rows'][0]['choices'], [])
        self.assertNotIn('secret_selected', view['selected_ids'])
        self.assertNotIn('secret_selected', json.dumps(view))

    def test_verbose_player_view_only_returns_requirements_the_viewer_displays(self):
        project = {
            'version': '2.10.7',
            'styling': {'reqFilterVisibleIsOn': False},
            'pointTypes': [],
            'rows': [{'id': 'r', 'title': 'R', 'titleText': '', 'allowedChoices': 0, 'requireds': [], 'objects': [
                {'id': 'secret_gate', 'title': 'Friendly Gate', 'text': '', 'requireds': [], 'scores': [], 'addons': []},
                {'id': 'target', 'title': 'Target', 'text': '', 'scores': [], 'addons': [], 'requireds': [
                    {'id': '', 'type': 'id', 'required': True, 'reqId': 'secret_gate', 'requireds': [],
                     'showRequired': False, 'beforeText': 'HIDDEN PREFIX', 'afterText': 'HIDDEN SUFFIX'},
                    {'id': '', 'type': 'id', 'required': True, 'reqId': 'secret_gate', 'requireds': [],
                     'showRequired': True, 'beforeText': 'Need', 'afterText': 'please'},
                ]},
            ]}],
        }
        sim = Simulator(project)
        view = sim.player_view(verbose=True)
        target = next(c for c in view['rows'][0]['choices'] if c['id'] == 'target')
        raw = json.dumps(target)
        self.assertEqual(target['requirements'], ['Need Friendly Gate please'])
        self.assertNotIn('HIDDEN PREFIX', raw)
        self.assertNotIn('HIDDEN SUFFIX', raw)
        self.assertNotIn('reqId', raw)
        self.assertNotIn('/rows/', raw)
        self.assertEqual(target['selection_errors'], [{'code': 'requirements.unmet', 'message': 'requirements are not met'}])

    def test_verbose_player_view_does_not_leak_forced_provider_ids(self):
        project = {
            'version': '2.10.7', 'pointTypes': [],
            'rows': [{'id': 'r', 'title': 'R', 'titleText': '', 'allowedChoices': 0, 'requireds': [], 'objects': [
                {'id': 'target', 'title': 'Target', 'text': '', 'requireds': [], 'scores': [], 'addons': []},
                {'id': 'hidden_provider', 'title': 'Provider', 'text': '', 'requireds': [], 'scores': [], 'addons': [],
                 'activateOtherChoice': True, 'activateThisChoice': 'target', 'isPrivateStyling': True,
                 'privateFilterIsOn': True, 'styling': {'selFilterVisibleIsOn': True}},
            ]}],
        }
        sim = Simulator(project)
        self.assertTrue(sim.select('hidden_provider').ok)
        view = sim.player_view(verbose=True)
        target = next(c for c in view['rows'][0]['choices'] if c['id'] == 'target')
        self.assertEqual(target['deselection_errors'], [{'code': 'deselection.forced', 'message': 'choice is forced active'}])
        self.assertNotIn('hidden_provider', json.dumps(target))

    def test_verbose_player_view_never_exposes_row_requirement_text_or_internal_hide_flags(self):
        project = {
            'version': '2.10.7',
            'styling': {'reqFilterVisibleIsOn': False},
            'pointTypes': [],
            'rows': [
                {'id': 'gate_row', 'title': 'Gate row', 'titleText': '', 'allowedChoices': 0, 'requireds': [], 'objects': [
                    {'id': 'gate', 'title': 'Gate', 'text': '', 'requireds': [], 'scores': [], 'addons': []},
                ]},
                {'id': 'target_row', 'title': 'Target row', 'titleText': '', 'allowedChoices': 0,
                 'requireds': [{'id': '', 'type': 'id', 'required': True, 'reqId': 'gate', 'requireds': [],
                                'showRequired': True, 'beforeText': 'ROW SECRET', 'afterText': ''}],
                 'objectTitleRemoved': True,
                 'objects': [{'id': 'target', 'title': 'Hidden title', 'text': '', 'requireds': [], 'scores': [], 'addons': []}]},
            ],
        }
        sim = Simulator(project)
        self.assertTrue(sim.select('gate').ok)
        view = sim.player_view(verbose=True)
        row = next(r for r in view['rows'] if r['id'] == 'target_row')
        raw = json.dumps(row)
        self.assertNotIn('ROW SECRET', raw)
        self.assertNotIn('requirements', row)
        self.assertNotIn('requirements_met', row)
        self.assertNotIn('row_hidden_content_flags', raw)
        self.assertNotIn('objectTitleRemoved', raw)

    def test_player_view_semantic_errors_never_echo_unmapped_internal_messages(self):
        sim = Simulator({'version': '2.10.7', 'pointTypes': [], 'rows': []})
        value = sim._player_semantic_errors([{'code': 'future.internal_code', 'message': 'secret_internal_id should never escape'}])
        self.assertEqual(value, [{'code': 'future.internal_code', 'message': 'action is not available'}])
        self.assertNotIn('secret_internal_id', json.dumps(value))

    def test_player_view_sanitizes_row_capacity_without_row_id(self):
        project = {
            'version': '2.10.7', 'pointTypes': [],
            'rows': [{
                'id': 'secret_row_id', 'title': 'Pick one', 'titleText': '', 'allowedChoices': 1, 'requireds': [],
                'objects': [
                    {'id': 'a', 'title': 'A', 'text': '', 'selectOnce': True, 'requireds': [], 'scores': [], 'addons': []},
                    {'id': 'b', 'title': 'B', 'text': '', 'requireds': [], 'scores': [], 'addons': []},
                ],
            }],
        }
        sim = Simulator(project)
        self.assertTrue(sim.select('a').ok)
        view = sim.player_view(verbose=True)
        b = next(c for r in view['rows'] for c in r['choices'] if c['id'] == 'b')
        self.assertEqual(b['selection_errors'], [{'code': 'row.capacity', 'message': 'the row has reached its selection limit'}])
        self.assertNotIn('secret_row_id', json.dumps(b['selection_errors']))

    def test_player_view_does_not_expose_below_zero_configuration_flag(self):
        project = {
            'version': '2.10.7',
            'pointTypes': [{'id': 'p', 'name': 'Budget', 'startingSum': 3, 'belowZeroNotAllowed': True}],
            'rows': [],
        }
        view = Simulator(project).player_view(verbose=True)
        self.assertEqual(view['points'], [{'id': 'p', 'name': 'Budget', 'value': 3}])
        self.assertNotIn('below_zero_not_allowed', json.dumps(view))

    def test_player_view_replaces_word_placeholders_like_viewer(self):
        project = {
            'version': '2.10.7',
            'pointTypes': [{'id': 'budget_token', 'name': 'Budget', 'startingSum': 7, 'belowZeroNotAllowed': False, 'allowFloat': False}],
            'words': [
                {'id': 'budget_token', 'replaceText': 'wrong'},
                {'id': 'multi_token', 'replaceText': 'wrong'},
                {'id': 'name_token', 'replaceText': 'Alice'},
            ],
            'rows': [{'id': 'r', 'title': 'Budget budget_token', 'titleText': 'Hello name_token', 'allowedChoices': 0, 'requireds': [], 'objects': [
                {'id': 'multi_token', 'title': 'Count multi_token', 'text': '', 'requireds': [], 'scores': [], 'addons': [],
                 'isSelectableMultiple': True, 'isMultipleUseVariable': True, 'numMultipleTimesPluss': 5},
            ]}],
        }
        sim = Simulator(project)
        self.assertTrue(sim.select('multi_token').ok)
        view = sim.player_view(verbose=True)
        self.assertEqual(view['rows'][0]['title'], 'Budget 7')
        self.assertEqual(view['rows'][0]['description'], 'Hello Alice')
        self.assertEqual(view['rows'][0]['choices'][0]['title'], 'Count 1')

    def test_image_hide_codes_are_not_carried_as_gameplay_state(self):
        project = {
            'version': '2.10.7', 'pointTypes': [],
            'rows': [
                {'id': 'control', 'title': 'Control', 'titleText': '', 'allowedChoices': 0, 'requireds': [], 'objects': [{
                    'id': 'hider', 'title': 'Hider', 'text': '', 'requireds': [], 'scores': [], 'addons': [],
                    'isContentHidden': True, 'hiddenContentsRow': ['target'], 'hiddenContentsType': ['2', '7'],
                }]},
                {'id': 'target', 'title': 'Target', 'titleText': 'Row text', 'allowedChoices': 0, 'requireds': [], 'objects': []},
            ],
        }
        sim = Simulator(project)
        self.assertTrue(sim.select('hider').ok)
        flags = sim.state.hidden_content['target']
        self.assertEqual(flags, {'textIsRemoved'})
        self.assertNotIn('Image', json.dumps(sim.export_state()))

    def test_runtime_content_hiding_is_reflected_in_verbose_player_view(self):
        project = {
            'version': '2.10.7',
            'pointTypes': [{'id': 'p', 'name': 'P', 'startingSum': 10, 'belowZeroNotAllowed': False}],
            'rows': [
                {'id': 'control', 'title': 'Control', 'titleText': '', 'allowedChoices': 0, 'requireds': [], 'objects': [{
                    'id': 'hider', 'title': 'Hider', 'text': '', 'requireds': [], 'scores': [], 'addons': [],
                    'isContentHidden': True, 'hiddenContentsRow': ['target_row'], 'hiddenContentsType': ['1','3','4'],
                }]},
                {'id': 'target_row', 'title': 'Target row', 'titleText': '', 'allowedChoices': 0, 'requireds': [], 'objects': [{
                    'id': 'target', 'title': 'Target title', 'text': 'Target description', 'requireds': [], 'addons': [],
                    'scores': [{'idx': 'st', 'id': 'p', 'value': 1, 'requireds': [], 'showScore': True}],
                }]},
            ],
        }
        sim = Simulator(project)
        before = next(c for r in sim.player_view(verbose=True)['rows'] if r['id'] == 'target_row' for c in r['choices'] if c['id'] == 'target')
        self.assertEqual(before['title'], 'Target title')
        self.assertEqual(before['description'], 'Target description')
        self.assertIn('scores', before)
        self.assertTrue(sim.select('hider').ok)
        after = next(c for r in sim.player_view(verbose=True)['rows'] if r['id'] == 'target_row' for c in r['choices'] if c['id'] == 'target')
        self.assertNotIn('title', after)
        self.assertNotIn('description', after)
        self.assertNotIn('scores', after)

    def test_auto_active_defaults_are_applied_and_locked(self):
        project = {
            'version': '2.10.7', 'pointTypes': [],
            'rows': [{'id': 'r', 'title': 'R', 'titleText': '', 'allowedChoices': 0, 'requireds': [], 'objects': [{
                'id': 'default', 'title': 'Default', 'text': '', 'requireds': [], 'scores': [], 'addons': [],
                'isAutoActive': True,
            }]}],
        }
        sim = Simulator(project)
        self.assertTrue(sim._active('default'))
        self.assertIn('__auto__', sim.state.forced_by['default'])
        event = sim.deselect('default')
        self.assertFalse(event.ok)
        self.assertEqual(event.code, 'deselection.forced')
        self.assertEqual(sim.state.events[-1].code, 'deselection.forced')

    def test_point_bar_visibility_matches_viewer_gate(self):
        project = {
            'version': '2.10.7',
            'pointTypes': [
                {'id': 'shown', 'name': 'Shown', 'startingSum': -2, 'belowZeroNotAllowed': False},
                {'id': 'gated', 'name': 'Gated', 'startingSum': 4, 'belowZeroNotAllowed': False,
                 'isNotShownPointBar': True, 'activatedId': 'gate'},
            ],
            'rows': [{'id': 'r', 'title': 'R', 'titleText': '', 'allowedChoices': 0, 'requireds': [], 'objects': [{
                'id': 'gate', 'title': 'Gate', 'text': '', 'requireds': [], 'scores': [], 'addons': [],
            }]}],
        }
        sim = Simulator(project)
        self.assertEqual([p['id'] for p in sim.player_view()['points']], ['shown'])
        self.assertTrue(sim.select('gate').ok)
        self.assertEqual([p['id'] for p in sim.player_view()['points']], ['shown', 'gated'])
        self.assertEqual(sim.player_view()['points'][0]['value'], -2)

    def test_forced_activation_of_already_active_target_registers_provider(self):
        project = {
            'version': '2.10.7', 'pointTypes': [],
            'rows': [{'id': 'r', 'title': 'R', 'titleText': '', 'allowedChoices': 0, 'requireds': [], 'objects': [
                {'id': 'target', 'title': 'Target', 'text': '', 'requireds': [], 'scores': [], 'addons': []},
                {'id': 'source', 'title': 'Source', 'text': '', 'requireds': [], 'scores': [], 'addons': [],
                 'activateOtherChoice': True, 'activateThisChoice': 'target'},
            ]}],
        }
        sim = Simulator(project)
        self.assertTrue(sim.select('target').ok)
        self.assertTrue(sim.select('source').ok)
        self.assertIn('source', sim.state.forced_by['target'])
        blocked = sim.deselect('target')
        self.assertFalse(blocked.ok)
        self.assertEqual(blocked.code, 'deselection.forced')
        self.assertTrue(sim.deselect('source').ok)
        self.assertFalse(sim._active('target'))

    def test_bare_forced_multi_target_does_not_add_a_selection(self):
        project = {
            'version': '2.10.7', 'pointTypes': [],
            'rows': [{'id': 'r', 'title': 'R', 'titleText': '', 'allowedChoices': 0, 'requireds': [], 'objects': [
                {'id': 'multi', 'title': 'Multi', 'text': '', 'requireds': [], 'scores': [], 'addons': [],
                 'isSelectableMultiple': True, 'isMultipleUseVariable': True, 'numMultipleTimesPluss': 5},
                {'id': 'source', 'title': 'Source', 'text': '', 'requireds': [], 'scores': [], 'addons': [],
                 'activateOtherChoice': True, 'activateThisChoice': 'multi'},
            ]}],
        }
        sim = Simulator(project)
        self.assertTrue(sim.select('source').ok)
        self.assertFalse(sim._active('multi'))
        self.assertEqual(sim._count('multi'), 0)

    def test_action_script_stops_after_first_invalid_player_action(self):
        project = {
            'version': '2.10.7', 'pointTypes': [],
            'rows': [{'id': 'r', 'title': 'R', 'titleText': '', 'allowedChoices': 0, 'requireds': [], 'objects': [
                {'id': 'blocked', 'title': 'Blocked', 'text': '', 'requireds': [], 'scores': [], 'addons': [], 'isNotSelectable': True},
                {'id': 'later', 'title': 'Later', 'text': '', 'requireds': [], 'scores': [], 'addons': []},
            ]}],
        }
        sim = Simulator(project)
        results = sim.apply_actions([
            {'action': 'select', 'id': 'blocked'},
            {'action': 'select', 'id': 'later'},
        ])
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0]['event']['ok'])
        self.assertFalse(sim._active('later'))

    def test_generate_compact_project_fragment(self):
        fragment = {
            'version': '2.10.7',
            'pointTypes': [{'id': 'budget', 'name': 'Budget', 'startingSum': 10, 'belowZeroNotAllowed': True}],
            'rows': [{
                'id': 'row-main',
                'title': 'Main',
                'allowedChoices': 1,
                'choices': [{
                    'id': 'choice-a',
                    'title': 'A',
                    'scores': [{'idx': 'score-a', 'id': 'budget', 'value': 2}],
                }],
            }],
        }
        project = build_project(fragment)
        self.assertTrue(validate(project)['valid'])
        self.assertEqual(project['rows'][0]['objects'][0]['index'], 0)
        self.assertEqual(project['rows'][0]['objects'][0]['scores'][0]['beforeText'], 'Cost:')

    def test_operation_results_are_snapshots_not_live_references(self):
        updated, result = apply_operation_script(PROJECT, {'operations': [
            {'op': 'update', 'ref': 'sword', 'title': 'First'},
            {'op': 'update', 'ref': 'sword', 'text': 'Second mutation'},
        ]})
        self.assertTrue(result['ok'], result)
        self.assertEqual(result['results'][0]['value']['title'], 'First')
        self.assertNotEqual(result['results'][0]['value'].get('text'), 'Second mutation')
        self.assertEqual(__import__('iccplus_tools').ProjectIndex(updated).one('sword', 'choice').value['text'], 'Second mutation')

    def test_batch_operation_script_updates_by_id(self):
        script = {
            'operations': [
                {'op': 'update', 'reference': 'sword', 'kind': 'choice', 'values': {'title': 'Longsword'}},
                {'op': 'add', 'kind': 'score', 'parent': 'sword', 'values': {'idx': 'extra-cost', 'id': 'budget', 'value': 1}},
                {'op': 'rename', 'old': 'elite', 'new': 'veteran'},
                {'op': 'assert', 'pointer': '/rows/0/objects/0/title', 'equals': 'Longsword'},
            ]
        }
        updated, result = apply_operation_script(PROJECT, script)
        self.assertTrue(result['ok'], result)
        self.assertTrue(result['validation']['valid'], result)
        idx = __import__('iccplus_tools').ProjectIndex(updated)
        self.assertEqual(idx.one('sword', 'choice').value['title'], 'Longsword')
        self.assertIsNotNone(idx.one('veteran', 'choice'))
        self.assertIsNotNone(idx.one('extra-cost', 'score'))


    def test_operation_shorthand_supports_inline_fields_and_singular_targets(self):
        script = {'operations': [
            {'op': 'update', 'ref': 'sword', 'title': 'Blade'},
            {'op': 'gate', 'source': 'sword', 'target': 'flagged'},
            {'op': 'score_many', 'target': 'elite', 'point': 'budget', 'value': 4},
        ]}
        updated, result = apply_operation_script(PROJECT, script)
        self.assertTrue(result['ok'], result)
        idx = __import__('iccplus_tools').ProjectIndex(updated)
        self.assertEqual(idx.one('sword', 'choice').value['title'], 'Blade')
        self.assertTrue(any(r.get('reqId') == 'sword' for r in idx.one('flagged', 'choice').value['requireds']))
        self.assertEqual([s['value'] for s in idx.one('elite', 'choice').value['scores'] if s.get('id') == 'budget'], [4])

    def test_operation_inline_field_typo_is_rejected_atomically(self):
        script = {'operations': [
            {'op': 'update', 'ref': 'sword', 'title': 'Blade'},
            {'op': 'update', 'ref': 'water', 'titel': 'Typo'},
        ]}
        updated, result = apply_operation_script(PROJECT, script)
        self.assertFalse(result['ok'])
        idx = __import__('iccplus_tools').ProjectIndex(updated)
        self.assertEqual(idx.one('sword', 'choice').value['title'], 'Sword')
        self.assertIn('unknown operation field', result['error'])
        self.assertIn('title', result['error'])

    def test_batch_operation_script_is_atomic_on_error(self):
        script = {
            'operations': [
                {'op': 'update', 'reference': 'sword', 'values': {'title': 'Changed'}},
                {'op': 'update', 'reference': 'missing-choice', 'values': {'title': 'Nope'}},
            ]
        }
        updated, result = apply_operation_script(PROJECT, script)
        self.assertFalse(result['ok'])
        idx = __import__('iccplus_tools').ProjectIndex(updated)
        self.assertEqual(idx.one('sword', 'choice').value['title'], 'Sword')

    def test_batch_upsert_is_idempotent(self):
        script = {
            'operations': [
                {'op': 'upsert', 'kind': 'choice', 'parent': 'gear', 'values': {'id': 'sword', 'title': 'Sword v2'}},
                {'op': 'upsert', 'kind': 'choice', 'parent': 'gear', 'values': {'id': 'new-tool', 'title': 'Tool'}},
            ]
        }
        updated, result = apply_operation_script(PROJECT, script)
        self.assertTrue(result['ok'], result)
        idx = __import__('iccplus_tools').ProjectIndex(updated)
        self.assertEqual(len(idx.find('sword', 'choice')), 1)
        self.assertEqual(idx.one('sword', 'choice').value['title'], 'Sword v2')
        self.assertIsNotNone(idx.one('new-tool', 'choice'))


    def test_generation_assigns_unique_ids_to_nested_entities(self):
        fragment = {
            'pointTypes': [{'name': 'Budget', 'startingSum': 10}],
            'rows': [{
                'title': 'Origins',
                'choices': [{
                    'title': 'Human',
                    'scores': [{'id': 'point_budget', 'value': 1}],
                    'requireds': [{'type': 'points', 'reqId': 'point_budget', 'reqPoints': 0, 'operator': '2'}],
                    'addons': [{'title': 'Note'}],
                }],
            }],
        }
        project = build_project(fragment)
        idx = __import__('iccplus_tools').ProjectIndex(project)
        identity_kinds = {'row','backpack_row','choice','selectable_addon','score','point','variable','word','group','row_design_group','choice_design_group','global_requirement','sound_effect'}
        identities = [e.id for e in idx.entities if e.kind in identity_kinds]
        self.assertEqual(len(identities), len(set(identities)))
        self.assertTrue(all(not x.startswith('@') and x for x in identities))
        self.assertTrue(all(r.value.get('id', '') == '' for r in idx.by_kind.get('requirement', [])))
        self.assertTrue(all(a.value.get('id', '') == '' for a in idx.by_kind.get('addon', [])))
        self.assertTrue(validate(project)['valid'], validate(project))

    def test_generated_identity_stress(self):
        rows = [{
            'title': 'Repeated Row',
            'choices': [{
                'title': 'Repeated Choice',
                'costs': {'budget': 1},
                'requires': ['anchor'],
                'addons': [
                    {'title': 'Repeated Addon'},
                    {'title': 'Repeated Addon', 'isSelectable': True, 'costs': {'budget': 1}, 'requires': ['anchor']},
                ],
            } for _ in range(20)],
        } for _ in range(30)]
        rows[0]['choices'].insert(0, {'id': 'anchor', 'title': 'Anchor'})
        fragment = {
            'pointTypes': [{'id': 'budget', 'name': 'Budget', 'startingSum': 10000}],
            'rows': rows,
        }
        project = build_project(fragment)
        ProjectEditor(project).normalize_and_check()
        idx = __import__('iccplus_tools').ProjectIndex(project)
        identities = [e.id for e in idx.entities if e.kind != 'category']
        self.assertGreater(len(identities), 2000)
        self.assertEqual(len(identities), len(set(identities)))
        self.assertTrue(validate(project)['valid'])


    def test_generation_rejects_duplicate_explicit_ids(self):
        fragment = {
            'rows': [
                {'id': 'same', 'title': 'A'},
                {'id': 'same', 'title': 'B'},
            ]
        }
        with self.assertRaisesRegex(ValueError, 'duplicate explicit ID'):
            build_project(fragment)

    def test_generation_shorthand_costs_requirements_and_pick(self):
        fragment = {
            'pointTypes': [{'id': 'budget', 'name': 'Budget', 'startingSum': 10}],
            'rows': [{
                'id': 'row_origin', 'title': 'Origin', 'pick': 1,
                'choices': [
                    {'id': 'human', 'title': 'Human'},
                    {'id': 'mage', 'title': 'Mage', 'costs': {'budget': 3}, 'requires': ['human'], 'excludes': ['robot']},
                    {'id': 'robot', 'title': 'Robot'},
                ]
            }]
        }
        project = build_project(fragment)
        mage = __import__('iccplus_tools').ProjectIndex(project).one('mage', 'choice').value
        self.assertEqual(project['rows'][0]['allowedChoices'], 1)
        self.assertEqual(mage['scores'][0]['id'], 'budget')
        self.assertEqual(mage['scores'][0]['value'], 3)
        self.assertEqual({(r['required'], r['reqId']) for r in mage['requireds']}, {(True, 'human'), (False, 'robot')})
        self.assertTrue(validate(project)['valid'], validate(project))

    def test_batch_high_level_helpers_are_idempotent(self):
        script = {'operations': [
            {'op': 'require', 'targets': ['elite'], 'source': 'sword'},
            {'op': 'require', 'targets': ['elite'], 'source': 'sword'},
            {'op': 'score_many', 'targets': ['fire', 'water'], 'point': 'budget', 'value': 2},
            {'op': 'score_many', 'targets': ['fire', 'water'], 'point': 'budget', 'value': 3},
            {'op': 'group_members', 'group': 'weapons', 'members': ['sword']},
            {'op': 'group_members', 'group': 'weapons', 'members': ['sword']},
        ]}
        updated, result = apply_operation_script(PROJECT, script)
        self.assertTrue(result['ok'], result)
        idx = __import__('iccplus_tools').ProjectIndex(updated)
        elite = idx.one('elite', 'choice').value
        simple = [r for r in elite['requireds'] if r.get('type') == 'id' and r.get('reqId') == 'sword' and r.get('required') is True]
        self.assertEqual(len(simple), 1)
        for cid in ('fire', 'water'):
            scores = [x for x in idx.one(cid, 'choice').value['scores'] if x.get('id') == 'budget' and not x.get('requireds')]
            self.assertEqual(len(scores), 1)
            self.assertEqual(scores[0]['value'], 3)
        self.assertEqual(idx.one('sword', 'choice').value['groups'].count('weapons'), 1)

    def test_bulk_idempotency_stress(self):
        project = copy.deepcopy(PROJECT)
        project['groups'].append({'id': 'stress_group', 'name': 'Stress', 'elements': [], 'rowElements': []})
        operations = []
        for _ in range(50):
            operations.extend([
                {'op': 'require', 'source': 'sword', 'targets': ['elite']},
                {'op': 'gate', 'source': 'sword', 'targets': ['flagged']},
                {'op': 'score_many', 'point': 'budget', 'value': 2, 'targets': ['elite']},
                {'op': 'group_members', 'group': 'stress_group', 'members': ['gear', 'elite']},
            ])
        once, first = apply_operation_script(project, {'operations': operations})
        self.assertTrue(first['ok'], first)
        twice, second = apply_operation_script(once, {'operations': operations})
        self.assertTrue(second['ok'], second)
        self.assertEqual(once, twice)
        idx = __import__('iccplus_tools').ProjectIndex(twice)
        elite = idx.one('elite', 'choice').value
        simple_sword = [r for r in elite['requireds'] if r.get('type') == 'id' and r.get('reqId') == 'sword' and r.get('required') is True]
        budget_scores = [x for x in elite['scores'] if x.get('id') == 'budget' and not x.get('requireds')]
        self.assertEqual(len(simple_sword), 1)
        self.assertEqual(len(budget_scores), 1)
        self.assertEqual(idx.one('stress_group', 'group').value['elements'], ['elite'])
        self.assertEqual(idx.one('stress_group', 'group').value['rowElements'], ['gear'])


    def test_hide_contents_helper_uses_upstream_codes(self):
        script = {'operations': [{
            'op': 'hide_contents',
            'source': 'sword',
            'rows': ['element', 'onepick'],
            'contents': ['title', 'image', 'text', 'score', 'requirements', 'unselected_addon', 'unmet_addon'],
        }]}
        updated, result = apply_operation_script(PROJECT, script)
        self.assertTrue(result['ok'], result)
        sword = __import__('iccplus_tools').ProjectIndex(updated).one('sword', 'choice').value
        self.assertTrue(sword['isContentHidden'])
        self.assertEqual(sword['hiddenContentsRow'], ['element', 'onepick'])
        self.assertEqual(sword['hiddenContentsType'], ['1', '2', '3', '4', '5', '9', '10'])

    def test_update_many_and_delete_many_are_atomic(self):
        script = {'operations': [
            {'op': 'update_many', 'references': ['fire', 'water'], 'values': {'template': 2}},
            {'op': 'delete_many', 'references': ['a', 'missing']},
        ]}
        updated, result = apply_operation_script(PROJECT, script)
        self.assertFalse(result['ok'])
        idx = __import__('iccplus_tools').ProjectIndex(updated)
        self.assertNotEqual(idx.one('fire', 'choice').value.get('template'), 2)
        self.assertIsNotNone(idx.one('a', 'choice'))

    def test_hidden_until_generation_hides_rows_and_choices(self):
        fragment = {
            'rows': [
                {'id': 'start', 'title': 'Start', 'choices': [{'id': 'unlock', 'title': 'Unlock'}]},
                {
                    'id': 'secret_row', 'title': 'Secret', 'hidden_until': 'unlock',
                    'choices': [{'id': 'secret_choice', 'title': 'Secret choice', 'hidden_until': 'unlock'}],
                },
            ],
        }
        project = build_project(fragment)
        idx = __import__('iccplus_tools').ProjectIndex(project)
        row = idx.one('secret_row', 'row').value
        choice = idx.one('secret_choice', 'choice').value
        self.assertEqual([(r['required'], r['reqId']) for r in row['requireds']], [(True, 'unlock')])
        self.assertEqual([(r['required'], r['reqId']) for r in choice['requireds']], [(True, 'unlock')])
        self.assertTrue(choice['privateFilterIsOn'])
        self.assertTrue(choice['styling']['reqFilterVisibleIsOn'])

    def test_gate_many_is_idempotent_and_can_ungate(self):
        script = {'operations': [
            {'op': 'gate', 'source': 'sword', 'targets': ['element', 'fire', 'water']},
            {'op': 'gate', 'source': 'sword', 'targets': ['element', 'fire', 'water']},
        ]}
        updated, result = apply_operation_script(PROJECT, script)
        self.assertTrue(result['ok'], result)
        idx = __import__('iccplus_tools').ProjectIndex(updated)
        for target in ('element', 'fire', 'water'):
            ent = idx.one(target)
            reqs = [r for r in ent.value['requireds'] if r.get('type') == 'id' and r.get('reqId') == 'sword']
            self.assertEqual(len(reqs), 1)
        self.assertTrue(idx.one('fire', 'choice').value['styling']['reqFilterVisibleIsOn'])

        cleared, result2 = apply_operation_script(updated, {'operations': [
            {'op': 'ungate', 'source': 'sword', 'targets': ['element', 'fire', 'water']},
        ]})
        self.assertTrue(result2['ok'], result2)
        idx2 = __import__('iccplus_tools').ProjectIndex(cleared)
        for target in ('element', 'fire', 'water'):
            self.assertFalse(any(r.get('type') == 'id' and r.get('reqId') == 'sword' for r in idx2.one(target).value['requireds']))
        self.assertNotIn('reqFilterVisibleIsOn', idx2.one('fire', 'choice').value.get('styling', {}))

    def test_operation_script_rejects_duplicate_identity_atomically(self):
        script = {'operations': [
            {'op': 'set', 'pointer': '/rows/0/objects/1/id', 'value': 'sword'},
        ]}
        updated, result = apply_operation_script(PROJECT, script)
        self.assertFalse(result['ok'])
        self.assertEqual(result['stage'], 'identity')
        idx = __import__('iccplus_tools').ProjectIndex(updated)
        self.assertEqual(idx.one('shield', 'choice').id, 'shield')

    def test_group_members_supports_rows_and_choices(self):
        project = copy.deepcopy(PROJECT)
        project['groups'].append({'id': 'mixed_group', 'name': 'Mixed', 'elements': [], 'rowElements': []})
        updated, result = apply_operation_script(project, {'operations': [
            {'op': 'group_members', 'group': 'mixed_group', 'members': ['gear', 'sword']},
        ]})
        self.assertTrue(result['ok'], result)
        idx = __import__('iccplus_tools').ProjectIndex(updated)
        group = idx.one('mixed_group', 'group').value
        self.assertEqual(group['elements'], ['sword'])
        self.assertEqual(group['rowElements'], ['gear'])
        self.assertIn('mixed_group', idx.one('gear', 'row').value['groups'])
        self.assertIn('mixed_group', idx.one('sword', 'choice').value['groups'])

    def test_design_group_members_updates_both_sides(self):
        project = copy.deepcopy(PROJECT)
        project['rowDesignGroups'] = [{'id': 'rdg', 'name': 'Rows', 'activatedId': '', 'elements': [], 'backpackElements': [], 'groupElements': [], 'styling': {}}]
        project['objectDesignGroups'] = [{'id': 'odg', 'name': 'Choices', 'activatedId': '', 'elements': [], 'backpackElements': [], 'groupElements': [], 'styling': {}}]
        updated, result = apply_operation_script(project, {'operations': [
            {'op': 'design_group_members', 'group': 'rdg', 'members': ['gear']},
            {'op': 'design_group_members', 'group': 'odg', 'members': ['sword']},
        ]})
        self.assertTrue(result['ok'], result)
        idx = __import__('iccplus_tools').ProjectIndex(updated)
        self.assertIn('rdg', idx.one('gear', 'row').value['rowDesignGroups'])
        self.assertIn('odg', idx.one('sword', 'choice').value['objectDesignGroups'])
        self.assertEqual(idx.one('rdg', 'row_design_group').value['elements'], ['gear'])
        self.assertEqual(idx.one('odg', 'choice_design_group').value['elements'], ['sword'])

    def test_generation_reconciles_group_elements_to_choice_groups(self):
        fragment = {
            'groups': [{'id': 'group_magic', 'name': 'Magic', 'elements': ['spell_a']}],
            'rows': [{'id': 'row_magic', 'title': 'Magic', 'choices': [{'id': 'spell_a', 'title': 'Spell'}]}],
        }
        project = build_project(fragment)
        editor = ProjectEditor(project)
        editor.normalize_and_check()
        idx = __import__('iccplus_tools').ProjectIndex(project)
        self.assertIn('group_magic', idx.one('spell_a', 'choice').value['groups'])
        self.assertEqual(idx.one('group_magic', 'group').value['elements'], ['spell_a'])


    def test_normalize_dedupes_and_rebuilds_memberships(self):
        project = copy.deepcopy(PROJECT)
        project['groups'].append({'id': 'g2', 'name': 'G2', 'elements': ['shield', 'shield'], 'rowElements': ['gear', 'gear']})
        project['rowDesignGroups'] = [{'id': 'rdg', 'name': 'Rows', 'activatedId': '', 'elements': ['gear', 'gear'], 'backpackElements': [], 'groupElements': [], 'styling': {}}]
        project['objectDesignGroups'] = [{'id': 'odg', 'name': 'Choices', 'activatedId': '', 'elements': ['sword', 'sword'], 'backpackElements': [], 'groupElements': ['g2', 'g2'], 'styling': {}}]
        idx = __import__('iccplus_tools').ProjectIndex(project)
        idx.one('shield', 'choice').value['groups'] = ['g2', 'g2']
        idx.one('gear', 'row').value['groups'] = ['g2', 'g2']
        idx.one('gear', 'row').value['rowDesignGroups'] = ['rdg', 'rdg']
        idx.one('sword', 'choice').value['objectDesignGroups'] = ['odg', 'odg']
        idx.one('g2', 'group').value['designGroups'] = ['odg', 'odg']
        ProjectEditor(project).normalize_and_check()
        idx = __import__('iccplus_tools').ProjectIndex(project)
        self.assertEqual(idx.one('g2', 'group').value['elements'], ['shield'])
        self.assertEqual(idx.one('g2', 'group').value['rowElements'], ['gear'])
        self.assertEqual(idx.one('gear', 'row').value['groups'], ['g2'])
        self.assertEqual(idx.one('rdg', 'row_design_group').value['elements'], ['gear'])
        self.assertEqual(idx.one('odg', 'choice_design_group').value['elements'], ['sword'])
        self.assertEqual(idx.one('odg', 'choice_design_group').value['groupElements'], ['g2'])

    def test_generation_reconciles_design_group_reverse_membership(self):
        fragment = {
            'groups': [{'id': 'g', 'name': 'G'}],
            'rowDesignGroups': [{'id': 'rdg', 'name': 'Rows', 'elements': ['row_a'], 'groupElements': ['g']}],
            'objectDesignGroups': [{'id': 'odg', 'name': 'Choices', 'elements': ['choice_a'], 'groupElements': ['g']}],
            'rows': [{'id': 'row_a', 'title': 'A', 'choices': [{'id': 'choice_a', 'title': 'A'}]}],
        }
        project = build_project(fragment)
        ProjectEditor(project).normalize_and_check()
        idx = __import__('iccplus_tools').ProjectIndex(project)
        self.assertIn('rdg', idx.one('row_a', 'row').value['rowDesignGroups'])
        self.assertIn('odg', idx.one('choice_a', 'choice').value['objectDesignGroups'])
        self.assertIn('rdg', idx.one('g', 'group').value['designGroups'])
        self.assertIn('odg', idx.one('g', 'group').value['designGroups'])
        self.assertEqual(idx.one('rdg', 'row_design_group').value['elements'], ['row_a'])
        self.assertEqual(idx.one('odg', 'choice_design_group').value['elements'], ['choice_a'])

    def test_design_group_members_supports_groups_and_backpack(self):
        project = copy.deepcopy(PROJECT)
        project['groups'].append({'id': 'g2', 'name': 'G2', 'elements': [], 'rowElements': []})
        editor = ProjectEditor(project)
        editor.add('backpack_row', values={'id': 'bag_row', 'title': 'Bag'}, normalize=False)
        editor.add('choice', parent='bag_row', values={'id': 'bag_choice', 'title': 'Bag Choice'}, normalize=False)
        project['rowDesignGroups'] = [{'id': 'rdg', 'name': 'Rows', 'activatedId': '', 'elements': [], 'backpackElements': [], 'groupElements': [], 'styling': {}}]
        project['objectDesignGroups'] = [{'id': 'odg', 'name': 'Choices', 'activatedId': '', 'elements': [], 'backpackElements': [], 'groupElements': [], 'styling': {}}]
        updated, result = apply_operation_script(project, {'operations': [
            {'op': 'design_group_members', 'group': 'rdg', 'members': ['bag_row', 'g2']},
            {'op': 'design_group_members', 'group': 'odg', 'members': ['bag_choice', 'g2']},
        ]})
        self.assertTrue(result['ok'], result)
        idx = __import__('iccplus_tools').ProjectIndex(updated)
        self.assertEqual(idx.one('rdg', 'row_design_group').value['backpackElements'], ['bag_row'])
        self.assertEqual(idx.one('odg', 'choice_design_group').value['backpackElements'], ['bag_choice'])
        self.assertEqual(idx.one('rdg', 'row_design_group').value['groupElements'], ['g2'])
        self.assertEqual(idx.one('odg', 'choice_design_group').value['groupElements'], ['g2'])
        self.assertIn('rdg', idx.one('g2', 'group').value['designGroups'])
        self.assertIn('odg', idx.one('g2', 'group').value['designGroups'])

    def test_validation_warns_on_duplicate_mechanics(self):
        project = copy.deepcopy(PROJECT)
        sword = __import__('iccplus_tools').ProjectIndex(project).one('sword', 'choice').value
        sword['requireds'] = [
            {'id': 'req-one', 'required': True, 'type': 'id', 'reqId': 'fire', 'requireds': [], 'orRequired': [], 'orRequireds': [], 'showRequired': True, 'beforeText': '', 'afterText': ''},
            {'id': 'req-two', 'required': True, 'type': 'id', 'reqId': 'fire', 'requireds': [], 'orRequired': [], 'orRequireds': [], 'showRequired': False, 'beforeText': 'Different display', 'afterText': ''},
        ]
        sword['scores'].append(copy.deepcopy(sword['scores'][0]))
        sword['scores'][-1]['idx'] = 'sword-cost-copy'
        report = validate(project)
        codes = [d['code'] for d in report['diagnostics']]
        self.assertIn('requirement.duplicate_mechanics', codes)
        self.assertIn('score.duplicate_mechanics', codes)
        self.assertTrue(report['valid'])

    def test_validation_warns_on_duplicate_reference_lists(self):
        project = copy.deepcopy(PROJECT)
        group = project['groups'][0]
        group['elements'] = ['sword', 'sword']
        report = validate(project)
        self.assertTrue(any(d['code'] == 'list.duplicate_reference' for d in report['diagnostics']))
        self.assertTrue(report['valid'])

    def test_generation_effects_expand_to_native_fields(self):
        fragment = {
            'pointTypes': [{'id': 'budget', 'name': 'Budget', 'startingSum': 20}],
            'variables': [{'id': 'flag', 'isTrue': False}],
            'words': [{'id': 'name_word', 'replaceText': 'Old'}],
            'soundEffects': [{'id': 'click_sfx', 'name': 'Click', 'audio': '', 'volume': 100, 'pitch': 1, 'isDefault': False, 'onSelected': False, 'onDeselected': False, 'requireds': [], 'groups': []}],
            'groups': [{'id': 'g_targets', 'name': 'Targets'}],
            'rows': [
                {'id': 'row_targets', 'title': 'Targets', 'choices': [
                    {'id': 'target_a', 'title': 'A', 'groups': ['g_targets']},
                    {'id': 'target_b', 'title': 'B', 'groups': ['g_targets']},
                ]},
                {'id': 'row_effects', 'title': 'Effects', 'choices': [{
                    'id': 'controller',
                    'title': 'Controller',
                    'effects': {
                        'activate': ['target_a'],
                        'deactivate': ['target_b'],
                        'hide_contents': {'rows': ['row_targets'], 'contents': ['title', 'unmet_addon']},
                        'row_limit': {'rows': ['row_targets'], 'add': 2},
                        'variables': {'targets': ['flag'], 'mode': 'toggle'},
                        'points': {
                            'multiply': {'targets': ['budget'], 'by': 2},
                            'divide': {'targets': ['budget'], 'by': 2},
                            'set': {'targets': ['budget'], 'to': 7},
                        },
                        'word': {'id': 'name_word', 'on_select': 'New', 'on_deselect': 'Old'},
                        'multiple': {'max': 3, 'min': 0, 'click': True, 'slider': True, 'hide_counter': False},
                        'discount': {'groups': ['g_targets'], 'points': ['budget'], 'operator': 'subtract', 'value': 2, 'stackable': True, 'low_limit': 0},
                        'scroll_to': {'row': 'row_targets'},
                        'template': {'targets': ['target_a'], 'to': 2},
                        'width': {'targets': ['target_a'], 'to': 'col-6'},
                        'sfx': {'select': 'click_sfx'},
                        'delay': {'select': 0.5},
                        'background': {'color': '#112233FF'},
                        'point_bar': {'text': '#FFFFFFFF'},
                        'confirm': True,
                        'selection': {'select_once': True, 'not_searchable': True},
                        'addons': {'show_all': True, 'show_score': True},
                        'bgm': {'id': 'theme_1', 'fade_in': 1.5, 'no_loop': True},
                        'transition': {'color': '#000000FF', 'time': 0.25},
                        'random_weight': 75,
                        'backpack_button_requirement': True,
                        'default_image': 'fallback.webp',
                    },
                }, {
                    'id': 'random_controller', 'title': 'Random',
                    'effects': {'random_activate': {'targets': ['target_a', 'target_b'], 'count': 1}},
                }]},
            ],
        }
        project = build_project(fragment)
        value = __import__('iccplus_tools').ProjectIndex(project).one('controller', 'choice').value
        self.assertTrue(value['activateOtherChoice'])
        self.assertEqual(value['activateThisChoice'], 'target_a')
        self.assertTrue(value['deactivateOtherChoice'])
        self.assertEqual(value['deactivateThisChoice'], 'target_b')
        self.assertEqual(value['hiddenContentsRow'], ['row_targets'])
        self.assertEqual(value['hiddenContentsType'], ['1', '10'])
        self.assertEqual(value['idOfAllowChoice'], ['row_targets'])
        self.assertEqual(value['numbAddToAllowChoice'], 2)
        self.assertEqual(value['changeType'], '3')
        self.assertEqual(value['pointTypeToMultiply'], ['budget'])
        self.assertEqual(value['pointTypeToDivide'], ['budget'])
        self.assertEqual(value['pointTypeToSet'], ['budget'])
        self.assertEqual(value['discountOperator'], '1')
        self.assertEqual(value['discountGroups'], ['g_targets'])
        self.assertTrue(value['isSelectableMultiple'])
        self.assertEqual(value['numMultipleTimesPluss'], 3)
        self.assertEqual(value['sfxIdOnSelect'], 'click_sfx')
        self.assertTrue(value['confirmIsOn'])
        self.assertTrue(value['selectOnce'])
        self.assertTrue(value['isNotSearchable'])
        self.assertTrue(value['showAllAddons'])
        self.assertTrue(value['showScoreInAddon'])
        self.assertEqual(value['bgmId'], 'theme_1')
        self.assertEqual(value['bgmFadeInSec'], 1.5)
        self.assertTrue(value['bgmNoLoop'])
        self.assertTrue(value['isFadeTransition'])
        self.assertEqual(value['fadeTransitionTime'], 0.25)
        self.assertEqual(value['randomWeight'], 75)
        self.assertTrue(value['backpackBtnRequirement'])
        self.assertEqual(value['defaultImage'], 'fallback.webp')
        random_value = __import__('iccplus_tools').ProjectIndex(project).one('random_controller', 'choice').value
        self.assertTrue(random_value['isActivateRandom'])
        self.assertEqual(random_value['numActivateRandom'], 1)
        self.assertEqual(random_value['activateThisChoice'], 'target_a,target_b')

    def test_duplicate_row_effect_expands(self):
        project = build_project({'rows': [
            {'id': 'source_row', 'title': 'Source'},
            {'id': 'controls', 'title': 'Controls', 'choices': [{
                'id': 'clone_it', 'title': 'Clone',
                'effects': {'duplicate_row': {'source': 'source_row', 'after': 'controls'}},
            }]},
        ]})
        value = __import__('iccplus_tools').ProjectIndex(project).one('clone_it', 'choice').value
        self.assertTrue(value['duplicateRow'])
        self.assertEqual(value['duplicateRowId'], 'source_row')
        self.assertEqual(value['duplicateRowPlace'], 'controls')

    def test_selectable_addon_supports_effects(self):
        project = build_project({'rows': [
            {'id': 'r1', 'title': 'R1', 'choices': [{'id': 'a', 'title': 'A'}]},
            {'id': 'r2', 'title': 'R2', 'choices': [{'id': 'parent', 'title': 'Parent', 'addons': [
                {'id': 'addon_fx', 'title': 'FX', 'isSelectable': True, 'effects': {'activate': 'a', 'confirm': True}},
            ]}]},
        ]})
        addon = __import__('iccplus_tools').ProjectIndex(project).one('addon_fx', 'selectable_addon').value
        self.assertTrue(addon['activateOtherChoice'])
        self.assertEqual(addon['activateThisChoice'], 'a')
        self.assertTrue(addon['confirmIsOn'])

    def test_generation_effect_conflict_fails(self):
        fragment = {'rows': [{'id': 'r', 'title': 'R', 'choices': [{
            'id': 'c', 'title': 'C', 'activateOtherChoice': False, 'effects': {'activate': 'other'},
        }]}]}
        with self.assertRaisesRegex(ValueError, 'conflicts with explicit native field'):
            build_project(fragment)

    def test_bulk_selector_update_and_expect(self):
        project = build_project({'rows': [
            {'id': 'row_magic', 'title': 'Magic', 'choices': [
                {'id': 'spell_fire', 'title': 'Fire'}, {'id': 'spell_ice', 'title': 'Ice'}, {'id': 'perk_focus', 'title': 'Focus'},
            ]},
        ]})
        updated, result = apply_operation_script(project, {'operations': [{
            'op': 'update_many',
            'where': {'kind': 'choice', 'row': 'row_magic', 'id_prefix': 'spell_'},
            'expect': 2,
            'template': 2,
        }]})
        self.assertTrue(result['ok'], result)
        idx = __import__('iccplus_tools').ProjectIndex(updated)
        self.assertEqual(idx.one('spell_fire', 'choice').value['template'], 2)
        self.assertEqual(idx.one('spell_ice', 'choice').value['template'], 2)
        self.assertNotEqual(idx.one('perk_focus', 'choice').value['template'], 2)
        self.assertEqual(result['results'][0]['matched_ids'], ['spell_fire', 'spell_ice'])

    def test_bulk_selector_expect_mismatch_is_atomic(self):
        script = {'operations': [
            {'op': 'update', 'ref': 'sword', 'title': 'Changed first'},
            {'op': 'update_many', 'where': {'kind': 'choice', 'row': 'element'}, 'expect': 99, 'template': 4},
        ]}
        updated, result = apply_operation_script(PROJECT, script)
        self.assertFalse(result['ok'])
        self.assertIn('expected 99 matches', result['error'])
        self.assertEqual(__import__('iccplus_tools').ProjectIndex(updated).one('sword', 'choice').value['title'], 'Sword')

    def test_gate_and_effects_support_where_selectors(self):
        project = copy.deepcopy(PROJECT)
        gated, result = apply_operation_script(project, {'operations': [
            {'op': 'gate', 'source': 'sword', 'where': {'kind': 'choice', 'row': 'element'}, 'expect': 4},
            {'op': 'effects', 'where': {'kind': 'choice', 'row': 'element'}, 'expect': 4, 'effects': {'confirm': True}},
        ]})
        self.assertTrue(result['ok'], result)
        idx = __import__('iccplus_tools').ProjectIndex(gated)
        for ent in idx.by_kind['choice']:
            if ent.row_id != 'element':
                continue
            self.assertTrue(ent.value['confirmIsOn'])
            self.assertTrue(any(r.get('reqId') == 'sword' for r in ent.value['requireds']))

    def test_delete_many_selector_is_atomic_with_later_error(self):
        script = {'operations': [
            {'op': 'delete_many', 'where': {'kind': 'choice', 'row': 'onepick'}, 'expect': 2},
            {'op': 'update', 'ref': 'missing', 'title': 'No'},
        ]}
        updated, result = apply_operation_script(PROJECT, script)
        self.assertFalse(result['ok'])
        idx = __import__('iccplus_tools').ProjectIndex(updated)
        self.assertIsNotNone(idx.one('a', 'choice'))
        self.assertIsNotNone(idx.one('b', 'choice'))

    def test_native_build_string_preserves_random_scores(self):
        from iccplus_tools.upstream_2106 import default_project
        project = default_project()
        project['pointTypes'] = [{
            'id': 'p', 'name': 'P', 'startingSum': 20, 'initValue': 20,
            'activatedId': '', 'beforeText': '', 'afterText': '', 'category': -1,
        }]
        project['rows'] = [{
            'index': 0, 'id': 'r', 'title': 'R', 'titleText': '', 'debugTitle': '',
            'objectWidth': 'col-md-3', 'image': '', 'template': 1, 'isButtonRow': False,
            'isResultRow': False, 'resultGroupId': '', 'isInfoRow': False,
            'defaultAspectWidth': 1, 'defaultAspectHeight': 1, 'allowedChoices': 0,
            'currentChoices': 0, 'rowJustify': 'start', 'requireds': [],
            'isEditModeOn': False, 'isRequirementOpen': False, 'rowDesignGroups': [],
            'objects': [{
                'id': 'random_cost', 'index': 0, 'title': 'Random', 'text': '', 'debugTitle': '',
                'image': '', 'template': 1, 'objectWidth': '', 'isActive': False,
                'multipleUseVariable': 0, 'initMultipleTimesMinus': 0,
                'selectedThisManyTimesProp': 0, 'requireds': [], 'addons': [], 'groups': [],
                'objectDesignGroups': [], 'scores': [{
                    'idx': 's', 'id': 'p', 'value': 1, 'requireds': [],
                    'isRandom': True, 'minValue': 2, 'maxValue': 5,
                }],
            }],
        }]
        sim = Simulator(project, seed=1)
        self.assertTrue(sim.select('random_cost').ok)
        build = sim.export_build_string()
        self.assertRegex(build, r'^random_cost/RS#0:[2-5]$')
        restored = Simulator(project, seed=999)
        restored.load_build_string(build)
        self.assertEqual(restored.state.points, sim.state.points)
        self.assertEqual(restored.export_build_string(), build)

    def test_random_activation_is_released_per_repeat(self):
        from iccplus_tools.upstream_2106 import default_project
        project = default_project()
        def choice(ident, **extra):
            value = {
                'id': ident, 'index': 0, 'title': ident, 'text': '', 'debugTitle': '',
                'image': '', 'template': 1, 'objectWidth': '', 'isActive': False,
                'multipleUseVariable': 0, 'initMultipleTimesMinus': 0,
                'selectedThisManyTimesProp': 0, 'requireds': [], 'addons': [],
                'scores': [], 'groups': [], 'objectDesignGroups': [],
            }
            value.update(extra)
            return value
        project['rows'] = [{
            'index': 0, 'id': 'r', 'title': 'R', 'titleText': '', 'debugTitle': '',
            'objectWidth': 'col-md-3', 'image': '', 'template': 1, 'isButtonRow': False,
            'isResultRow': False, 'resultGroupId': '', 'isInfoRow': False,
            'defaultAspectWidth': 1, 'defaultAspectHeight': 1, 'allowedChoices': 0,
            'currentChoices': 0, 'rowJustify': 'start', 'requireds': [],
            'isEditModeOn': False, 'isRequirementOpen': False, 'rowDesignGroups': [],
            'objects': [choice('a'), choice('b'), choice(
                'source', isSelectableMultiple=True, isMultipleUseVariable=True,
                numMultipleTimesMinus=0, numMultipleTimesPluss=3,
                activateOtherChoice=True, activateThisChoice='a,b',
                isActivateRandom=True, numActivateRandom=1,
            )],
        }]
        sim = Simulator(project, seed=1)
        self.assertTrue(sim.select('source').ok)
        self.assertTrue(sim.select('source').ok)
        chosen = [step[0] for step in sim.state.random_activation_ledger['source']]
        self.assertEqual(len(chosen), 2)
        self.assertEqual(set(chosen), {'a', 'b'})
        self.assertTrue(sim.deselect('source').ok)
        selected = sim.snapshot(False)['selected_ids']
        self.assertIn('source', selected)
        self.assertEqual(len([x for x in ('a', 'b') if x in selected]), 1)
        self.assertTrue(sim.deselect('source').ok)
        self.assertEqual(sim.snapshot(False)['selected_ids'], [])

    def test_native_build_string_round_trips_random_activation(self):
        from iccplus_tools.upstream_2106 import default_project
        project = default_project()
        def choice(ident, **extra):
            value = {
                'id': ident, 'index': 0, 'title': ident, 'text': '', 'debugTitle': '',
                'image': '', 'template': 1, 'objectWidth': '', 'isActive': False,
                'multipleUseVariable': 0, 'initMultipleTimesMinus': 0,
                'selectedThisManyTimesProp': 0, 'requireds': [], 'addons': [],
                'scores': [], 'groups': [], 'objectDesignGroups': [],
            }
            value.update(extra)
            return value
        project['rows'] = [{
            'index': 0, 'id': 'r', 'title': 'R', 'titleText': '', 'debugTitle': '',
            'objectWidth': 'col-md-3', 'image': '', 'template': 1, 'isButtonRow': False,
            'isResultRow': False, 'resultGroupId': '', 'isInfoRow': False,
            'defaultAspectWidth': 1, 'defaultAspectHeight': 1, 'allowedChoices': 0,
            'currentChoices': 0, 'rowJustify': 'start', 'requireds': [],
            'isEditModeOn': False, 'isRequirementOpen': False, 'rowDesignGroups': [],
            'objects': [choice('a'), choice('b'), choice(
                'source', activateOtherChoice=True, activateThisChoice='a,b',
                isActivateRandom=True, numActivateRandom=1,
            )],
        }]
        sim = Simulator(project, seed=2)
        self.assertTrue(sim.select('source').ok)
        build = sim.export_build_string()
        self.assertRegex(build, r'^source/RND#[ab],[ab]$')
        restored = Simulator(project, seed=1234)
        restored.load_build_string(build)
        self.assertEqual(restored.snapshot(False)['selected_ids'], sim.snapshot(False)['selected_ids'])
        self.assertEqual(restored.export_build_string(), build)


if __name__ == '__main__':
    unittest.main()
