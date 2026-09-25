from __future__ import annotations

import copy
import json
from pathlib import Path

from iccplus_tools.simulator import Simulator

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = ROOT / 'verification' / 'expected' / 'runtime_cases.json'
VERIFY = ROOT / 'verification'


def _snapshot(sim: Simulator, case: dict) -> dict:
    prefix = case['prefix'] + '__'
    out = {
        'entities': {
            e.id: {'active': sim._active(e.id), 'multiple': sim._count(e.id)}
            for e in sim.index.selectables() if e.id.startswith(prefix)
        },
        'points': {k: float(v) for k, v in sorted(sim.state.points.items()) if k.startswith(prefix)},
        'variables': {k: v for k, v in sorted(sim.state.variables.items()) if k.startswith(prefix)},
        'words': {k: v for k, v in sorted(sim.state.words.items()) if k.startswith(prefix)},
        'rows': {
            e.id: {
                'currentChoices': int(sim.state.row_counts.get(e.id, 0)),
                'allowedChoices': int(sim._row_allowed(e)),
            }
            for e in sim.index.by_kind.get('row', []) if e.id.startswith(prefix)
        },
        'requirements': {},
        'build_string': sim.export_build_string(),
    }
    for ident in case.get('check_requirements', []):
        ent = sim.index.one(ident, 'choice') or sim.index.one(ident, 'selectable_addon')
        if ent is not None:
            out['requirements'][ident] = sim.req.evaluate(ent.value.get('requireds', []), sim.state)[0]
    return out


def _apply(sim: Simulator, action: dict) -> None:
    op = action['op']
    if op == 'select':
        sim.select(str(action['id']))
    elif op == 'deselect':
        sim.deselect(str(action['id']))
    elif op == 'row_button':
        sim.press_row_button(str(action['id']))
    elif op == 'reset':
        sim.reset()
    elif op == 'set_point':
        sim.state.points[str(action['id'])] = float(action['value'])
    else:
        raise AssertionError(f'unsupported verification action: {action!r}')


def test_all_isolated_runtime_fixtures_match_every_intermediate_and_final_expectation():
    cases = json.loads(EXPECTED.read_text(encoding='utf-8'))
    assert len(cases) == 32
    for case in cases:
        project = json.loads((VERIFY / case['fixture']).read_text(encoding='utf-8'))
        sim = Simulator(copy.deepcopy(project), clean=False)
        observed_steps = []
        for action in case['actions']:
            _apply(sim, action)
            observed_steps.append(_snapshot(sim, case))
            assert sim.runtime_state_issues() == [], case['id']
        assert observed_steps == case['expected_after_actions'], case['id']
        assert _snapshot(sim, case) == case['expected'], case['id']
