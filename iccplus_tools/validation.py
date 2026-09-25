from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from typing import Any

from .model import Entity, ProjectIndex
from .project_integrity import completeness_issues
from .upstream_2106 import ICCPLUS_VERSION


@dataclass(slots=True)
class Diagnostic:
    code: str
    severity: str
    path: str
    message: str
    entity_id: str | None = None
    suggestion: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


RUNTIME_EFFECT_FIELDS = {
    'discountOther', 'changeTemplates', 'changeWidth',
    'setBgmIsOn', 'isFadeTransition', 'customTextfieldIsOn', 'confirmIsOn', 'isImageUpload',
    'changePointBar', 'changeBackground', 'scrollToRow', 'scrollToObject',
}


def _objects(v: Any) -> list[dict[str, Any]]:
    return [x for x in v if isinstance(x, dict)] if isinstance(v, list) else []


def _strings(v: Any) -> list[str]:
    return [x for x in v if isinstance(x, str)] if isinstance(v, list) else []


def _mechanical_signature(value: dict[str, Any], ignored: set[str]) -> str:
    cleaned = {k: v for k, v in value.items() if k not in ignored}
    return json.dumps(cleaned, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def _duplicate_strings(out: list[Diagnostic], ent: Entity, field: str) -> None:
    values = _strings(ent.value.get(field))
    seen: set[str] = set()
    for i, value in enumerate(values):
        if value in seen:
            _diag(out, 'list.duplicate_reference', 'warning', f'{ent.path}/{field}/{i}', f'{field} contains duplicate reference {value!r}.', ent, 'Keep each reference once unless repeated entries have documented viewer meaning.')
        seen.add(value)


def _duplicate_mechanics(index: ProjectIndex, out: list[Diagnostic]) -> None:
    req_ignored = {'id', 'beforeText', 'afterText', 'showRequired', 'customTextIsOn', 'customText'}
    score_ignored = {'idx', 'beforeText', 'afterText', 'showScore', 'hideValue'}

    req_seen: dict[tuple[str | None, str], Entity] = {}
    for req in index.by_kind.get('requirement', []):
        sig = _mechanical_signature(req.value, req_ignored)
        key = (req.parent_id, sig)
        first = req_seen.get(key)
        if first is not None:
            _diag(out, 'requirement.duplicate_mechanics', 'warning', req.path, f'Requirement duplicates the mechanics of {first.id!r} under the same parent.', req, 'Merge or remove the repeated requirement unless duplicate display text is intentional.')
        else:
            req_seen[key] = req

    score_seen: dict[tuple[str | None, str], Entity] = {}
    for score in index.by_kind.get('score', []):
        sig = _mechanical_signature(score.value, score_ignored)
        key = (score.parent_id, sig)
        first = score_seen.get(key)
        if first is not None:
            _diag(out, 'score.duplicate_mechanics', 'warning', score.path, f'Score duplicates the mechanics of {first.id!r} under the same parent.', score, 'Merge or remove the repeated score unless duplicate display text is intentional.')
        else:
            score_seen[key] = score


def _diag(out: list[Diagnostic], code: str, severity: str, path: str, msg: str, ent: Entity | None = None, suggestion: str | None = None) -> None:
    out.append(Diagnostic(code, severity, path, msg, ent.id if ent else None, suggestion))


def _check_ref(out: list[Diagnostic], ent: Entity, field: str, allowed: set[str], label: str) -> None:
    value = ent.value.get(field)
    if isinstance(value, str) and value and value not in allowed:
        _diag(out, 'reference.missing', 'error', f'{ent.path}/{field}', f'{field} references missing {label} {value!r}.', ent)


def _check_ref_array(out: list[Diagnostic], ent: Entity, field: str, allowed: set[str], label: str) -> None:
    value = ent.value.get(field)
    if not isinstance(value, list):
        return
    for i, item in enumerate(value):
        if isinstance(item, str) and item and item not in allowed:
            _diag(out, 'reference.missing', 'error', f'{ent.path}/{field}/{i}', f'{field} references missing {label} {item!r}.', ent)


def _req_refs(out: list[Diagnostic], ent: Entity, index: ProjectIndex, sets: dict[str, set[str]]) -> None:
    req = ent.value
    typ = str(req.get('type', ''))
    rid = str(req.get('reqId', ''))
    if typ == 'id':
        base = rid.split('/ON#', 1)[0]
        if base and base not in sets['activation']:
            _diag(out, 'requirement.missing_selectable', 'error', ent.path + '/reqId', f'id requirement references missing selectable or variable {base!r}.', ent)
    elif typ == 'points':
        if rid and rid not in sets['points']:
            _diag(out, 'requirement.missing_point', 'error', ent.path + '/reqId', f'point requirement references missing point {rid!r}.', ent)
    elif typ == 'pointCompare':
        for field in ('reqId', 'reqId1'):
            value = str(req.get(field, ''))
            if value and value not in sets['points']:
                _diag(out, 'requirement.missing_point', 'error', ent.path + '/' + field, f'point comparison references missing point {value!r}.', ent)
        for i, more in enumerate(_objects(req.get('more'))):
            value = str(more.get('id', ''))
            if value and value not in sets['points']:
                _diag(out, 'requirement.missing_point', 'error', f'{ent.path}/more/{i}/id', f'point comparison references missing point {value!r}.', ent)
    elif typ == 'selFromGroups':
        for i, gid in enumerate(_strings(req.get('selGroups'))):
            if gid not in sets['groups']:
                _diag(out, 'requirement.missing_group', 'error', f'{ent.path}/selGroups/{i}', f'group selection requirement references missing group {gid!r}.', ent)
    elif typ == 'selFromRows':
        for i, row in enumerate(_strings(req.get('selRows'))):
            if row not in sets['rows']:
                _diag(out, 'requirement.missing_row', 'error', f'{ent.path}/selRows/{i}', f'row selection requirement references missing row {row!r}.', ent)
    elif typ == 'gid':
        if rid and rid not in sets['global']:
            _diag(out, 'requirement.missing_global', 'error', ent.path + '/reqId', f'global requirement {rid!r} does not exist.', ent)
    elif typ == 'word':
        if rid and rid not in sets['words']:
            _diag(out, 'requirement.missing_word', 'error', ent.path + '/reqId', f'word requirement references missing word {rid!r}.', ent)
    elif typ not in {'or', 'selFromWhole', ''}:
        _diag(out, 'requirement.unknown_type', 'warning', ent.path + '/type', f'Unknown requirement type {typ!r}; simulator will treat it as unmet.', ent)


def _global_cycles(index: ProjectIndex, out: list[Diagnostic]) -> None:
    graph: dict[str, set[str]] = {}
    for gr in index.by_kind.get('global_requirement', []):
        targets: set[str] = set()
        stack = list(_objects(gr.value.get('requireds')))
        while stack:
            req = stack.pop()
            if req.get('type') == 'gid' and req.get('reqId'):
                targets.add(str(req['reqId']))
            stack.extend(_objects(req.get('requireds'))); stack.extend(_objects(req.get('orRequireds')))
        graph[gr.id] = targets
    visiting: set[str] = set(); done: set[str] = set()
    def visit(node: str, chain: list[str]) -> None:
        if node in visiting:
            cycle = chain[chain.index(node):] + [node] if node in chain else [node, node]
            ent = index.one(node, 'global_requirement')
            _diag(out, 'global_requirement.cycle', 'error', ent.path if ent else '/globalRequirements', 'Global requirement cycle: ' + ' -> '.join(cycle), ent)
            return
        if node in done: return
        visiting.add(node)
        for child in graph.get(node, set()):
            if child in graph: visit(child, [*chain, child])
        visiting.remove(node); done.add(node)
    for node in graph: visit(node, [node])


PROJECT_ARRAY_FIELDS = ('rows', 'pointTypes', 'variables', 'words', 'groups', 'rowDesignGroups', 'objectDesignGroups', 'globalRequirements', 'soundEffects', 'categories', 'backpack')


def project_shape_diagnostics(project: Any) -> list[Diagnostic]:
    out: list[Diagnostic] = []
    if not isinstance(project, dict):
        _diag(out, 'project.not_object', 'error', '', 'ICC Plus project JSON must be an object.')
        return out
    if 'rows' not in project:
        _diag(out, 'structure.missing_rows', 'error', '/rows', 'ICC Plus project JSON must contain a rows array.')
    for key in PROJECT_ARRAY_FIELDS:
        if key in project and not isinstance(project[key], list):
            _diag(out, 'structure.expected_array', 'error', '/' + key, f'{key} must be an array.')
    return out


def validate(project: Any, *, complete: bool = False) -> dict[str, Any]:
    out = project_shape_diagnostics(project)
    if not isinstance(project, dict):
        return _report(out, {})

    index = ProjectIndex(project)
    sets = {
        'points': index.ids(['point']),
        'variables': index.ids(['variable']),
        'words': index.ids(['word']),
        'groups': index.ids(['group']),
        'rows': index.ids(['row', 'backpack_row']),
        'global': index.ids(['global_requirement']),
        'selectables': index.ids(['choice', 'selectable_addon']),
        'sounds': index.ids(['sound_effect']),
    }
    sets['activation'] = sets['selectables'] | sets['variables']

    identity_kinds = {'row','backpack_row','choice','selectable_addon','score','point','variable','word','group','row_design_group','choice_design_group','global_requirement','sound_effect'}
    seen: dict[str, list[Entity]] = {}
    for ent in index.entities:
        if ent.kind in identity_kinds and not ent.id.startswith('@'):
            seen.setdefault(ent.id, []).append(ent)
    for ident, ents in seen.items():
        if len(ents) > 1:
            for ent in ents:
                _diag(out, 'id.duplicate', 'error', ent.path + ('/idx' if ent.kind == 'score' else '/id'), f'ID {ident!r} is used by {len(ents)} entities.', ent, 'Rename one ID and rewrite references.')

    for ent in index.by_kind.get('row', []) + index.by_kind.get('backpack_row', []):
        if not ent.value.get('id'):
            _diag(out, 'id.missing', 'error', ent.path + '/id', 'Row has no ID.', ent)
        expected = int(ent.path.rsplit('/', 1)[-1])
        if isinstance(ent.value.get('index'), (int, float)) and int(ent.value['index']) != expected:
            _diag(out, 'index.stale', 'warning', ent.path + '/index', f'Row index is {ent.value["index"]}, expected {expected}.', ent, 'Normalize indexes.')
        allowed = ent.value.get('allowedChoices', 0)
        if isinstance(allowed, (int, float)) and allowed < 0:
            _diag(out, 'row.negative_allowed_choices', 'warning', ent.path + '/allowedChoices', 'Negative allowedChoices is unusual; ICC Plus treats only values > 0 as a cap.', ent)

    for ent in index.by_kind.get('choice', []):
        if not ent.value.get('id'):
            _diag(out, 'id.missing', 'error', ent.path + '/id', 'Choice has no ID.', ent)
        expected = int(ent.path.split('/objects/')[-1].split('/')[0])
        if isinstance(ent.value.get('index'), (int, float)) and int(ent.value['index']) != expected:
            _diag(out, 'index.stale', 'warning', ent.path + '/index', f'Choice index is {ent.value["index"]}, expected {expected}.', ent, 'Normalize indexes.')

    for ent in index.by_kind.get('addon', []) + index.by_kind.get('selectable_addon', []):
        # Non-selectable Addons are created upstream with id: "". Only a
        # selectable Addon is registered in choiceMap and therefore needs an ID.
        if ent.kind == 'selectable_addon' and not ent.value.get('id'):
            _diag(out, 'id.missing', 'error', ent.path + '/id', 'Selectable Addon has no ID.', ent)
        if ent.kind == 'selectable_addon' and ent.value.get('parentId') and str(ent.value['parentId']) != ent.parent_id:
            _diag(out, 'addon.parent_mismatch', 'warning', ent.path + '/parentId', f'parentId is {ent.value["parentId"]!r}, actual parent choice is {ent.parent_id!r}.', ent)

    for score in index.by_kind.get('score', []):
        pid = str(score.value.get('id', ''))
        if pid and pid not in sets['points']:
            _diag(out, 'score.missing_point', 'error', score.path + '/id', f'Score references missing point {pid!r}.', score)
        if not score.value.get('idx'):
            _diag(out, 'score.missing_idx', 'error', score.path + '/idx', 'Score has no idx identifier.', score)

    for req in index.by_kind.get('requirement', []):
        # Ordinary Requirements are structural objects in ICC Plus and their
        # creator default is id: ""; global requirements have real IDs.
        _req_refs(out, req, index, sets)

    _duplicate_mechanics(index, out)

    for kind in ('point','variable','word','group','row_design_group','choice_design_group','global_requirement','sound_effect'):
        for ent in index.by_kind.get(kind, []):
            if not ent.value.get('id'):
                _diag(out, 'id.missing', 'error', ent.path + '/id', f'{kind.replace("_", " ").title()} has no ID.', ent)

    # Categories do not have a string ID upstream. Their identity is the pair (type, idx).
    cat_seen: dict[str, list[Entity]] = {}
    for cat in index.by_kind.get('category', []):
        if not isinstance(cat.value.get('idx'), int):
            _diag(out, 'category.missing_idx', 'error', cat.path + '/idx', 'Category has no integer idx.', cat)
        cat_seen.setdefault(cat.id, []).append(cat)
    for ident, cats in cat_seen.items():
        if len(cats) > 1:
            for cat in cats:
                _diag(out, 'category.duplicate_identity', 'error', cat.path, f'Category identity {ident!r} is duplicated.', cat)

    for group in index.by_kind.get('group', []):
        _duplicate_strings(out, group, 'elements')
        _duplicate_strings(out, group, 'rowElements')
        for i, member in enumerate(_strings(group.value.get('elements'))):
            if member not in sets['selectables']:
                _diag(out, 'group.missing_member', 'error', f'{group.path}/elements/{i}', f'Group contains missing selectable {member!r}.', group)
        for i, row in enumerate(_strings(group.value.get('rowElements'))):
            if row not in sets['rows']:
                _diag(out, 'group.missing_row', 'error', f'{group.path}/rowElements/{i}', f'Group contains missing row {row!r}.', group)

    row_designs = index.ids(['row_design_group']); choice_designs = index.ids(['choice_design_group'])
    design_groups = row_designs | choice_designs

    for point in index.by_kind.get('point', []):
        _check_ref(out, point, 'activatedId', sets['activation'], 'selectable or variable')

    for group in index.by_kind.get('group', []):
        _duplicate_strings(out, group, 'designGroups')
        _check_ref_array(out, group, 'designGroups', design_groups, 'design group')

    for dg in index.by_kind.get('row_design_group', []):
        _check_ref(out, dg, 'activatedId', sets['activation'], 'selectable or variable')
        _duplicate_strings(out, dg, 'elements')
        _duplicate_strings(out, dg, 'backpackElements')
        _duplicate_strings(out, dg, 'groupElements')
        _check_ref_array(out, dg, 'elements', index.ids(['row']), 'row')
        _check_ref_array(out, dg, 'backpackElements', index.ids(['backpack_row']), 'backpack row')
        _check_ref_array(out, dg, 'groupElements', sets['groups'], 'group')

    for dg in index.by_kind.get('choice_design_group', []):
        _check_ref(out, dg, 'activatedId', sets['activation'], 'selectable or variable')
        _duplicate_strings(out, dg, 'elements')
        _duplicate_strings(out, dg, 'backpackElements')
        _duplicate_strings(out, dg, 'groupElements')
        _check_ref_array(out, dg, 'elements', sets['selectables'], 'selectable')
        _check_ref_array(out, dg, 'backpackElements', sets['selectables'], 'selectable')
        _check_ref_array(out, dg, 'groupElements', sets['groups'], 'group')

    for sfx in index.by_kind.get('sound_effect', []):
        _duplicate_strings(out, sfx, 'groups')
        _check_ref_array(out, sfx, 'groups', sets['groups'], 'group')
    for ent in index.selectables():
        if ent.value.get('isSelectableMultiple'):
            variable_mode = ent.value.get('isMultipleUseVariable') is True
            score_mode = isinstance(ent.value.get('multipleScoreId'), str) and bool(ent.value.get('multipleScoreId'))
            if not variable_mode and not score_mode:
                _diag(
                    out, 'multiple.mode_missing', 'error', ent.path + '/isSelectableMultiple',
                    f'isSelectableMultiple is enabled but neither isMultipleUseVariable nor multipleScoreId is configured; ICC Plus {ICCPLUS_VERSION} renders the counter but +/- does not change this entity.',
                    ent, 'Enable isMultipleUseVariable for a normal repeat counter, or set multipleScoreId for a point-backed counter.'
                )
            elif variable_mode and score_mode:
                _diag(
                    out, 'multiple.mode_ambiguous', 'warning', ent.path + '/isSelectableMultiple',
                    f'Both repeat modes are configured. ICC Plus {ICCPLUS_VERSION} gives isMultipleUseVariable precedence and ignores multipleScoreId for the counter.',
                    ent
                )
        _duplicate_strings(out, ent, 'groups')
        _duplicate_strings(out, ent, 'objectDesignGroups')
        _check_ref_array(out, ent, 'groups', sets['groups'], 'group')
        _check_ref_array(out, ent, 'objectDesignGroups', choice_designs, 'choice design group')
        _check_ref_array(out, ent, 'discountRows', sets['rows'], 'row')
        _check_ref_array(out, ent, 'discountChoices', sets['selectables'], 'selectable')
        _check_ref_array(out, ent, 'discountGroups', sets['groups'], 'group')
        _check_ref_array(out, ent, 'discountPointTypes', sets['points'], 'point')
        _check_ref_array(out, ent, 'pointTypeToMultiply', sets['points'], 'point')
        _check_ref_array(out, ent, 'pointTypeToDivide', sets['points'], 'point')
        _check_ref_array(out, ent, 'pointTypeToSet', sets['points'], 'point')
        _check_ref_array(out, ent, 'changedVariables', sets['variables'], 'variable')
        _duplicate_strings(out, ent, 'hiddenContentsRow')
        _duplicate_strings(out, ent, 'hiddenContentsType')
        _check_ref_array(out, ent, 'hiddenContentsRow', sets['rows'], 'row')
        for i, code in enumerate(_strings(ent.value.get('hiddenContentsType'))):
            if code not in {str(x) for x in range(1, 11)}:
                _diag(out, 'effect.invalid_hidden_content_type', 'error', f'{ent.path}/hiddenContentsType/{i}', f'hiddenContentsType contains unknown code {code!r}; expected 1 through 10.', ent)
        _check_ref_array(out, ent, 'idOfAllowChoice', sets['rows'], 'row')
        for field in ('idOfTheTextfieldWord',): _check_ref(out, ent, field, sets['words'], 'word')
        for field in ('sfxIdOnSelect','sfxIdOnDeselect'): _check_ref(out, ent, field, sets['sounds'], 'sound effect')
        for field in ('activateThisChoice','deactivateThisChoice'):
            raw = ent.value.get(field)
            if isinstance(raw, str) and raw:
                for token in raw.split(','):
                    # ICC Plus 2.10.7 splits these fields on commas but does not
                    # trim each token. Validation must use the same literal ID so
                    # a target like " a" is reported as missing when only "a"
                    # exists instead of being falsely accepted here.
                    base = token.split('/ON#', 1)[0]
                    if base and base not in sets['selectables'] and base not in sets['groups']:
                        _diag(out, 'effect.missing_target', 'error', f'{ent.path}/{field}', f'{field} references missing selectable/group {base!r}.', ent)
        enabled = sorted(k for k in RUNTIME_EFFECT_FIELDS if ent.value.get(k))
        if enabled:
            _diag(out, 'simulation.advanced_effects', 'info', ent.path, 'Choice uses advanced effects: ' + ', '.join(enabled) + '. Static validation covers references; the headless simulator reports any effect it does not execute exactly.', ent)

    for row in index.by_kind.get('row', []) + index.by_kind.get('backpack_row', []):
        _duplicate_strings(out, row, 'groups')
        _duplicate_strings(out, row, 'rowDesignGroups')
        _check_ref_array(out, row, 'groups', sets['groups'], 'group')
        _check_ref_array(out, row, 'rowDesignGroups', row_designs, 'row design group')
        if row.value.get('isResultRow') or row.value.get('isGroupRow'):
            _check_ref(out, row, 'resultGroupId', sets['groups'] | sets['rows'], 'group or row')

    _global_cycles(index, out)
    vc = project.get('viewerConfig')
    if isinstance(vc, dict) and vc.get('useSeparateImages') is True and vc.get('useLocalViewer') is True:
        _diag(out, 'viewer.mutually_exclusive_export_modes', 'error', '/viewerConfig', 'useSeparateImages and useLocalViewer cannot both be true.')

    if complete:
        for issue in completeness_issues(project):
            out.append(Diagnostic(
                issue.get('code', 'complete.invalid'),
                'error',
                str(issue.get('path', '')),
                str(issue.get('message', 'Project is not Creator-complete.')),
                issue.get('entity_id'),
                issue.get('suggestion'),
            ))

    report = _report(out, index.summary())
    report['mode'] = 'complete' if complete else 'compatibility'
    return report


def validate_complete(project: Any) -> dict[str, Any]:
    """Validate a final/generated project against the official Creator-complete shape."""
    return validate(project, complete=True)


def _report(out: list[Diagnostic], summary: dict[str, Any]) -> dict[str, Any]:
    errors = sum(1 for x in out if x.severity == 'error')
    warnings = sum(1 for x in out if x.severity == 'warning')
    return {'valid': errors == 0, 'errors': errors, 'warnings': warnings, 'summary': summary, 'diagnostics': [x.to_dict() for x in out]}
