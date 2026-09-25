from __future__ import annotations

import copy
import unittest

from iccplus_tools.editor import ProjectEditor, new_project
from iccplus_tools.model import ProjectIndex
from iccplus_tools.operations import apply_operation_script


def project_fixture():
    p = new_project()
    e = ProjectEditor(p)
    r1 = e.add('row', values={'id': 'r1', 'title': 'One'})
    r2 = e.add('row', values={'id': 'r2', 'title': 'Two'})
    a = e.add('choice', parent='r1', values={'id': 'a', 'title': 'A'})
    b = e.add('choice', parent='r1', values={'id': 'b', 'title': 'B'})
    e.add('choice', parent='r2', values={'id': 'c', 'title': 'C'})
    e.add('score', parent='a', values={'idx': 'sa', 'id': '', 'value': 1})
    e.add('selectable_addon', parent='a', values={'id': 'aa', 'title': 'AA'})
    e.normalize_and_check()
    return p


class StructuralAuthoringTests(unittest.TestCase):
    def test_reorder_rows_and_choices_rewrites_indices(self):
        p = project_fixture()
        e = ProjectEditor(p)
        self.assertEqual(e.reorder('row', ['r2', 'r1']), ['r2', 'r1'])
        self.assertEqual([r['id'] for r in p['rows']], ['r2', 'r1'])
        self.assertEqual([r['index'] for r in p['rows']], [0, 1])
        self.assertEqual(e.reorder('choice', ['b', 'a'], parent='r1'), ['b', 'a'])
        row = e.resolve('r1').value
        self.assertEqual([c['id'] for c in row['objects']], ['b', 'a'])
        self.assertEqual([c['index'] for c in row['objects']], [0, 1])

    def test_partial_reorder_preserves_unlisted_relative_order(self):
        p = project_fixture()
        e = ProjectEditor(p)
        e.add('choice', parent='r1', values={'id': 'd'})
        self.assertEqual(e.reorder('choice', ['d'], parent='r1', partial=True), ['d', 'a', 'b'])

    def test_move_choice_between_rows(self):
        p = project_fixture()
        e = ProjectEditor(p)
        moved = e.move('b', parent='r2', index=0)
        self.assertEqual(moved['parent'], 'r2')
        self.assertEqual([x['id'] for x in e.resolve('r1').value['objects']], ['a'])
        self.assertEqual([x['id'] for x in e.resolve('r2').value['objects']], ['b', 'c'])
        self.assertEqual([x['index'] for x in e.resolve('r2').value['objects']], [0, 1])

    def test_move_selectable_addon_repairs_parent_id(self):
        p = project_fixture()
        e = ProjectEditor(p)
        e.move('aa', parent='b')
        addon = e.resolve('aa', 'selectable_addon').value
        self.assertEqual(addon['parentId'], 'b')
        self.assertFalse(any(x.get('id') == 'aa' for x in e.resolve('a').value['addons']))

    def test_clone_row_remaps_nested_identities_and_internal_refs(self):
        p = project_fixture()
        e = ProjectEditor(p)
        # Make B depend on A so the clone must point at cloned A, not source A.
        e.add('requirement', parent='b', values={'type': 'id', 'required': True, 'reqId': 'a'})
        source = e.resolve('r1').value
        source['objects'][0]['isActive'] = True
        result = e.clone('r1')
        cloned = result['value']
        self.assertNotEqual(cloned['id'], 'r1')
        old_to_new = result['id_map']
        self.assertIn('a', old_to_new)
        self.assertIn('b', old_to_new)
        ca, cb = cloned['objects'][:2]
        self.assertEqual(ca['id'], old_to_new['a'])
        self.assertEqual(cb['requireds'][0]['reqId'], old_to_new['a'])
        self.assertFalse(ca['isActive'])
        selectable = ca['addons'][0]
        self.assertEqual(selectable['parentId'], ca['id'])
        self.assertNotEqual(selectable['id'], 'aa')
        self.assertNotEqual(ca['scores'][0]['idx'], 'sa')
        e.normalize_and_check()

    def test_import_fragment_preserves_unique_identity_and_remaps_collision(self):
        p = project_fixture()
        e = ProjectEditor(p)
        unique = {'id': 'fresh', 'index': 0, 'title': 'Fresh', 'text': '', 'debugTitle': '', 'image': '', 'template': 1, 'objectWidth': '', 'isActive': False, 'multipleUseVariable': 0, 'selectedThisManyTimesProp': 0, 'requireds': [], 'addons': [], 'scores': [], 'groups': [], 'objectDesignGroups': []}
        imported = e.import_fragment('choice', unique, parent='r2')
        self.assertEqual(imported['id'], 'fresh')
        collision = copy.deepcopy(unique)
        collision['title'] = 'Again'
        imported2 = e.import_fragment('choice', collision, parent='r2')
        self.assertNotEqual(imported2['id'], 'fresh')
        self.assertEqual(imported2['id_map']['fresh'], imported2['id'])


    def test_add_supports_creator_top_level_entity_kinds(self):
        p = new_project()
        e = ProjectEditor(p)
        rd = e.add('row_design_group', values={'id': 'rd1'})
        cd = e.add('choice_design_group', values={'id': 'cd1'})
        sfx = e.add('sound_effect', values={'id': 'sfx1'})
        cat = e.add('category', values={'type': 'point', 'name': 'Economy'})
        bp = e.add('backpack_row', values={'id': 'bp1'})
        self.assertEqual(rd['id'], 'rd1')
        self.assertEqual(cd['id'], 'cd1')
        self.assertEqual(sfx['id'], 'sfx1')
        self.assertEqual(cat, {'idx': 0, 'name': 'Economy', 'type': 'point'})
        self.assertEqual(bp['id'], 'bp1')
        e.normalize_and_check()

    def test_category_slots_follow_creator_identity_and_delete_unassigns(self):
        p = new_project()
        e = ProjectEditor(p)
        point = e.add('point', values={'id': 'p1', 'category': 0})
        first = e.add('category', values={'type': 'point', 'idx': 0, 'name': 'First'})
        second = e.add('category', values={'type': 'point', 'name': 'Second'})
        same_slot_other_type = e.add('category', values={'type': 'word', 'idx': 0, 'name': 'Words'})
        self.assertEqual(first['idx'], 0)
        self.assertEqual(second['idx'], 1)
        self.assertEqual(same_slot_other_type['idx'], 0)
        with self.assertRaisesRegex(ValueError, 'identity already exists'):
            e.add('category', values={'type': 'point', 'idx': 0})
        with self.assertRaisesRegex(ValueError, 'Creator slot'):
            e.add('category', values={'type': 'point', 'idx': 99})
        with self.assertRaisesRegex(ValueError, 'requires type'):
            e.add('category', values={'type': 'sound'})
        e.delete('point:0', kind='category')
        self.assertEqual(point['category'], -1)
        self.assertFalse(ProjectIndex(p).find('point:0', 'category'))

    def test_category_update_cannot_move_creator_slot(self):
        p = new_project()
        e = ProjectEditor(p)
        e.add('category', values={'type': 'point', 'idx': 0, 'name': 'A'})
        e.update('point:0', kind='category', values={'name': 'B'})
        self.assertEqual(e.resolve('point:0', 'category').value['name'], 'B')
        with self.assertRaisesRegex(ValueError, 'Creator slot'):
            e.update('point:0', kind='category', values={'idx': 1})

    def test_clone_and_import_support_top_level_creator_entities(self):
        p = new_project()
        e = ProjectEditor(p)
        e.add('group', values={'id': 'g1', 'name': 'G'})
        cloned = e.clone('g1')
        self.assertNotEqual(cloned['id'], 'g1')
        self.assertEqual(cloned['value']['name'], 'G')
        imported = e.import_fragment('variable', {'id': 'v_external', 'isTrue': True, 'category': -1})
        self.assertEqual(imported['id'], 'v_external')
        e.add('category', values={'type': 'variable', 'idx': 0, 'name': 'Vars'})
        # Category identity is composite; importing a colliding slot uses the next free Creator slot.
        cat_import = e.import_fragment('category', {'idx': 0, 'name': 'Vars copy', 'type': 'variable'})
        self.assertEqual(cat_import['id'], 'variable:1')
        e.normalize_and_check()

    def test_batch_structural_operations_are_atomic(self):
        p = project_fixture()
        original = copy.deepcopy(p)
        updated, result = apply_operation_script(p, {'operations': [
            {'op': 'reorder', 'kind': 'choice', 'parent': 'r1', 'order': ['b', 'a']},
            {'op': 'move', 'reference': 'b', 'parent': 'r2', 'index': 0},
            {'op': 'clone', 'reference': 'a', 'parent': 'r2'},
        ]})
        self.assertTrue(result['ok'], result)
        self.assertEqual([x['id'] for x in ProjectEditor(updated).resolve('r1').value['objects']], ['a'])
        self.assertGreater(len(ProjectEditor(updated).resolve('r2').value['objects']), 2)

        failed, bad = apply_operation_script(original, {'operations': [
            {'op': 'move', 'reference': 'b', 'parent': 'r2'},
            {'op': 'move', 'reference': 'missing', 'parent': 'r2'},
        ]})
        self.assertFalse(bad['ok'])
        self.assertEqual(failed, original)


if __name__ == '__main__':
    unittest.main()


def test_creator_feature_factory_defaults_match_2106_source():
    from iccplus_tools.editor import make_entity
    from iccplus_tools.upstream_2106 import default_project
    project = default_project()
    project['rowDesignGroups'] = []
    project['objectDesignGroups'] = []
    row_design = make_entity(project, 'row_design_group')
    project['rowDesignGroups'].append(row_design)
    choice_design = make_entity(project, 'choice_design_group')
    sfx = make_entity(project, 'sound_effect')
    assert row_design['name'] == 'Design Group 1'
    assert choice_design['name'] == 'Design Group 1'
    assert sfx['volume'] == 1
    assert sfx['pitch'] == 0


def test_word_requirement_factory_matches_creator_initial_placeholder():
    from iccplus_tools.editor import make_entity
    from iccplus_tools.upstream_2106 import default_project
    req = make_entity(default_project(), 'requirement', {'type': 'word'})
    assert req['type'] == 'word'
    assert req['orRequired'] == [{'req': ''}]
