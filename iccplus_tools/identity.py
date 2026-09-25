from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .model import ProjectIndex

PREFIXES = {
    'row': 'row',
    'backpack_row': 'row',
    'choice': 'choice',
    'addon': 'addon',
    'selectable_addon': 'addon',
    'score': 'score',
    'requirement': 'req',
    'point': 'point',
    'variable': 'var',
    'word': 'word',
    'group': 'group',
    'global_requirement': 'greq',
    'row_design_group': 'rowdesign',
    'choice_design_group': 'choicedesign',
    'sound_effect': 'sfx',
}

IDENTITY_KINDS = frozenset(PREFIXES)


def slugify(value: Any, fallback: str = 'item') -> str:
    text = str(value or '').strip().lower()
    text = re.sub(r'[^a-z0-9]+', '_', text).strip('_')
    return text or fallback


@dataclass
class IdentityAllocator:
    """Project-wide deterministic identity allocator.

    Explicit IDs are never changed. Auto IDs avoid both already-used IDs and
    explicit IDs reserved elsewhere in the same generation input.
    """

    used: set[str] = field(default_factory=set)
    reserved: set[str] = field(default_factory=set)

    @classmethod
    def from_project(cls, project: dict[str, Any]) -> 'IdentityAllocator':
        return cls(used=set(ProjectIndex(project).ids()))

    def reserve(self, ident: str) -> None:
        if ident in self.reserved:
            raise ValueError(f'duplicate explicit ID in generation input: {ident}')
        self.reserved.add(ident)

    def claim(self, ident: str) -> str:
        ident = str(ident).strip()
        if not ident:
            raise ValueError('explicit ID cannot be empty')
        if ident in self.used:
            raise ValueError(f'ID already exists: {ident}')
        self.used.add(ident)
        return ident

    def allocate(self, kind: str, hint: Any = None, *, parent: str | None = None) -> str:
        prefix = PREFIXES.get(kind, slugify(kind, 'item'))
        pieces = [prefix]
        if parent:
            p = slugify(parent)
            if p and p != prefix:
                pieces.append(p)
        h = slugify(hint, 'item')
        if h and h not in pieces:
            pieces.append(h)
        base = '_'.join(pieces)
        candidate = base
        n = 2
        blocked = self.used | self.reserved
        while candidate in blocked:
            candidate = f'{base}_{n}'
            n += 1
        self.used.add(candidate)
        return candidate


def entity_hint(kind: str, values: dict[str, Any], parent: str | None = None) -> str:
    if kind == 'score':
        return str(values.get('id') or 'score')
    if kind == 'requirement':
        target = values.get('reqId') or values.get('reqId1') or values.get('type') or 'condition'
        state = 'yes' if values.get('required', True) else 'no'
        return f'{state}_{target}'
    return str(values.get('debugTitle') or values.get('title') or values.get('name') or parent or 'item')
