from __future__ import annotations

from typing import Any, Iterable

from .model import ProjectIndex, Entity


def _as_strings(value: Any, field: str) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list) or any(not isinstance(x, str) for x in value):
        raise ValueError(f'{field} must be a string or an array of strings')
    return list(dict.fromkeys(x.strip() for x in value if x.strip()))


def select_entities(project: dict[str, Any], where: dict[str, Any]) -> list[Entity]:
    """Select static project entities by stable structural metadata.

    Selectors intentionally avoid fuzzy matching. A generated mutation should be
    reproducible, so every filter is exact except explicit *_contains filters.
    """
    if not isinstance(where, dict):
        raise ValueError('where must be an object')
    allowed_keys = {
        'kind', 'kinds', 'id', 'ids', 'id_prefix', 'row', 'rows', 'parent',
        'parents', 'group', 'groups', 'title_contains', 'text_contains',
        'path_prefix', 'backpack',
    }
    unknown = set(where) - allowed_keys
    if unknown:
        raise ValueError(f'unknown where filter(s): {", ".join(sorted(unknown))}')

    idx = ProjectIndex(project)
    entities = list(idx.entities)

    kinds = _as_strings(where.get('kinds', where.get('kind')), 'where.kinds')
    if kinds:
        entities = [e for e in entities if e.kind in set(kinds)]

    ids = _as_strings(where.get('ids', where.get('id')), 'where.ids')
    if ids:
        wanted = set(ids)
        entities = [e for e in entities if e.id in wanted]

    prefix = str(where.get('id_prefix', '')).strip()
    if prefix:
        entities = [e for e in entities if e.id.startswith(prefix)]

    rows = _as_strings(where.get('rows', where.get('row')), 'where.rows')
    if rows:
        wanted = set(rows)
        entities = [
            e for e in entities
            if e.row_id in wanted or (e.kind in {'row', 'backpack_row'} and e.id in wanted)
        ]

    parents = _as_strings(where.get('parents', where.get('parent')), 'where.parents')
    if parents:
        wanted = set(parents)
        entities = [e for e in entities if e.parent_id in wanted]

    groups = _as_strings(where.get('groups', where.get('group')), 'where.groups')
    if groups:
        wanted: set[str] = set()
        for group_id in groups:
            group = idx.one(group_id, 'group')
            if not group:
                raise ValueError(f'where.group not found: {group_id}')
            for field in ('elements', 'rowElements'):
                raw = group.value.get(field)
                if isinstance(raw, list):
                    wanted.update(str(x) for x in raw if isinstance(x, str))
        entities = [
            e for e in entities
            if e.id in wanted or any(g in groups for g in (e.value.get('groups') if isinstance(e.value.get('groups'), list) else []))
        ]

    title_contains = str(where.get('title_contains', '')).strip().lower()
    if title_contains:
        entities = [e for e in entities if title_contains in e.title.lower()]

    text_contains = str(where.get('text_contains', '')).strip().lower()
    if text_contains:
        def text_of(e: Entity) -> str:
            v = e.value
            return str(v.get('text') or v.get('titleText') or v.get('replaceText') or '').lower()
        entities = [e for e in entities if text_contains in text_of(e)]

    path_prefix = str(where.get('path_prefix', '')).strip()
    if path_prefix:
        entities = [e for e in entities if e.path.startswith(path_prefix)]

    if 'backpack' in where:
        want = bool(where['backpack'])
        entities = [e for e in entities if e.path.startswith('/backpack/') == want]

    entities.sort(key=lambda e: e.path)
    return entities


def check_expected_count(count: int, expect: Any, *, label: str = 'selection') -> None:
    if expect is None:
        return
    if isinstance(expect, int) and not isinstance(expect, bool):
        if count != expect:
            raise ValueError(f'{label} expected {expect} matches, got {count}')
        return
    if not isinstance(expect, dict):
        raise ValueError('expect must be an integer or an object with min/max')
    unknown = set(expect) - {'min', 'max'}
    if unknown:
        raise ValueError(f'unknown expect key(s): {", ".join(sorted(unknown))}')
    minimum = expect.get('min')
    maximum = expect.get('max')
    if minimum is not None:
        if not isinstance(minimum, int) or isinstance(minimum, bool) or minimum < 0:
            raise ValueError('expect.min must be a non-negative integer')
        if count < minimum:
            raise ValueError(f'{label} expected at least {minimum} matches, got {count}')
    if maximum is not None:
        if not isinstance(maximum, int) or isinstance(maximum, bool) or maximum < 0:
            raise ValueError('expect.max must be a non-negative integer')
        if count > maximum:
            raise ValueError(f'{label} expected at most {maximum} matches, got {count}')


def resolve_bulk_refs(
    project: dict[str, Any],
    *,
    explicit: Iterable[str] | None = None,
    where: dict[str, Any] | None = None,
    expect: Any = None,
    allow_empty: bool = False,
    allowed_kinds: set[str] | None = None,
    label: str = 'targets',
) -> list[str]:
    refs: list[str] = []
    for ref in explicit or []:
        text = str(ref).strip()
        if text and text not in refs:
            refs.append(text)
    if where is not None:
        for ent in select_entities(project, where):
            if ent.id not in refs:
                refs.append(ent.id)

    idx = ProjectIndex(project)
    resolved: list[str] = []
    for ref in refs:
        matches = idx.find(ref)
        if len(matches) != 1:
            if not matches:
                raise ValueError(f'{label} entity not found: {ref}')
            raise ValueError(f'{label} entity is ambiguous: {ref}')
        ent = matches[0]
        if allowed_kinds is not None and ent.kind not in allowed_kinds:
            raise ValueError(f'{label} entity {ref!r} has kind {ent.kind!r}; expected one of {sorted(allowed_kinds)}')
        resolved.append(ref)

    check_expected_count(len(resolved), expect, label=label)
    if not resolved and not allow_empty:
        raise ValueError(f'{label} matched no entities')
    return resolved
