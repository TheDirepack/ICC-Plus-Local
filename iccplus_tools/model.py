from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

Json = dict[str, Any]


def esc(value: str) -> str:
    return value.replace('~', '~0').replace('/', '~1')


@dataclass(slots=True)
class Entity:
    kind: str
    id: str
    value: Json
    path: str
    parent_id: str | None = None
    row_id: str | None = None
    choice_id: str | None = None

    @property
    def title(self) -> str:
        return str(self.value.get('debugTitle') or self.value.get('title') or self.value.get('name') or self.id)


class ProjectIndex:
    """Index the parts of an ICC Plus project that have identity or runtime meaning."""

    TOP = {
        'pointTypes': 'point',
        'variables': 'variable',
        'words': 'word',
        'groups': 'group',
        'rowDesignGroups': 'row_design_group',
        'objectDesignGroups': 'choice_design_group',
        'globalRequirements': 'global_requirement',
        'soundEffects': 'sound_effect',
        'categories': 'category',
    }

    def __init__(self, project: Json):
        self.project = project
        self.entities: list[Entity] = []
        self.by_id: dict[str, list[Entity]] = {}
        self.by_kind: dict[str, list[Entity]] = {}
        self.by_path: dict[str, Entity] = {}
        self._collect_rows('rows', 'row')
        self._collect_rows('backpack', 'backpack_row')
        for key, kind in self.TOP.items():
            for i, value in enumerate(self._objects(project.get(key))):
                path = f'/{esc(key)}/{i}'
                if kind == 'category':
                    ident = f"{value.get('type', '')}:{value.get('idx', i)}"
                else:
                    ident = str(value.get('id') or f'@{path}')
                ent = self._add(Entity(kind, ident, value, path))
                if kind in {'global_requirement', 'sound_effect'}:
                    self._collect_requirements(value.get('requireds'), f'{path}/requireds', ent.id, None, None)

    @staticmethod
    def _objects(value: Any) -> list[Json]:
        return [x for x in value if isinstance(x, dict)] if isinstance(value, list) else []

    def _add(self, entity: Entity) -> Entity:
        self.entities.append(entity)
        self.by_id.setdefault(entity.id, []).append(entity)
        self.by_kind.setdefault(entity.kind, []).append(entity)
        self.by_path[entity.path] = entity
        return entity

    def _collect_requirements(
        self,
        value: Any,
        base: str,
        parent_id: str,
        row_id: str | None,
        choice_id: str | None,
    ) -> None:
        for i, req in enumerate(self._objects(value)):
            path = f'{base}/{i}'
            ident = str(req.get('id') or f'@{path}')
            ent = self._add(Entity('requirement', ident, req, path, parent_id, row_id, choice_id))
            self._collect_requirements(req.get('requireds'), f'{path}/requireds', ent.id, row_id, choice_id)
            self._collect_requirements(req.get('orRequireds'), f'{path}/orRequireds', ent.id, row_id, choice_id)

    def _collect_scores(self, value: Any, base: str, parent_id: str, row_id: str, choice_id: str) -> None:
        for i, score in enumerate(self._objects(value)):
            path = f'{base}/{i}'
            ident = str(score.get('idx') or f'@{path}')
            ent = self._add(Entity('score', ident, score, path, parent_id, row_id, choice_id))
            self._collect_requirements(score.get('requireds'), f'{path}/requireds', ent.id, row_id, choice_id)

    def _collect_rows(self, key: str, kind: str) -> None:
        for ri, row in enumerate(self._objects(self.project.get(key))):
            rpath = f'/{key}/{ri}'
            rid = str(row.get('id') or f'@{rpath}')
            rent = self._add(Entity(kind, rid, row, rpath, row_id=rid))
            self._collect_requirements(row.get('requireds'), f'{rpath}/requireds', rent.id, rid, None)
            for ci, choice in enumerate(self._objects(row.get('objects'))):
                cpath = f'{rpath}/objects/{ci}'
                cid = str(choice.get('id') or f'@{cpath}')
                cent = self._add(Entity('choice', cid, choice, cpath, rid, rid, cid))
                self._collect_requirements(choice.get('requireds'), f'{cpath}/requireds', cid, rid, cid)
                self._collect_scores(choice.get('scores'), f'{cpath}/scores', cid, rid, cid)
                for ai, addon in enumerate(self._objects(choice.get('addons'))):
                    apath = f'{cpath}/addons/{ai}'
                    selectable = addon.get('isSelectable') is True
                    aid = str(addon.get('id') or f'@{apath}')
                    akind = 'selectable_addon' if selectable else 'addon'
                    aent = self._add(Entity(akind, aid, addon, apath, cid, rid, cid))
                    self._collect_requirements(addon.get('requireds'), f'{apath}/requireds', aent.id, rid, cid)
                    if selectable:
                        self._collect_scores(addon.get('scores'), f'{apath}/scores', aid, rid, cid)

    def find(self, ident: str, kind: str | None = None) -> list[Entity]:
        if ident.startswith('/'):
            ent = self.by_path.get(ident)
            return [ent] if ent and (kind is None or ent.kind == kind) else []
        values = self.by_id.get(ident, [])
        return [x for x in values if kind is None or x.kind == kind]

    def one(self, ident: str, kind: str | None = None) -> Entity | None:
        found = self.find(ident, kind)
        return found[0] if len(found) == 1 else None

    def selectables(self, include_backpack: bool = True) -> list[Entity]:
        values = list(self.by_kind.get('choice', [])) + list(self.by_kind.get('selectable_addon', []))
        if include_backpack:
            return values
        backpack_rows = {x.id for x in self.by_kind.get('backpack_row', [])}
        return [x for x in values if x.row_id not in backpack_rows]

    def row(self, entity: Entity) -> Entity | None:
        return self.one(entity.row_id or '', 'row') or self.one(entity.row_id or '', 'backpack_row')

    def parent_choice(self, entity: Entity) -> Entity | None:
        if entity.kind not in {'addon', 'selectable_addon'} or not entity.parent_id:
            return None
        return self.one(entity.parent_id, 'choice')

    def group_members(self, group_id: str) -> list[str]:
        group = self.one(group_id, 'group')
        if not group:
            return []
        return [str(x) for x in group.value.get('elements', []) if isinstance(x, str)]

    def summary(self) -> dict[str, Any]:
        count = lambda k: len(self.by_kind.get(k, []))
        return {
            'version': self.project.get('version'),
            'rows': count('row'),
            'backpack_rows': count('backpack_row'),
            'choices': count('choice'),
            'selectable_addons': count('selectable_addon'),
            'scores': count('score'),
            'requirements': count('requirement'),
            'points': count('point'),
            'variables': count('variable'),
            'words': count('word'),
            'groups': count('group'),
            'global_requirements': count('global_requirement'),
        }

    def ids(self, kinds: Iterable[str] | None = None) -> set[str]:
        if kinds is None:
            entities = self.entities
        else:
            wanted = set(kinds)
            entities = [x for x in self.entities if x.kind in wanted]
        return {x.id for x in entities if not x.id.startswith('@')}
