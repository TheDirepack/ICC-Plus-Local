"""Result/Group Row card projection from pinned ICC Plus Viewer 2.10.16 AppRow.

Offline simulator/player-view regressions; the official Chromium DOM
differential is a separate gate, not implied by passing this file.
"""
import copy
import json
import unittest
from pathlib import Path

from iccplus_tools.simulator import Simulator

DEMO = json.loads((Path(__file__).resolve().parents[1] / 'examples' / 'demo_project.json').read_text())


def make_project():
    project = copy.deepcopy(DEMO)
    project['rows'].append({
        **copy.deepcopy(project['rows'][0]), 'id': 'result', 'title': 'Result',
        'index': len(project['rows']), 'objects': [], 'isResultRow': True,
        'isGroupRow': False, 'resultGroupId': '',
    })
    project['rows'].append({
        **copy.deepcopy(project['rows'][0]), 'id': 'group_display', 'title': 'Weapons',
        'index': len(project['rows']), 'objects': [], 'isResultRow': False,
        'isGroupRow': True, 'resultGroupId': 'weapons',
    })
    return project


class ViewerProjectedRowTest(unittest.TestCase):
    def test_result_row_tracks_selected_choices_in_source_order(self):
        sim = Simulator(make_project())
        result = next(r for r in sim.player_view()['rows'] if r['id'] == 'result')
        self.assertEqual(result['choice_ids'], [])
        self.assertTrue(sim.select('fire').ok)
        self.assertTrue(sim.select('sword').ok)
        result = next(r for r in sim.player_view()['rows'] if r['id'] == 'result')
        self.assertEqual(result['choice_ids'], ['sword', 'fire'])
        self.assertEqual(result['selected_choice_ids'], ['sword', 'fire'])
        self.assertTrue(sim.deselect('sword').ok)
        result = next(r for r in sim.player_view()['rows'] if r['id'] == 'result')
        self.assertEqual(result['choice_ids'], ['fire'])

    def test_result_row_group_filter_and_is_not_result(self):
        project = make_project()
        project['pointTypes'][0]['startingSum'] = 100
        project['pointTypes'][0]['initValue'] = 100
        project['rows'][0]['objects'][1]['isNotResult'] = True
        project['rows'][0]['resultGroupId'] = 'regional'
        project['rows'][-2]['resultGroupId'] = 'weapons'
        project['rows'][1]['objects'][0]['groups'].append('weapons')
        sim = Simulator(project)
        for choice in ('sword', 'fire', 'shield'):
            self.assertTrue(sim.select(choice).ok, choice)
        ids = next(r['choice_ids'] for r in sim.player_view()['rows'] if r['id'] == 'result')
        self.assertEqual(ids, ['sword', 'fire'])
        # Source Row resultGroupId membership qualifies independently.
        project['rows'][0]['resultGroupId'] = 'weapons'
        sim = Simulator(project)
        self.assertTrue(sim.select('sword').ok)
        ids = next(r['choice_ids'] for r in sim.player_view()['rows'] if r['id'] == 'result')
        self.assertEqual(ids, ['sword'])

    def test_group_row_projects_unselected_choice_and_addon_parent_duplicates(self):
        project = make_project()
        project['groups'][0]['elements'] = ['sharp', 'sword']
        sim = Simulator(project)
        row = next(r for r in sim.player_view(verbose=True)['rows'] if r['id'] == 'group_display')
        self.assertEqual(row['choice_ids'], ['sword', 'sword'])
        self.assertEqual([c['index'] for c in row['choices']], [0, 1])
        self.assertEqual(row['available_choice_ids'], ['sword', 'sword'])
        self.assertTrue(sim.select('sword').ok)
        self.assertTrue(sim.select('sharp').ok)
        row = next(r for r in sim.player_view()['rows'] if r['id'] == 'group_display')
        self.assertEqual(row['choice_ids'], ['sword', 'sword'])

    def test_projected_group_uses_display_row_filter_not_hidden_source_row(self):
        project = make_project()
        project['rows'][0]['requireds'] = [{
            'type': 'id', 'required': True, 'reqId': 'fire', 'operator': '1',
            'requireds': [], 'orRequireds': [], 'orRequired': [],
        }]
        sim = Simulator(project)
        self.assertFalse(sim.row_visible('gear'))
        group = next(r for r in sim.player_view()['rows'] if r['id'] == 'group_display')
        self.assertEqual(group['choice_ids'], ['sword'])
        self.assertTrue(sim.entity_visible('sword'))

        # The group display's private filter overrides the owner row filter.
        project['rows'][0]['requireds'] = []
        project['rows'][0].update(isPrivateStyling=True, privateFilterIsOn=True,
                                  styling={'selFilterVisibleIsOn': True})
        project['rows'][-1].update(isPrivateStyling=True, privateFilterIsOn=True,
                                   styling={'selFilterVisibleIsOn': False})
        sim = Simulator(project)
        self.assertTrue(sim.select('sword').ok)
        visible = sim.player_view()
        gear = next(r for r in visible['rows'] if r['id'] == 'gear')
        group = next(r for r in visible['rows'] if r['id'] == 'group_display')
        self.assertNotIn('sword', gear['choice_ids'])
        self.assertEqual(group['choice_ids'], ['sword'])
        self.assertIn('sword', visible['selected_ids'])

    def test_display_info_row_is_visible_but_not_clickable(self):
        project = make_project()
        project['rows'][-1]['isInfoRow'] = True
        sim = Simulator(project)
        row = next(r for r in sim.player_view(verbose=True)['rows'] if r['id'] == 'group_display')
        self.assertEqual(row['choice_ids'], ['sword'])
        self.assertFalse(row['choices'][0]['can_select'])
        self.assertFalse(row['choices'][0]['can_deselect'])
        self.assertEqual(row['available_choice_ids'], [])
        self.assertIn('sword', sim.player_view()['available_direct_choice_ids'])

    def test_only_info_projection_does_not_enable_player_selection(self):
        project = make_project()
        project['rows'][0]['requireds'] = [{
            'type': 'id', 'required': True, 'reqId': 'fire', 'operator': '1',
            'requireds': [], 'orRequireds': [], 'orRequired': [],
        }]
        project['rows'][-1]['isInfoRow'] = True
        sim = Simulator(project)
        self.assertFalse(sim.row_visible('gear'))
        self.assertTrue(sim.entity_visible('sword'))
        group = next(r for r in sim.player_view()['rows'] if r['id'] == 'group_display')
        self.assertEqual(group['choice_ids'], ['sword'])
        self.assertEqual(group['available_choice_ids'], [])
        self.assertFalse(sim.choice_status('sword').selectable)
        self.assertNotIn('sword', sim.player_view()['available_direct_choice_ids'])
        self.assertEqual(sim.click('sword').code, 'interaction.click_ignored')

    def test_result_row_addons_use_destination_row_flags(self):
        project = make_project()
        sim = Simulator(project)
        self.assertTrue(sim.select('sword').ok)
        row = next(r for r in sim.player_view(verbose=True)['rows'] if r['id'] == 'result')
        self.assertIn('sword', row['choice_ids'])
        self.assertNotIn('sharp', row['choices'][0]['addon_ids'])
        self.assertTrue(sim.select('sharp').ok)
        row = next(r for r in sim.player_view(verbose=True)['rows'] if r['id'] == 'result')
        self.assertIn('sharp', row['choices'][0]['addon_ids'])
        project['rows'][0]['objects'][0]['addons'][0]['isNotResult'] = True
        sim = Simulator(project)
        self.assertTrue(sim.select('sword').ok)
        self.assertTrue(sim.select('sharp').ok)
        row = next(r for r in sim.player_view(verbose=True)['rows'] if r['id'] == 'result')
        self.assertNotIn('sharp', row['choices'][0]['addon_ids'])


if __name__ == '__main__':
    unittest.main()
