from __future__ import annotations

from typing import Any

from .agent_protocol import AGENT_SCRIPT_KEYS, strict_agent_operation_keys
from .field_catalog import FIELD_CATALOG, suggest_fields
from .model import ProjectIndex
from .operations import apply_operation_script, load_operation_script

PHASE_FORMATS = {
    'structure': 'iccplus-structure-ops',
    'rules': 'iccplus-rules-ops',
}

STRUCTURE_KINDS = {'row', 'backpack_row', 'choice', 'addon', 'selectable_addon', 'category'}
STRUCTURE_OPS = {
    'add', 'upsert', 'update', 'delete', 'rename',
    'reorder', 'move', 'clone', 'row_sort', 'row_copy_choices', 'row_move_choices',
    'assert', 'normalize',
}

STRUCTURE_FIELDS: dict[str, set[str]] = {
    'row': {
        'id', 'index', 'isBackpack', 'title', 'titleText', 'debugTitle',
        'isInfoRow', 'isGroupRow',
    },
    'backpack_row': {
        'id', 'index', 'isBackpack', 'title', 'titleText', 'debugTitle',
        'isInfoRow', 'isGroupRow',
    },
    'choice': {'id', 'index', 'title', 'text', 'debugTitle'},
    'addon': {'id', 'title', 'text', 'parentId', 'skipIndex'},
    'selectable_addon': {'id', 'title', 'text', 'parentId', 'skipIndex'},
    'category': {'idx', 'name', 'type'},
}

RULE_ENTITY_KINDS = {
    'point', 'variable', 'word', 'group', 'global_requirement', 'sound_effect',
    'score', 'requirement',
}
RULE_TARGET_KINDS = {'row', 'backpack_row', 'choice', 'addon', 'selectable_addon'}
RULES_OPS = {
    'add', 'upsert', 'update', 'delete',
    'require', 'exclude', 'gate', 'ungate', 'score_many', 'group_members',
    'effects', 'hide_contents', 'clear_hide_contents', 'assert', 'normalize',
}

RULE_FIELDS: dict[str, set[str]] = {
    'row': {
        'allowedChoices', 'isResultRow', 'resultGroupId', 'isButtonRow', 'buttonType', 'buttonId', 'buttonText',
        'buttonRandom', 'buttonRandomNumber', 'isWeightedRandom',
        'allowActivateUnselectable', 'deselectChoices', 'buttonTypeRadio',
        'btnPointAddon', 'pointTypeRandom', 'randomMin', 'randomMax',
        'onlyUnselectedChoices', 'onlyIfNoChoices', 'requireds', 'groups',
    },
    'backpack_row': {
        'allowedChoices', 'isResultRow', 'resultGroupId', 'isButtonRow', 'buttonType', 'buttonId', 'buttonText',
        'buttonRandom', 'buttonRandomNumber', 'isWeightedRandom',
        'allowActivateUnselectable', 'deselectChoices', 'buttonTypeRadio',
        'btnPointAddon', 'pointTypeRandom', 'randomMin', 'randomMax',
        'onlyUnselectedChoices', 'onlyIfNoChoices', 'requireds', 'groups',
    },
    'choice': {
        'requireds', 'scores', 'groups', 'linkedObjects', 'multipleUseVariable',
        'initMultipleTimesMinus', 'hideMultipleCounter', 'allowSelectByClick',
        'hideCounterUntilSelect', 'isSelectableMultiple', 'isMultipleUseVariable',
        'multipleScoreId', 'numMultipleTimesMinus', 'numMultipleTimesPluss',
        'isNotSelectable', 'selectOnce', 'notDeselectedByClean', 'isNotResult',
        'isNotBuild', 'cleanACtivatedOnSelect', 'isNotDeactivate',
        'isAllowDeselect', 'activateAfterReset', 'isNotActiveUnselectable',
        'randomWeight', 'isSelectDelayed', 'selectDelayTime', 'isDeselectDelayed',
        'deselectDelayTime', 'isNotSearchable', 'isAutoActive', 'isCountDisabled',
        'deselectWhenNoAddon', 'showScoreInAddon', 'showReqInAddon',
        'showMulInAddon',
    },
    'selectable_addon': {
        'requireds', 'scores', 'groups', 'multipleUseVariable', 'deselectParent',
        'countAsChoice', 'hideMultipleCounter', 'allowSelectByClick',
        'hideCounterUntilSelect', 'isSelectableMultiple', 'isMultipleUseVariable',
        'multipleScoreId', 'numMultipleTimesMinus', 'numMultipleTimesPluss',
        'isNotSelectable', 'selectOnce', 'notDeselectedByClean', 'isNotResult',
        'isNotBuild', 'cleanACtivatedOnSelect', 'isNotDeactivate',
        'isAllowDeselect', 'activateAfterReset', 'isNotActiveUnselectable',
        'randomWeight', 'isSelectDelayed', 'selectDelayTime', 'isDeselectDelayed',
        'deselectDelayTime', 'isNotSearchable', 'isAutoActive', 'isCountDisabled',
        'deselectWhenNoAddon', 'showScoreInAddon', 'showReqInAddon',
        'showMulInAddon', 'showAddon', 'hideAddon',
    },
    'addon': {'requireds', 'showAddon', 'hideAddon'},
    'point': {
        'id', 'name', 'startingSum', 'beforeText', 'afterText',
        'belowZeroNotAllowed', 'isNotShownPointBar', 'isNotShownObjects',
        'allowFloat', 'decimalPlaces', 'category', 'useScoreText',
        'scoreBeforeText', 'scoreAfterText',
    },
    'variable': {'id', 'isTrue', 'category'},
    'word': {'id', 'replaceText', 'category'},
    'group': {'id', 'name', 'category', 'elements', 'rowElements'},
    'global_requirement': {'id', 'name', 'category', 'requireds'},
    'sound_effect': {
        'id', 'name', 'audio', 'volume', 'pitch', 'isDefault', 'onSelected',
        'onDeselected', 'requireds', 'groups',
    },
    'requirement': set(FIELD_CATALOG.get('requirement', ())),
    'score': {
        'idx', 'id', 'value', 'type', 'beforeText', 'afterText', 'requireds',
        'showScore', 'hideValue', 'isNotRecalculatable', 'isNotRecalculateSelf',
        'isNotDiscountable', 'isRandom', 'minValue', 'maxValue', 'setValue',
        'notStackableDiscount', 'multiplyByTimes', 'displayMulScore',
        'replaceText', 'hideDisValue', 'hideDisIcon', 'useExpression',
        'expValue', 'expMinValue', 'expMaxValue',
    },
}




def _phase_operation_keys(op: str, generic_keys: dict[str, frozenset[str]]) -> set[str]:
    keys = set(generic_keys.get(op, ()))
    if op in {'add', 'upsert'}:
        keys.add('items')
    if op in {'update', 'delete'}:
        keys.update({'references', 'refs', 'where', 'expect', 'allow_empty'})
    return keys


def _target_mode(operation: dict[str, Any]) -> str:
    single = 'reference' in operation or 'ref' in operation
    explicit = 'references' in operation or 'refs' in operation
    selector = 'where' in operation
    count = int(single) + int(explicit) + int(selector)
    if count != 1:
        return 'invalid'
    return 'single' if single else 'bulk'


def _normalize_phase_operations(script: dict[str, Any]) -> list[dict[str, Any]]:
    """Expand phase-friendly batch shapes into the low-level atomic engine.

    The phase CLI keeps one public verb for one-or-many edits. `add`/`upsert`
    accept either `values` or `items`; `update`/`delete` accept one ref, many
    refs, or a selector. The low-level engine still uses its historical
    update_many/delete_many operations internally.
    """
    out: list[dict[str, Any]] = []
    for operation in script['operations']:
        op = str(operation.get('op', ''))
        if op in {'add', 'upsert'} and 'items' in operation:
            base = {k: v for k, v in operation.items() if k not in {'items', 'values'}}
            for item in operation['items']:
                expanded = dict(base)
                expanded['values'] = item
                out.append(expanded)
            continue
        if op in {'update', 'delete'} and _target_mode(operation) == 'bulk':
            expanded = dict(operation)
            expanded['op'] = 'update_many' if op == 'update' else 'delete_many'
            if isinstance(expanded.get('where'), dict) and operation.get('kind'):
                where = dict(expanded['where'])
                if 'kind' not in where and 'kinds' not in where:
                    where['kind'] = str(operation['kind'])
                expanded['where'] = where
            out.append(expanded)
            continue
        out.append(dict(operation))
    return out

def _script_error(label: str, message: str) -> ValueError:
    return ValueError(f'{label}: {message}')


def _suggest(kind: str, field: str, allowed: set[str]) -> str:
    matches = [x for x in suggest_fields('row' if kind == 'backpack_row' else kind, field, limit=3) if x in allowed]
    return f'; suggestions: {", ".join(matches)}' if matches else ''


def _validate_values(phase: str, kind: str, operation: dict[str, Any], index: int) -> None:
    values = operation.get('values', {})
    if values is None:
        values = {}
    if not isinstance(values, dict):
        raise _script_error(f'operation {index}', 'values must be an object')
    allowed = STRUCTURE_FIELDS.get(kind, set()) if phase == 'structure' else RULE_FIELDS.get(kind, set())
    unknown = sorted(set(values) - allowed)
    if unknown:
        details = []
        for field in unknown:
            details.append(field + _suggest(kind, field, allowed))
        other = 'rules' if phase == 'structure' else 'structure/style'
        raise _script_error(
            f'operation {index}',
            f'{phase} phase does not allow {kind} field(s): {", ".join(details)}; move those edits to the {other} phase or use low-level apply for an exceptional field',
        )
    unset = operation.get('unset', [])
    if isinstance(unset, str):
        unset = [unset]
    if unset is None:
        unset = []
    if not isinstance(unset, list) or any(not isinstance(x, str) for x in unset):
        raise _script_error(f'operation {index}', 'unset must be a string array')
    bad_unset = sorted(set(unset) - allowed)
    if bad_unset:
        raise _script_error(f'operation {index}', f'{phase} phase cannot unset {kind} field(s): {", ".join(bad_unset)}')


def validate_phase_script(script: dict[str, Any], phase: str, *, project: dict[str, Any] | None = None) -> dict[str, Any]:
    if phase not in PHASE_FORMATS:
        raise ValueError(f'unknown authoring phase: {phase}')
    if not isinstance(script, dict):
        raise ValueError(f'{phase} script must be an object')
    unknown_top = sorted(set(script) - AGENT_SCRIPT_KEYS)
    if unknown_top:
        raise ValueError(f'{phase} script has unknown top-level field(s): {", ".join(unknown_top)}')
    if script.get('format') != PHASE_FORMATS[phase]:
        raise ValueError(f'{phase} script format must be {PHASE_FORMATS[phase]!r}')
    if script.get('format_version') != 1:
        raise ValueError(f'{phase} script format_version must be 1')
    if script.get('strict_fields') is not True:
        raise ValueError(f'{phase} script requires strict_fields=true')
    operations = script.get('operations')
    if not isinstance(operations, list) or not operations:
        raise ValueError(f'{phase} script operations must be a non-empty array')

    generic_keys = strict_agent_operation_keys()
    allowed_ops = STRUCTURE_OPS if phase == 'structure' else RULES_OPS
    index = ProjectIndex(project) if project is not None else None

    for i, operation in enumerate(operations):
        if not isinstance(operation, dict):
            raise _script_error(f'operation {i}', 'must be an object')
        op = operation.get('op')
        if not isinstance(op, str) or op not in allowed_ops:
            raise _script_error(f'operation {i}', f'{op!r} is not allowed in the {phase} phase; allowed: {", ".join(sorted(allowed_ops))}')
        known_keys = _phase_operation_keys(op, generic_keys)
        if not known_keys:
            raise _script_error(f'operation {i}', f'unsupported operation {op!r}')
        extra = sorted(set(operation) - known_keys)
        if extra:
            raise _script_error(f'operation {i}', f'unknown {op} field(s): {", ".join(extra)}')

        if op in {'add', 'upsert'}:
            has_values = 'values' in operation
            has_items = 'items' in operation
            if has_values == has_items:
                raise _script_error(f'operation {i}', f'{op} requires exactly one of values or items')
            if has_items:
                items = operation.get('items')
                if not isinstance(items, list) or not items:
                    raise _script_error(f'operation {i}', 'items must be a non-empty array')
                if any(not isinstance(item, dict) for item in items):
                    raise _script_error(f'operation {i}', 'every items entry must be an object of native field values')

        if op in {'update', 'delete'}:
            mode = _target_mode(operation)
            if mode == 'invalid':
                raise _script_error(f'operation {i}', f'{op} requires exactly one target form: ref/reference, refs/references, or where')
            if 'references' in operation and 'refs' in operation:
                raise _script_error(f'operation {i}', 'use either references or refs, not both')

        kind = operation.get('kind')
        if op in {'add', 'upsert', 'update', 'update_many', 'delete', 'delete_many'}:
            if not isinstance(kind, str) or not kind:
                raise _script_error(f'operation {i}', f'{op} requires kind in a phase script')
            if phase == 'structure':
                if kind not in STRUCTURE_KINDS:
                    raise _script_error(f'operation {i}', f'{kind!r} belongs in rules or low-level apply, not structure')
            else:
                if op in {'add', 'upsert'} and kind not in RULE_ENTITY_KINDS:
                    raise _script_error(f'operation {i}', f'rules may add only rule entities: {", ".join(sorted(RULE_ENTITY_KINDS))}')
                if op in {'delete', 'delete_many'} and kind not in RULE_ENTITY_KINDS:
                    raise _script_error(f'operation {i}', f'rules may delete only rule entities: {", ".join(sorted(RULE_ENTITY_KINDS))}')
                if kind not in (RULE_ENTITY_KINDS | RULE_TARGET_KINDS):
                    raise _script_error(f'operation {i}', f'{kind!r} is not a rules-phase kind')
            if op in {'add', 'upsert'} and 'items' in operation:
                for item_index, item in enumerate(operation['items']):
                    try:
                        _validate_values(phase, kind, {'values': item}, i)
                    except ValueError as exc:
                        raise _script_error(f'operation {i}.items[{item_index}]', str(exc).split(': ', 1)[-1]) from exc
            elif op in {'add', 'upsert', 'update'}:
                _validate_values(phase, kind, operation, i)

        if phase == 'structure' and op == 'reorder':
            reorder_kind = operation.get('kind')
            if reorder_kind not in STRUCTURE_KINDS:
                raise _script_error(f'operation {i}', f'structure reorder cannot target {reorder_kind!r}')

        if phase == 'structure' and index is not None and op in {'move', 'clone'}:
            ref = operation.get('reference', operation.get('ref'))
            if isinstance(ref, str):
                ent = index.one(ref)
                if ent is not None and ent.kind not in STRUCTURE_KINDS:
                    raise _script_error(f'operation {i}', f'{op} target {ref!r} is {ent.kind}, not a structure entity')

        if phase == 'structure' and index is not None and op == 'rename':
            old = operation.get('old')
            if isinstance(old, str):
                ent = index.one(old)
                if ent is not None and ent.kind not in STRUCTURE_KINDS:
                    raise _script_error(f'operation {i}', f'rename target {old!r} is {ent.kind}, not a structure entity')

    return script


def load_phase_script(source: str, phase: str) -> dict[str, Any]:
    return validate_phase_script(load_operation_script(source), phase)


def apply_phase_script(project: dict[str, Any], script: dict[str, Any], phase: str, *, validate_after: bool = True) -> tuple[dict[str, Any], dict[str, Any]]:
    validate_phase_script(script, phase, project=project)
    expanded = _normalize_phase_operations(script)
    generic = {
        'format': 'iccplus-agent-ops',
        'format_version': 1,
        'strict_fields': True,
        'operations': expanded,
    }
    updated, result = apply_operation_script(project, generic, validate_after=validate_after)
    result['phase'] = phase
    result['format'] = PHASE_FORMATS[phase]
    result['requested_operation_count'] = len(script['operations'])
    result['executed_operation_count'] = len(expanded)
    return updated, result
