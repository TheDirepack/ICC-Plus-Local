"""Official AppRow DOM differential fixtures for Result/Group Row projection."""
from __future__ import annotations

import copy
from typing import Any

from .live_parity import _choice, _project, _req, _row
from .simulator import Simulator


def projected_cases() -> list[dict[str, Any]]:
    sword = _choice('sword', groups=['weapons'])
    sword['addons'] = [{
        'id': 'sharp', 'title': 'Sharp', 'text': '', 'template': 1,
        'addonWidth': 'col-12', 'image': '', 'requireds': [],
        'parentId': 'sword', 'isSelectable': True, 'scores': [],
        'groups': ['weapons'], 'multipleUseVariable': 0, 'isActive': False,
    }]
    gear = _row('gear', [sword, _choice('shield', isNotResult=True)])
    other = _row('other', [_choice('fire', groups=['weapons'])])
    result = _row('result', [])
    result.update(isResultRow=True, isInfoRow=True)
    scoped = _row('scoped_result', [])
    scoped.update(isResultRow=True, isInfoRow=True, resultGroupId='weapons')
    group = _row('group', [])
    group.update(isGroupRow=True, resultGroupId='weapons')
    groups = [{'id': 'weapons', 'name': 'Weapons', 'category': -1,
               'elements': ['sharp', 'fire', 'sword'], 'rowElements': []}]
    proj = _project(rows=[gear, other, result, scoped, group], groups=groups)
    captured = ['gear', 'other', 'result', 'scoped_result', 'group']
    # Include duplicate group cards from selectable-Addon and direct parent entries.
    selected = {
        'name': 'result_group_card_projection', 'project': proj, 'row_ids': captured,
        'actions': [{'op': 'select', 'id': 'fire'}, {'op': 'select', 'id': 'sword'},
                    {'op': 'select', 'id': 'sharp'}, {'op': 'select', 'id': 'shield'},
                    {'op': 'deselect', 'id': 'sword'}],
    }
    hidden = copy.deepcopy(proj)
    hidden['rows'][0]['requireds'] = [_req('id', reqId='fire')]
    # A Group Row mounts a card even when the original Row fails Requirements.
    cross = copy.deepcopy(proj)
    cross['backpack'] = [_row('bag_source', [_choice('bag_item', groups=['weapons'])])]
    cross['groups'][0]['elements'] = ['bag_item']
    # The main Viewer Group Row can project a Choice whose source is Backpack.
    return [selected, {'name': 'group_row_hidden_source', 'project': hidden,
                       'row_ids': captured, 'actions': []},
            {'name': 'group_row_backpack_source', 'project': cross,
             'row_ids': captured, 'actions': []}]


def local_projected_traces() -> dict[str, list[dict[str, list[str]]]]:
    results: dict[str, list[dict[str, list[str]]]] = {}
    for case in projected_cases():
        sim = Simulator(copy.deepcopy(case['project']))

        def capture() -> dict[str, list[str]]:
            rows = {row['id']: row['choice_ids'] for row in sim.player_view()['rows']}
            return {row_id: list(rows.get(row_id, [])) for row_id in case['row_ids']}

        trace = [capture()]
        for action in case['actions']:
            event = (sim.select(action['id']) if action['op'] == 'select'
                     else sim.deselect(action['id']))
            if not event.ok:
                raise AssertionError(f"{case['name']}: {action} failed: {event.code}")
            trace.append(capture())
        results[case['name']] = trace
    return results
