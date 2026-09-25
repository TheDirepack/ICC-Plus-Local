from __future__ import annotations

import copy
from typing import Any

from .editor import _deep_merge, make_entity, new_project
from .identity import IdentityAllocator
from .effects import apply_choice_effects
from .project_integrity import hydrate_project
from .validation import validate_complete

ENTITY_ARRAYS = {
    'pointTypes': 'point',
    'variables': 'variable',
    'words': 'word',
    'groups': 'group',
    'rowDesignGroups': 'row_design_group',
    'objectDesignGroups': 'choice_design_group',
    'globalRequirements': 'global_requirement',
    'soundEffects': 'sound_effect',
}


def _objects(value: Any) -> list[dict[str, Any]]:
    return [x for x in value if isinstance(x, dict)] if isinstance(value, list) else []


def _list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _apply_defaults(defaults: dict[str, Any], kind: str, source: dict[str, Any]) -> dict[str, Any]:
    base = defaults.get(kind, {})
    if not isinstance(base, dict):
        base = {}
    return _deep_merge(base, source)


def _reserve_entity(allocator: IdentityAllocator, kind: str, source: dict[str, Any]) -> None:
    # ICC Plus ordinary Requirements and non-selectable Addons use id: ""
    # and are not entered in the runtime identity maps.
    if kind not in {'requirement', 'addon'}:
        key = 'idx' if kind == 'score' else 'id'
        value = source.get(key)
        if value is not None and str(value).strip():
            allocator.reserve(str(value))
    for req in _objects(source.get('requireds')):
        _reserve_entity(allocator, 'requirement', req)
    for req in _objects(source.get('orRequireds')):
        _reserve_entity(allocator, 'requirement', req)
    if kind in {'choice', 'selectable_addon'}:
        for score in _objects(source.get('scores')):
            _reserve_entity(allocator, 'score', score)
    if kind == 'choice':
        for addon in _objects(source.get('addons')):
            _reserve_entity(allocator, 'selectable_addon' if addon.get('isSelectable') is True else 'addon', addon)


def _reserve_explicit_ids(fragment: dict[str, Any]) -> IdentityAllocator:
    allocator = IdentityAllocator()
    for key, kind in ENTITY_ARRAYS.items():
        for value in _objects(fragment.get(key)):
            _reserve_entity(allocator, kind, value)
    for key, kind in (('rows', 'row'), ('backpack', 'backpack_row')):
        for row in _objects(fragment.get(key)):
            _reserve_entity(allocator, kind, row)
            for choice in _objects(row.get('objects', row.get('choices'))):
                _reserve_entity(allocator, 'choice', choice)
    return allocator


def _simple_req_key(req: dict[str, Any]) -> tuple[Any, ...] | None:
    if req.get('type') != 'id' or req.get('requireds') or req.get('orRequireds'):
        return None
    return ('id', bool(req.get('required', True)), str(req.get('reqId', '')))


def _add_req_aliases(values: dict[str, Any]) -> None:
    requireds = _objects(values.get('requireds'))
    seen = {k for r in requireds if (k := _simple_req_key(r)) is not None}
    for required, key in ((True, 'requires'), (False, 'excludes')):
        raw = values.pop(key, None)
        for target in _list(raw):
            target = str(target).strip()
            if not target:
                continue
            semantic = ('id', required, target)
            if semantic in seen:
                continue
            requireds.append({'type': 'id', 'required': required, 'reqId': target})
            seen.add(semantic)
    if requireds or 'requireds' in values:
        values['requireds'] = requireds


def _apply_hidden_until(values: dict[str, Any], *, choice_like: bool = False) -> None:
    """Expand a script-friendly hidden-until alias into ICC Plus fields.

    Rows disappear automatically while their requirements are unmet. Choices
    need the requirement-visibility filter enabled as well. Addons already use
    requirement state for whether they are shown.
    """
    raw = values.pop('hidden_until', None)
    if raw is None:
        raw = values.pop('visible_if', None)
    if raw is None:
        return
    current = values.get('requires')
    merged = _list(current) + _list(raw)
    values['requires'] = list(dict.fromkeys(str(x).strip() for x in merged if str(x).strip()))
    if choice_like:
        values['privateFilterIsOn'] = True
        styling = values.get('styling')
        if not isinstance(styling, dict):
            styling = {}
        styling = _deep_merge(styling, {'reqFilterVisibleIsOn': True})
        values['styling'] = styling


def _add_cost_alias(values: dict[str, Any]) -> None:
    costs = values.pop('costs', None)
    if costs is None:
        return
    if not isinstance(costs, dict):
        raise ValueError('costs must be an object mapping point IDs to numeric values')
    scores = _objects(values.get('scores'))
    existing = {str(x.get('id', '')) for x in scores if x.get('id')}
    for point_id, amount in costs.items():
        if str(point_id) in existing:
            raise ValueError(f'costs duplicates an explicit score for point {point_id!r}')
        if not isinstance(amount, (int, float)) or isinstance(amount, bool):
            raise ValueError(f'cost for point {point_id!r} must be numeric')
        scores.append({'id': str(point_id), 'value': amount})
        existing.add(str(point_id))
    values['scores'] = scores


def _add_choice_aliases(values: dict[str, Any], *, choice_like: bool = True) -> None:
    _apply_hidden_until(values, choice_like=choice_like)
    _add_req_aliases(values)
    _add_cost_alias(values)
    effects = values.pop('effects', None)
    apply_choice_effects(values, effects, consume_legacy=True)


def _build_requirement(project: dict[str, Any], source: dict[str, Any], *, allocator: IdentityAllocator, defaults: dict[str, Any], parent: str) -> dict[str, Any]:
    values = _apply_defaults(defaults, 'requirement', copy.deepcopy(source))
    nested = values.pop('requireds', None)
    alternatives = values.pop('orRequireds', None)
    req = make_entity(project, 'requirement', values, allocator=allocator, parent=parent)
    if nested is not None:
        req['requireds'] = [_build_requirement(project, x, allocator=allocator, defaults=defaults, parent=parent) for x in _objects(nested)]
    if alternatives is not None:
        req['orRequireds'] = [_build_requirement(project, x, allocator=allocator, defaults=defaults, parent=parent) for x in _objects(alternatives)]
    return req


def _build_score(project: dict[str, Any], source: dict[str, Any], *, allocator: IdentityAllocator, defaults: dict[str, Any], parent: str) -> dict[str, Any]:
    values = _apply_defaults(defaults, 'score', copy.deepcopy(source))
    requireds = values.pop('requireds', None)
    score = make_entity(project, 'score', values, allocator=allocator, parent=parent)
    sid = str(score['idx'])
    if requireds is not None:
        score['requireds'] = [_build_requirement(project, x, allocator=allocator, defaults=defaults, parent=sid) for x in _objects(requireds)]
    return score


def _build_addon(project: dict[str, Any], source: dict[str, Any], parent_id: str, *, allocator: IdentityAllocator, defaults: dict[str, Any]) -> dict[str, Any]:
    kind = 'selectable_addon' if source.get('isSelectable') is True else 'addon'
    values = _apply_defaults(defaults, kind, copy.deepcopy(source))
    if kind == 'selectable_addon':
        _add_choice_aliases(values, choice_like=False)
    else:
        _apply_hidden_until(values, choice_like=False)
        _add_req_aliases(values)
    requireds = values.pop('requireds', None)
    scores = values.pop('scores', None)
    addon = make_entity(project, kind, values, allocator=allocator, parent=parent_id)
    aid = str(addon.get('id', ''))
    child_parent = aid if kind == 'selectable_addon' and aid else parent_id
    if kind == 'selectable_addon':
        addon['parentId'] = parent_id
        if scores is not None:
            addon['scores'] = [_build_score(project, x, allocator=allocator, defaults=defaults, parent=child_parent) for x in _objects(scores)]
    if requireds is not None:
        addon['requireds'] = [_build_requirement(project, x, allocator=allocator, defaults=defaults, parent=child_parent) for x in _objects(requireds)]
    return addon


def _build_choice(project: dict[str, Any], source: dict[str, Any], index: int, *, allocator: IdentityAllocator, defaults: dict[str, Any], parent: str) -> dict[str, Any]:
    values = _apply_defaults(defaults, 'choice', copy.deepcopy(source))
    _add_choice_aliases(values)
    requireds = values.pop('requireds', None)
    scores = values.pop('scores', None)
    addons = values.pop('addons', None)
    values['index'] = index
    choice = make_entity(project, 'choice', values, allocator=allocator, parent=parent)
    cid = str(choice['id'])
    if requireds is not None:
        choice['requireds'] = [_build_requirement(project, x, allocator=allocator, defaults=defaults, parent=cid) for x in _objects(requireds)]
    if scores is not None:
        choice['scores'] = [_build_score(project, x, allocator=allocator, defaults=defaults, parent=cid) for x in _objects(scores)]
    if addons is not None:
        choice['addons'] = [_build_addon(project, x, cid, allocator=allocator, defaults=defaults) for x in _objects(addons)]
    return choice


def _build_row(project: dict[str, Any], source: dict[str, Any], index: int, *, backpack: bool, allocator: IdentityAllocator, defaults: dict[str, Any]) -> dict[str, Any]:
    kind = 'backpack_row' if backpack else 'row'
    values = _apply_defaults(defaults, kind, copy.deepcopy(source))
    if backpack and not defaults.get('backpack_row'):
        values = _deep_merge(defaults.get('row', {}) if isinstance(defaults.get('row'), dict) else {}, values)
    if 'pick' in values:
        if 'allowedChoices' in values:
            raise ValueError('row cannot use both pick and allowedChoices')
        values['allowedChoices'] = values.pop('pick')
    _apply_hidden_until(values, choice_like=False)
    _add_req_aliases(values)
    requireds = values.pop('requireds', None)
    objects = values.pop('objects', values.pop('choices', None))
    values['index'] = index
    row = make_entity(project, kind, values, allocator=allocator)
    rid = str(row['id'])
    if backpack:
        row['isBackpack'] = True
    if requireds is not None:
        row['requireds'] = [_build_requirement(project, x, allocator=allocator, defaults=defaults, parent=rid) for x in _objects(requireds)]
    if objects is not None:
        row['objects'] = [_build_choice(project, x, i, allocator=allocator, defaults=defaults, parent=rid) for i, x in enumerate(_objects(objects))]
    return row


def build_project(fragment: dict[str, Any]) -> dict[str, Any]:
    """Build a complete project from a compact, script-friendly ICC-shaped document."""
    if not isinstance(fragment, dict):
        raise ValueError('generation input must be a JSON object')

    defaults: dict[str, Any] = {}
    if fragment.get('format') == 'iccplus-generation-script':
        defaults_raw = fragment.get('defaults', {})
        if not isinstance(defaults_raw, dict):
            raise ValueError('generation script defaults must be an object')
        defaults = defaults_raw
        payload = fragment.get('project', {})
        if not isinstance(payload, dict):
            raise ValueError('generation script project must be an object')
        fragment = payload

    allocator = _reserve_explicit_ids(fragment)
    project = new_project()
    special = set(ENTITY_ARRAYS) | {'rows', 'backpack', 'categories'}
    for key, value in fragment.items():
        if key not in special:
            # Preserve the official Creator baseline for structured project
            # sections such as styling and viewerConfig. A compact fragment
            # supplies overrides, not a replacement for the rest of the
            # official section.
            if isinstance(value, dict) and isinstance(project.get(key), dict):
                project[key] = _deep_merge(project[key], value)
            else:
                project[key] = copy.deepcopy(value)

    for key, kind in ENTITY_ARRAYS.items():
        if key in fragment:
            values = []
            for source in _objects(fragment.get(key)):
                merged = _apply_defaults(defaults, kind, source)
                if kind in {'global_requirement', 'sound_effect'}:
                    reqs = merged.pop('requireds', None)
                else:
                    reqs = None
                item = make_entity(project, kind, merged, allocator=allocator)
                if reqs is not None:
                    item['requireds'] = [_build_requirement(project, x, allocator=allocator, defaults=defaults, parent=str(item['id'])) for x in _objects(reqs)]
                values.append(item)
            project[key] = values

    if 'categories' in fragment:
        categories = copy.deepcopy(fragment['categories']) if isinstance(fragment['categories'], list) else []
        used: dict[str, set[int]] = {}
        for cat in categories:
            if not isinstance(cat, dict):
                continue
            typ = str(cat.get('type', ''))
            if isinstance(cat.get('idx'), int):
                idx = int(cat['idx'])
                if idx in used.setdefault(typ, set()):
                    raise ValueError(f'duplicate category identity: {typ}:{idx}')
                used[typ].add(idx)
        for cat in categories:
            if not isinstance(cat, dict) or isinstance(cat.get('idx'), int):
                continue
            typ = str(cat.get('type', ''))
            idx = 0
            while idx in used.setdefault(typ, set()):
                idx += 1
            cat['idx'] = idx
            used[typ].add(idx)
        project['categories'] = categories

    if 'rows' in fragment:
        project['rows'] = [_build_row(project, x, i, backpack=False, allocator=allocator, defaults=defaults) for i, x in enumerate(_objects(fragment.get('rows')))]
    if 'backpack' in fragment:
        project['backpack'] = [_build_row(project, x, i, backpack=True, allocator=allocator, defaults=defaults) for i, x in enumerate(_objects(fragment.get('backpack')))]

    # ICC Plus stores Group and design-group membership on both sides. Treat
    # explicit reverse member arrays as authoring input and copy them to the
    # member side, which ProjectEditor.normalize() uses as canonical.
    from .model import ProjectIndex
    idx = ProjectIndex(project)
    for group in idx.by_kind.get('group', []):
        for field, allowed in (('elements', {'choice', 'selectable_addon'}), ('rowElements', {'row', 'backpack_row'})):
            members = [str(x) for x in group.value.get(field, []) if isinstance(x, str)] if isinstance(group.value.get(field), list) else []
            for member_id in members:
                member = idx.one(member_id)
                if member is None or member.kind not in allowed:
                    continue
                side = member.value.setdefault('groups', [])
                if isinstance(side, list) and group.id not in side:
                    side.append(group.id)

    for design_kind, side_field in (('row_design_group', 'rowDesignGroups'), ('choice_design_group', 'objectDesignGroups')):
        for design in idx.by_kind.get(design_kind, []):
            for field in ('elements', 'backpackElements'):
                members = [str(x) for x in design.value.get(field, []) if isinstance(x, str)] if isinstance(design.value.get(field), list) else []
                for member_id in members:
                    member = idx.one(member_id)
                    allowed = {'row', 'backpack_row'} if design_kind == 'row_design_group' else {'choice'}
                    if member is None or member.kind not in allowed:
                        continue
                    side = member.value.setdefault(side_field, [])
                    if isinstance(side, list) and design.id not in side:
                        side.append(design.id)
            group_members = [str(x) for x in design.value.get('groupElements', []) if isinstance(x, str)] if isinstance(design.value.get('groupElements'), list) else []
            for member_id in group_members:
                member = idx.one(member_id, 'group')
                if member is None:
                    continue
                side = member.value.setdefault('designGroups', [])
                if isinstance(side, list) and design.id not in side:
                    side.append(design.id)
    hydrate_project(project, upgrade_version=True)
    report = validate_complete(project)
    if not report['valid']:
        first = next((d for d in report['diagnostics'] if d.get('severity') == 'error'), None)
        message = first.get('message') if isinstance(first, dict) else 'complete project validation failed'
        raise ValueError(f'generated project is not Creator-complete: {message}')
    return project
