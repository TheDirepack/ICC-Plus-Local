from __future__ import annotations

from typing import Any

from .simulator import Simulator


def run_scenario(project: dict[str, Any], spec: dict[str, Any], *, seed: int = 0) -> dict[str, Any]:
    sim = Simulator(project, seed=seed)
    results: list[dict[str, Any]] = []
    passed = True
    for n, step in enumerate(spec.get('steps', [])):
        if not isinstance(step, dict):
            results.append({'step': n, 'ok': False, 'message': 'step must be an object'}); passed = False; continue
        if 'select' in step:
            event = sim.select(str(step['select']), times=int(step.get('times', 1) or 1))
            ok = event.ok if step.get('expect_ok', True) else not event.ok
            results.append({'step': n, 'ok': ok, 'action': 'select', 'event': event.to_dict()}); passed &= ok
        elif 'deselect' in step:
            event = sim.deselect(str(step['deselect']))
            ok = event.ok if step.get('expect_ok', True) else not event.ok
            results.append({'step': n, 'ok': ok, 'action': 'deselect', 'event': event.to_dict()}); passed &= ok
        elif 'assert' in step and isinstance(step['assert'], dict):
            checks = _assert_state(sim, step['assert'])
            ok = all(x['ok'] for x in checks)
            results.append({'step': n, 'ok': ok, 'action': 'assert', 'checks': checks}); passed &= ok
        else:
            results.append({'step': n, 'ok': False, 'message': 'unknown step'}); passed = False
    return {'passed': bool(passed), 'steps': results, 'final': sim.snapshot()}


def _assert_state(sim: Simulator, wanted: dict[str, Any]) -> list[dict[str, Any]]:
    snap = sim.snapshot(include_choice_status=True); out: list[dict[str, Any]] = []
    def add(name: str, ok: bool, actual: Any, expected: Any) -> None: out.append({'name': name, 'ok': bool(ok), 'actual': actual, 'expected': expected})
    if 'points' in wanted and isinstance(wanted['points'], dict):
        for pid, value in wanted['points'].items(): add(f'point:{pid}', snap['points'].get(pid) == value, snap['points'].get(pid), value)
    if 'selected' in wanted:
        expected = [str(x) for x in wanted['selected']]; add('selected', all(x in snap['selected_ids'] for x in expected), snap['selected_ids'], expected)
    if 'selected_exact' in wanted:
        expected = [str(x) for x in wanted['selected_exact']]; add('selected_exact', snap['selected_ids'] == expected, snap['selected_ids'], expected)
    if 'not_selected' in wanted:
        expected = [str(x) for x in wanted['not_selected']]; add('not_selected', all(x not in snap['selected_ids'] for x in expected), snap['selected_ids'], expected)
    if 'selectable' in wanted:
        expected = [str(x) for x in wanted['selectable']]; add('selectable', all(x in snap['selectable_ids'] for x in expected), snap['selectable_ids'], expected)
    if 'invalid' in wanted:
        expected = [str(x) for x in wanted['invalid']]; add('invalid', all(x in snap['invalid_choices'] for x in expected), sorted(snap['invalid_choices']), expected)
    if 'variables' in wanted and isinstance(wanted['variables'], dict):
        for vid, value in wanted['variables'].items(): add(f'variable:{vid}', snap['variables'].get(vid) == value, snap['variables'].get(vid), value)
    return out
