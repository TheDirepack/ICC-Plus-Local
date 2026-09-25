from __future__ import annotations

import copy
import difflib
import json
from pathlib import Path
from typing import Any

from .editor import ProjectEditor, pointer_get
from .field_catalog import FIELD_CATALOG, suggest_fields
from .field_types import validate_known_values
from .effects import HIDE_CONTENT_TYPES, apply_choice_effects
from .selectors import resolve_bulk_refs
from .validation import validate
from .creator_helpers import import_design, sort_row_choices
from .agent_protocol import AGENT_SCRIPT_KEYS, strict_agent_operation_keys

def _string_list(value: Any, field: str) -> list[str]:
    """Accept the common one-or-many form used by LLM generated operations."""
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list) or any(not isinstance(x, str) for x in value):
        raise ValueError(f'{field} must be a string or an array of strings')
    return list(dict.fromkeys(x for x in value if x))


def _one_or_many(operation: dict[str, Any], plural: str, singular: str) -> list[str]:
    if plural in operation and singular in operation:
        raise ValueError(f'use either {plural} or {singular}, not both')
    value = operation.get(plural, operation.get(singular))
    return _string_list(value, plural)


def _bulk_refs(
    project: dict[str, Any],
    operation: dict[str, Any],
    plural: str,
    singular: str,
    *,
    allowed_kinds: set[str] | None = None,
    label: str | None = None,
) -> list[str]:
    explicit = _one_or_many(operation, plural, singular)
    where = operation.get('where')
    if where is not None and not isinstance(where, dict):
        raise ValueError('where must be an object')
    return resolve_bulk_refs(
        project,
        explicit=explicit,
        where=where,
        expect=operation.get('expect'),
        allow_empty=bool(operation.get('allow_empty', False)),
        allowed_kinds=allowed_kinds,
        label=label or plural,
    )


def _reference(operation: dict[str, Any], *, required: bool = True) -> str | None:
    if 'reference' in operation and 'ref' in operation and operation['reference'] != operation['ref']:
        raise ValueError('reference and ref disagree')
    value = operation.get('reference', operation.get('ref'))
    if value is None:
        if required:
            raise ValueError('reference is required')
        return None
    value = str(value).strip()
    if not value and required:
        raise ValueError('reference is required')
    return value or None


def _field_kind(kind: str) -> str:
    return {'backpack_row': 'row'}.get(kind, kind)


def _operation_values(operation: dict[str, Any], kind: str, reserved: set[str], label: str, *, strict_fields: bool = False) -> dict[str, Any]:
    """Merge optional inline native fields with the legacy values object.

    Inline fields are limited to the pinned native field catalog. That catches
    misspelled operation keys while keeping values={} as the escape hatch for
    uncommon or forward-compatible native data.
    """
    nested = operation.get('values', {})
    if nested is None:
        nested = {}
    if not isinstance(nested, dict):
        raise ValueError(f'{label}.values must be an object')

    allowed = set(FIELD_CATALOG.get(_field_kind(kind), ()))
    inline: dict[str, Any] = {}
    unknown: list[str] = []
    for key, value in operation.items():
        if key in reserved:
            continue
        if key in allowed:
            inline[key] = value
        else:
            unknown.append(key)
    if unknown:
        suggestion_parts = []
        for key in sorted(unknown):
            matches = suggest_fields(_field_kind(kind), key, limit=2)
            if matches:
                suggestion_parts.append(f'{key} -> {"/".join(matches)}')
        hint = f'; suggestions: {", ".join(suggestion_parts)}' if suggestion_parts else ''
        raise ValueError(
            f'{label} has unknown operation field(s): {", ".join(sorted(unknown))}{hint}; '
            'put uncommon native fields inside values'
        )

    nested_unknown = [key for key in nested if key not in allowed]
    if strict_fields and nested_unknown:
        suggestion_parts = []
        for key in sorted(nested_unknown):
            matches = suggest_fields(_field_kind(kind), key, limit=2)
            if matches:
                suggestion_parts.append(f'{key} -> {"/".join(matches)}')
        hint = f'; suggestions: {", ".join(suggestion_parts)}' if suggestion_parts else ''
        raise ValueError(
            f'{label}.values has unknown native field(s): {", ".join(sorted(nested_unknown))}{hint}; '
            'canonical agent scripts are strict; use the compatibility operation format only for an intentional future ICC Plus field'
        )
    for key, value in nested.items():
        if key in inline and inline[key] != value:
            raise ValueError(f'{label}.{key} is set both inline and in values with different values')
        inline[key] = value
    # Compatibility scripts keep unknown fields under values as an explicit
    # forward-compatible escape hatch. Canonical agent scripts set
    # strict_fields=true and reject them above. Pinned fields are always type checked.
    validate_known_values(_field_kind(kind), inline, path=label)
    return inline

def _ensure_simple_requirement(editor: ProjectEditor, target: str, source: str, required: bool) -> tuple[dict[str, Any], bool]:
    ent = editor.resolve(target)
    reqs = ent.value.setdefault('requireds', [])
    if not isinstance(reqs, list):
        raise ValueError(f'{target}.requireds is not an array')
    for req in reqs:
        if isinstance(req, dict) and req.get('type') == 'id' and bool(req.get('required', True)) == required and str(req.get('reqId', '')) == source and not req.get('requireds') and not req.get('orRequireds'):
            return req, False
    value = editor.add('requirement', parent=target, values={'type': 'id', 'required': required, 'reqId': source}, normalize=False)
    return value, True

def _ensure_simple_score(editor: ProjectEditor, target: str, point: str, value: float) -> tuple[dict[str, Any], bool]:
    ent = editor.resolve(target)
    scores = ent.value.setdefault('scores', [])
    if not isinstance(scores, list):
        raise ValueError(f'{target}.scores is not an array')
    for score in scores:
        if isinstance(score, dict) and str(score.get('id', '')) == point and not score.get('requireds'):
            score['value'] = value
            return score, False
    score = editor.add('score', parent=target, values={'id': point, 'value': value}, normalize=False)
    return score, True


def _set_hidden_when_unmet(ent: Any, enabled: bool) -> None:
    if ent.kind not in {'choice', 'selectable_addon'}:
        return
    if enabled:
        ent.value['privateFilterIsOn'] = True
        styling = ent.value.setdefault('styling', {})
        if not isinstance(styling, dict):
            raise ValueError(f'{ent.id}.styling is not an object')
        styling['reqFilterVisibleIsOn'] = True
    else:
        styling = ent.value.get('styling')
        if isinstance(styling, dict):
            styling.pop('reqFilterVisibleIsOn', None)


def load_operation_script(source: str) -> dict[str, Any]:
    if source == '-':
        import sys
        text = sys.stdin.read()
    elif source.startswith('@'):
        text = Path(source[1:]).read_text(encoding='utf-8')
    else:
        stripped_source = source.lstrip()
        if stripped_source.startswith(('{', '[')) or '\n' in source or '\r' in source:
            text = source
        else:
            try:
                candidate = Path(source)
                text = candidate.read_text(encoding='utf-8') if candidate.exists() and candidate.is_file() else source
            except OSError:
                text = source
    stripped = text.lstrip()
    if not stripped:
        return {'format': 'iccplus-ops', 'format_version': 1, 'operations': []}
    if stripped[0] in '[{':
        try:
            value = json.loads(text)
        except json.JSONDecodeError:
            value = None
        if value is not None:
            if isinstance(value, list):
                return {'format': 'iccplus-ops', 'format_version': 1, 'operations': value}
            if not isinstance(value, dict):
                raise ValueError('operation script must be an object, an array, or JSONL')
            if 'op' in value and 'operations' not in value:
                return {'format': 'iccplus-ops', 'format_version': 1, 'operations': [value]}
            return value

    operations: list[dict[str, Any]] = []
    for line_no, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f'JSONL operation on line {line_no} must be an object')
        operations.append(value)
    return {'format': 'iccplus-ops', 'format_version': 1, 'operations': operations}


def _result_entity(value: dict[str, Any], kind: str | None = None) -> dict[str, Any]:
    ident = value.get('idx') if kind == 'score' else value.get('id')
    return {'id': ident, 'kind': kind, 'value': copy.deepcopy(value)}


def apply_operation_script(
    project: dict[str, Any],
    script: dict[str, Any],
    *,
    validate_after: bool = True,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if not isinstance(script, dict):
        raise ValueError('operation script must be an object')
    agent_format = script.get('format') == 'iccplus-agent-ops'
    if agent_format:
        unknown_script = sorted(set(script) - AGENT_SCRIPT_KEYS)
        if unknown_script:
            raise ValueError(f'iccplus-agent-ops has unknown top-level field(s): {", ".join(unknown_script)}')
        if script.get('format_version') != 1:
            raise ValueError('iccplus-agent-ops format_version must be 1')
        if script.get('strict_fields') is not True:
            raise ValueError('iccplus-agent-ops requires strict_fields=true')
    operations = script.get('operations', [])
    if not isinstance(operations, list):
        raise ValueError('operation script operations must be an array')

    strict_fields = bool(script.get('strict_fields', False) or script.get('format') == 'iccplus-agent-ops')
    working = copy.deepcopy(project)
    editor = ProjectEditor(working)
    results: list[dict[str, Any]] = []

    for index, operation in enumerate(operations):
        if not isinstance(operation, dict):
            return project, {
                'ok': False,
                'stage': 'operation',
                'operation_index': index,
                'error': 'operation must be an object',
                'results': results,
            }
        op = str(operation.get('op', '')).strip()
        try:
            if agent_format:
                allowed_keys = strict_agent_operation_keys().get(op)
                if allowed_keys is None:
                    raise ValueError(f'unknown operation {op!r}')
                unknown_keys = sorted(set(operation) - set(allowed_keys))
                if unknown_keys:
                    hints = []
                    for key in unknown_keys:
                        matches = difflib.get_close_matches(key, sorted(allowed_keys), n=2, cutoff=0.45)
                        if not matches and operation.get('kind'):
                            matches = suggest_fields(_field_kind(str(operation.get('kind', ''))), key, limit=2)
                        if matches:
                            hints.append(f'{key} -> {"/".join(matches)}')
                    suffix = f'; suggestions: {", ".join(hints)}' if hints else ''
                    raise ValueError(f'{op} has unknown operation field(s): {", ".join(unknown_keys)}{suffix}')
            if op == 'add':
                kind = str(operation['kind'])
                values = _operation_values(operation, kind, {'op', 'kind', 'parent', 'values'}, 'add', strict_fields=strict_fields)
                value = editor.add(kind, parent=operation.get('parent'), values=values, normalize=False)
                results.append({'index': index, 'op': op, 'ok': True, **_result_entity(value, kind)})
            elif op == 'upsert':
                kind = str(operation['kind'])
                values = _operation_values(operation, kind, {'op', 'kind', 'parent', 'values'}, 'upsert', strict_fields=strict_fields)
                value, created = editor.upsert(kind, parent=operation.get('parent'), values=values, normalize=False)
                results.append({'index': index, 'op': op, 'ok': True, 'created': created, **_result_entity(value, kind)})
            elif op == 'project_update':
                values = _operation_values(operation, 'project', {'op', 'values', 'unset'}, 'project_update', strict_fields=strict_fields)
                unset = _string_list(operation.get('unset', []), 'project_update.unset')
                editor.update_project(values=values, unset=unset, normalize=False)
                results.append({'index': index, 'op': op, 'ok': True, 'updated_fields': sorted(values), 'unset': unset})
            elif op == 'update':
                reference = _reference(operation)
                resolved = editor.resolve(reference, operation.get('kind'))
                values = _operation_values(operation, resolved.kind, {'op', 'reference', 'ref', 'kind', 'values', 'unset'}, 'update', strict_fields=strict_fields)
                unset = _string_list(operation.get('unset', []), 'update.unset')
                value = editor.update(reference, kind=operation.get('kind'), values=values, unset=unset, normalize=False)
                results.append({'index': index, 'op': op, 'ok': True, **_result_entity(value, operation.get('kind'))})
            elif op == 'update_many':
                if 'references' in operation and 'refs' in operation:
                    raise ValueError('use either references or refs, not both')
                explicit = _string_list(operation.get('references', operation.get('refs')), 'update_many.references')
                allowed = {str(operation['kind'])} if operation.get('kind') else None
                refs = resolve_bulk_refs(working, explicit=explicit, where=operation.get('where'), expect=operation.get('expect'), allow_empty=bool(operation.get('allow_empty', False)), allowed_kinds=allowed, label='update_many.references')
                resolved = editor.resolve(refs[0], operation.get('kind'))
                values = _operation_values(operation, resolved.kind, {'op', 'references', 'refs', 'kind', 'values', 'unset', 'where', 'expect', 'allow_empty'}, 'update_many', strict_fields=strict_fields)
                unset = _string_list(operation.get('unset', []), 'update_many.unset')
                changed = []
                for ref in refs:
                    current = editor.resolve(ref, operation.get('kind'))
                    if current.kind != resolved.kind:
                        raise ValueError('update_many selected mixed entity kinds; specify kind or narrow where')
                    value = editor.update(ref, kind=operation.get('kind'), values=values, unset=unset, normalize=False)
                    changed.append(_result_entity(value, operation.get('kind')))
                results.append({'index': index, 'op': op, 'ok': True, 'count': len(changed), 'matched_ids': refs, 'entities': changed})
            elif op in {'require', 'exclude'}:
                targets = _bulk_refs(working, operation, 'targets', 'target', label=f'{op}.targets')
                source = str(operation.get('source', '')).strip()
                if not source:
                    raise ValueError(f'{op}.source is required')
                editor.resolve(source)
                created = 0
                ids = []
                required = op == 'require'
                for target in targets:
                    value, was_created = _ensure_simple_requirement(editor, target, source, required)
                    created += int(was_created)
                    ids.append(value.get('id'))
                results.append({'index': index, 'op': op, 'ok': True, 'targets': len(targets), 'created': created, 'requirement_ids': ids})
            elif op == 'gate':
                targets = _bulk_refs(working, operation, 'targets', 'target', allowed_kinds={'row','backpack_row','choice','addon','selectable_addon'}, label='gate.targets')
                source = str(operation.get('source', '')).strip()
                if not source:
                    raise ValueError('gate.source is required')
                editor.resolve(source)
                hidden = bool(operation.get('hidden', True))
                required = bool(operation.get('required', True))
                created = 0
                ids = []
                for target in targets:
                    ent = editor.resolve(target)
                    if ent.kind not in {'row', 'backpack_row', 'choice', 'addon', 'selectable_addon'}:
                        raise ValueError(f'gate target is not displayable content: {target}')
                    value, was_created = _ensure_simple_requirement(editor, target, source, required)
                    created += int(was_created)
                    ids.append(value.get('id'))
                    _set_hidden_when_unmet(ent, hidden)
                results.append({'index': index, 'op': op, 'ok': True, 'targets': len(targets), 'created': created, 'hidden': hidden, 'requirement_ids': ids})
            elif op == 'ungate':
                targets = _bulk_refs(working, operation, 'targets', 'target', allowed_kinds={'row','backpack_row','choice','addon','selectable_addon'}, label='ungate.targets')
                source = str(operation.get('source', '')).strip()
                if not source:
                    raise ValueError('ungate.source is required')
                removed = 0
                for target in targets:
                    ent = editor.resolve(target)
                    reqs = ent.value.get('requireds', [])
                    if not isinstance(reqs, list):
                        raise ValueError(f'{target}.requireds is not an array')
                    kept = []
                    for req in reqs:
                        if isinstance(req, dict) and req.get('type') == 'id' and str(req.get('reqId', '')) == source and not req.get('requireds') and not req.get('orRequireds'):
                            removed += 1
                            continue
                        kept.append(req)
                    ent.value['requireds'] = kept
                    if bool(operation.get('restore_visibility', True)):
                        _set_hidden_when_unmet(ent, False)
                results.append({'index': index, 'op': op, 'ok': True, 'targets': len(targets), 'removed': removed})
            elif op == 'score_many':
                targets = _bulk_refs(working, operation, 'targets', 'target', allowed_kinds={'choice','selectable_addon'}, label='score_many.targets')
                point = str(operation.get('point', '')).strip()
                if not point:
                    raise ValueError('score_many.point is required')
                editor.resolve(point, 'point')
                amount = operation.get('value')
                if not isinstance(amount, (int, float)) or isinstance(amount, bool):
                    raise ValueError('score_many.value must be numeric')
                created = 0
                score_ids = []
                for target in targets:
                    value, was_created = _ensure_simple_score(editor, target, point, amount)
                    created += int(was_created)
                    score_ids.append(value.get('idx'))
                results.append({'index': index, 'op': op, 'ok': True, 'targets': len(targets), 'created': created, 'score_ids': score_ids})
            elif op == 'group_members':
                group_id = str(operation.get('group', '')).strip()
                if not group_id:
                    raise ValueError('group_members.group is required')
                group_ent = editor.resolve(group_id, 'group')
                refs = _bulk_refs(working, operation, 'members', 'member', allowed_kinds={'row','backpack_row','choice','selectable_addon'}, label='group_members.members')
                remove = bool(operation.get('remove', False))
                for ref in refs:
                    ent = editor.resolve(ref)
                    if ent.kind in {'choice', 'selectable_addon'}:
                        groups = ent.value.setdefault('groups', [])
                        member_field = 'elements'
                    elif ent.kind in {'row', 'backpack_row'}:
                        groups = ent.value.setdefault('groups', [])
                        member_field = 'rowElements'
                    else:
                        raise ValueError(f'group member must be a row, choice, or selectable addon: {ref}')
                    if not isinstance(groups, list):
                        raise ValueError(f'{ref}.groups is not an array')
                    members = group_ent.value.setdefault(member_field, [])
                    if not isinstance(members, list):
                        raise ValueError(f'{group_id}.{member_field} is not an array')
                    if remove:
                        ent.value['groups'] = [x for x in groups if x != group_id]
                        group_ent.value[member_field] = [x for x in members if x != ent.id]
                    else:
                        if group_id not in groups:
                            groups.append(group_id)
                        if ent.id not in members:
                            members.append(ent.id)
                results.append({'index': index, 'op': op, 'ok': True, 'group': group_id, 'members': len(refs), 'remove': remove})
            elif op == 'design_group_members':
                group_id = str(operation.get('group', '')).strip()
                if not group_id:
                    raise ValueError('design_group_members.group is required')
                group_ent = editor.resolve(group_id)
                if group_ent.kind not in {'row_design_group', 'choice_design_group'}:
                    raise ValueError('design_group_members.group must be a Row or Choice design group')
                refs = _bulk_refs(working, operation, 'members', 'member', allowed_kinds={'row','backpack_row','choice','group'}, label='design_group_members.members')
                remove = bool(operation.get('remove', False))
                for ref in refs:
                    ent = editor.resolve(ref)
                    if ent.kind == 'group':
                        side_field = 'designGroups'
                        member_field = 'groupElements'
                    elif group_ent.kind == 'row_design_group':
                        if ent.kind not in {'row', 'backpack_row'}:
                            raise ValueError(f'Row design group member must be a row or Group: {ref}')
                        side_field = 'rowDesignGroups'
                        member_field = 'backpackElements' if ent.kind == 'backpack_row' else 'elements'
                    else:
                        if ent.kind != 'choice':
                            raise ValueError(f'Choice design group member must be a choice or Group: {ref}')
                        side_field = 'objectDesignGroups'
                        member_field = 'backpackElements' if ent.path.startswith('/backpack/') else 'elements'
                    side = ent.value.setdefault(side_field, [])
                    members = group_ent.value.setdefault(member_field, [])
                    if not isinstance(side, list) or not isinstance(members, list):
                        raise ValueError('design group membership field is not an array')
                    if remove:
                        ent.value[side_field] = [x for x in side if x != group_id]
                        group_ent.value[member_field] = [x for x in members if x != ent.id]
                    else:
                        if group_id not in side:
                            side.append(group_id)
                        if ent.id not in members:
                            members.append(ent.id)
                results.append({'index': index, 'op': op, 'ok': True, 'group': group_id, 'members': len(refs), 'remove': remove})
            elif op == 'effects':
                targets = _bulk_refs(working, operation, 'targets', 'target', allowed_kinds={'choice','selectable_addon'}, label='effects.targets')
                spec = operation.get('effects')
                if not isinstance(spec, dict):
                    raise ValueError('effects.effects must be an object')
                for target in targets:
                    ent = editor.resolve(target)
                    apply_choice_effects(ent.value, copy.deepcopy(spec))
                results.append({'index': index, 'op': op, 'ok': True, 'count': len(targets), 'matched_ids': targets})
            elif op == 'hide_contents':
                source = str(operation.get('source', '')).strip()
                ent = editor.resolve(source)
                if ent.kind not in {'choice', 'selectable_addon'}:
                    raise ValueError('hide_contents.source must be a choice or selectable addon')
                rows = _one_or_many(operation, 'rows', 'row')
                for row_id in rows:
                    row_ent = editor.resolve(row_id)
                    if row_ent.kind not in {'row', 'backpack_row'}:
                        raise ValueError(f'hide_contents row target is not a row: {row_id}')
                raw_contents = _one_or_many(operation, 'contents', 'content')
                codes = []
                for raw in raw_contents:
                    key = raw.strip().lower().replace('-', '_').replace(' ', '_')
                    code = HIDE_CONTENT_TYPES.get(key)
                    if not code:
                        raise ValueError(f'unknown hide_contents content type: {raw!r}')
                    if code not in codes:
                        codes.append(code)
                ent.value['isContentHidden'] = True
                ent.value['hiddenContentsRow'] = rows
                ent.value['hiddenContentsType'] = codes
                results.append({'index': index, 'op': op, 'ok': True, 'source': source, 'rows': rows, 'content_codes': codes})
            elif op == 'clear_hide_contents':
                source = str(operation.get('source', '')).strip()
                ent = editor.resolve(source)
                for field in ('isContentHidden','hiddenContentsRow','hiddenContentsType'):
                    ent.value.pop(field, None)
                results.append({'index': index, 'op': op, 'ok': True, 'source': source})
            elif op == 'row_sort':
                row = str(operation.get('row', '')).strip()
                if not row:
                    raise ValueError('row_sort.row is required')
                mode = str(operation.get('by', '')).strip()
                if not mode:
                    raise ValueError('row_sort.by is required')
                order = sort_row_choices(working, row, mode)
                results.append({'index': index, 'op': op, 'ok': True, 'row': row, 'by': mode, 'order': order})
            elif op in {'row_copy_choices', 'row_move_choices'}:
                source = str(operation.get('source', '')).strip()
                target = str(operation.get('target', '')).strip()
                if not source or not target:
                    raise ValueError(f'{op}.source and {op}.target are required')
                source_ent = editor.resolve(source)
                target_ent = editor.resolve(target)
                if source_ent.kind not in {'row', 'backpack_row'} or target_ent.kind not in {'row', 'backpack_row'}:
                    raise ValueError(f'{op} source and target must be Rows')
                if source_ent.id == target_ent.id:
                    raise ValueError(f'{op} source and target must be different Rows')
                objects = source_ent.value.get('objects')
                if not isinstance(objects, list):
                    raise ValueError(f'{source}.objects is not an array')
                ids = [str(choice.get('id', '')) for choice in objects if isinstance(choice, dict) and choice.get('id')]
                changed = []
                for ref in ids:
                    if op == 'row_copy_choices':
                        changed.append(editor.clone(ref, parent=target, normalize=False))
                    else:
                        changed.append(editor.move(ref, parent=target, normalize=False))
                results.append({'index': index, 'op': op, 'ok': True, 'source': source, 'target': target, 'count': len(changed), 'entities': changed})
            elif op == 'design_import':
                target = str(operation.get('target', '')).strip()
                if not target:
                    raise ValueError('design_import.target is required')
                value = operation.get('design')
                if not isinstance(value, dict):
                    raise ValueError('design_import.design must be a design JSON object')
                imported = import_design(working, target, copy.deepcopy(value))
                results.append({'index': index, 'op': op, 'ok': True, 'design': imported})
            elif op == 'reorder':
                kind = str(operation.get('kind', '')).strip()
                if not kind:
                    raise ValueError('reorder.kind is required')
                order = _string_list(operation.get('order'), 'reorder.order')
                final = editor.reorder(kind, order, parent=operation.get('parent'), partial=bool(operation.get('partial', False)))
                results.append({'index': index, 'op': op, 'ok': True, 'kind': kind, 'parent': operation.get('parent'), 'order': final})
            elif op == 'move':
                reference = _reference(operation)
                parent = str(operation.get('parent', '')).strip()
                if not parent:
                    raise ValueError('move.parent is required')
                pos = operation.get('index')
                if pos is not None and (not isinstance(pos, int) or isinstance(pos, bool)):
                    raise ValueError('move.index must be an integer')
                moved = editor.move(reference, parent=parent, index=pos, normalize=False)
                results.append({'index': index, 'op': op, 'ok': True, 'moved': moved})
            elif op == 'clone':
                reference = _reference(operation)
                pos = operation.get('index')
                if pos is not None and (not isinstance(pos, int) or isinstance(pos, bool)):
                    raise ValueError('clone.index must be an integer')
                cloned = editor.clone(reference, parent=operation.get('parent'), index=pos, normalize=False)
                results.append({'index': index, 'op': op, 'ok': True, 'cloned': cloned})
            elif op == 'delete_many':
                explicit = _string_list(operation.get('references', operation.get('refs')), 'delete_many.references')
                allowed = {str(operation['kind'])} if operation.get('kind') else None
                refs = resolve_bulk_refs(working, explicit=explicit, where=operation.get('where'), expect=operation.get('expect'), allow_empty=bool(operation.get('allow_empty', False)), allowed_kinds=allowed, label='delete_many.references')
                removed = []
                for ref in refs:
                    removed.append(editor.delete(ref, kind=operation.get('kind'), normalize=False))
                results.append({'index': index, 'op': op, 'ok': True, 'count': len(removed), 'removed': removed})
            elif op == 'delete':
                removed = editor.delete(_reference(operation), kind=operation.get('kind'), normalize=False)
                results.append({'index': index, 'op': op, 'ok': True, 'removed': removed})
            elif op == 'rename':
                editor.rename(str(operation['old']), str(operation['new']), normalize=False)
                results.append({'index': index, 'op': op, 'ok': True, 'old': operation['old'], 'new': operation['new']})
            elif op == 'set':
                editor.set(str(operation['pointer']), copy.deepcopy(operation.get('value')))
                results.append({'index': index, 'op': op, 'ok': True, 'pointer': operation['pointer']})
            elif op == 'remove':
                removed = editor.remove(str(operation['pointer']))
                results.append({'index': index, 'op': op, 'ok': True, 'pointer': operation['pointer'], 'removed': removed})
            elif op == 'assert':
                if 'pointer' in operation:
                    actual = pointer_get(working, str(operation['pointer']))
                    if 'equals' in operation and actual != operation['equals']:
                        raise ValueError(f"assert failed at {operation['pointer']}: expected {operation['equals']!r}, got {actual!r}")
                    results.append({'index': index, 'op': op, 'ok': True, 'pointer': operation['pointer'], 'actual': actual})
                else:
                    reference = _reference(operation)
                    found = editor.resolve(reference, operation.get('kind'))
                    results.append({'index': index, 'op': op, 'ok': True, 'reference': reference, 'path': found.path, 'kind': found.kind})
            elif op == 'normalize':
                changes = editor.normalize()
                results.append({'index': index, 'op': op, 'ok': True, 'changes': changes})
            else:
                raise ValueError(f'unknown operation {op!r}')
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            return project, {
                'ok': False,
                'stage': 'operation',
                'operation_index': index,
                'operation': operation,
                'error': str(exc),
                'results': results,
            }

    try:
        changes = editor.normalize_and_check()
    except ValueError as exc:
        return project, {
            'ok': False,
            'stage': 'identity',
            'error': str(exc),
            'results': results,
        }
    report: dict[str, Any] = {
        'ok': True,
        'operations_applied': len(operations),
        'results': results,
        'normalization_changes': changes,
    }
    if validate_after:
        report['validation'] = validate(working)
    return working, report
