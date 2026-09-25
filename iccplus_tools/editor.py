from __future__ import annotations

import copy
import json
from typing import Any

from .model import ProjectIndex
from .identity import IdentityAllocator, entity_hint
from .field_types import validate_known_values
from .upstream_2106 import default_project


def new_project() -> dict[str, Any]:
    """Return an exact deep copy of ICC Plus 2.10.7 ``defaultApp``."""
    return default_project()



def make_entity(project: dict[str, Any], kind: str, values: dict[str, Any] | None = None, *, allocator: IdentityAllocator | None = None, parent: str | None = None) -> dict[str, Any]:
    values = copy.deepcopy(values or {})
    validate_known_values(kind, values, recursive=True)
    allocator = allocator or IdentityAllocator.from_project(project)

    identity_key = 'idx' if kind == 'score' else 'id'
    # Categories use the Creator's composite (type, idx) identity and have no
    # string ID. They are handled separately below.
    if kind == 'category':
        ident = ''
    else:
        # ICC Plus does not give ordinary Requirements or non-selectable Addons
        # project identities. Their creator defaults use id: "".
        structural_identity = kind in {'requirement', 'addon'}
        explicit = values.get(identity_key)
        if structural_identity:
            ident = str(explicit) if explicit is not None else ''
        elif explicit is not None and str(explicit).strip():
            ident = allocator.claim(str(explicit))
        else:
            values.pop(identity_key, None)
            ident = allocator.allocate(kind, entity_hint(kind, values, parent), parent=parent)
    if kind == 'row':
        base = {'index': len(project.setdefault('rows', [])), 'id': ident, 'title': project.get('defaultRowTitle', 'Row'), 'titleText': project.get('defaultRowText', ''), 'debugTitle': '', 'objectWidth': project.get('defaultRowWidth', 'col-md-3'), 'image': '', 'template': project.get('defaultRowTemplate', 1), 'isButtonRow': False, 'isResultRow': False, 'resultGroupId': '', 'isInfoRow': False, 'defaultAspectWidth': 1, 'defaultAspectHeight': 1, 'allowedChoices': project.get('defaultRowAllowedChoices', 0), 'currentChoices': 0, 'rowJustify': project.get('defaultRowJustify', 'start'), 'requireds': [], 'isEditModeOn': False, 'isRequirementOpen': False, 'objects': [], 'rowDesignGroups': []}
    elif kind == 'backpack_row':
        # AppBackpack.svelte createNewRow(-1) uses fixed build/result-row
        # defaults rather than the normal-row defaults configured on the app.
        base = {'index': len(project.setdefault('backpack', [])), 'id': ident, 'isBackpack': True, 'title': project.get('defaultRowTitle', 'Row'), 'titleText': project.get('defaultRowText', ''), 'debugTitle': '', 'objectWidth': 'col-md-3', 'image': '', 'template': 1, 'isButtonRow': False, 'buttonType': True, 'buttonId': '', 'buttonText': 'Click', 'buttonRandom': False, 'buttonRandomNumber': 1, 'isResultRow': True, 'resultGroupId': '', 'isInfoRow': True, 'defaultAspectWidth': 1, 'defaultAspectHeight': 1, 'allowedChoices': 0, 'currentChoices': 0, 'requireds': [], 'isEditModeOn': False, 'isRequirementOpen': False, 'objects': [], 'rowDesignGroups': []}
    elif kind == 'choice':
        base = {'index': 0, 'id': ident, 'title': project.get('defaultChoiceTitle', 'Choice'), 'text': project.get('defaultChoiceText', ''), 'debugTitle': '', 'image': '', 'template': project.get('defaultChoiceTemplate', 1), 'objectWidth': project.get('defaultChoiceWidth', ''), 'isActive': False, 'multipleUseVariable': 0, 'initMultipleTimesMinus': 0, 'selectedThisManyTimesProp': 0, 'requireds': [], 'addons': [], 'scores': [], 'groups': [], 'objectDesignGroups': []}
    elif kind in {'addon', 'selectable_addon'}:
        base = {'id': ident, 'title': project.get('defaultAddonTitle', 'Addon'), 'text': project.get('defaultAddonText', ''), 'template': project.get('defaultAddonTemplate', 1), 'addonWidth': project.get('defaultAddonWidth', 'col-12'), 'image': '', 'requireds': [], **({'parentId': parent} if parent is not None else {}), **({'showAddon': True} if project.get('defaultUseShowAddon') else {}), **({'hideAddon': True} if project.get('defaultUseHideAddon') else {})}
        if kind == 'selectable_addon':
            # ObjectAddon.svelte first creates a normal Addon. Toggling
            # "This addon is selectable" then adds only these fields. Other
            # selectable-only fields are created lazily by their own controls.
            base.update({'id': ident, 'isSelectable': True, 'scores': []})
    elif kind == 'score':
        base = {'idx': ident, 'id': '', 'value': 0, 'type': '', 'requireds': [], 'beforeText': project.get('defaultBeforePoint', 'Cost:'), 'afterText': project.get('defaultAfterPoint', 'points'), 'showScore': project.get('defaultUseShowScore', True)}
    elif kind == 'requirement':
        req_type = values.get('type', 'id')
        base = {'required': True, 'requireds': [], 'orRequired': ([{'req': ''}] if req_type == 'word' else []), 'orRequireds': [], 'id': ident, 'type': 'id', 'reqId': '', 'reqId1': '', 'reqId2': '', 'reqId3': '', 'reqPoints': 0, 'showRequired': project.get('defaultUseShowReq', False), 'operator': '1', 'afterText': project.get('defaultAfterReq', 'choice'), 'beforeText': project.get('defaultBeforeReq', 'Required:'), 'orNum': 1, 'selNum': 1, 'selFromOperators': '1', 'more': []}
    elif kind == 'point':
        n = len(project.setdefault('pointTypes', [])) + 1
        base = {'id': ident, 'name': f'Point {n}', 'startingSum': 0, 'initValue': 0, 'activatedId': '', 'beforeText': f'Point {n}:', 'afterText': '', 'category': -1}
    elif kind == 'variable':
        base = {'id': ident, 'isTrue': False, 'category': -1}
    elif kind == 'word':
        base = {'id': ident, 'replaceText': '', 'category': -1}
    elif kind == 'group':
        n = len(project.setdefault('groups', [])) + 1
        base = {'id': ident, 'name': f'Group {n}', 'category': -1, 'elements': [], 'rowElements': []}
    elif kind == 'global_requirement':
        n = len(project.setdefault('globalRequirements', [])) + 1
        base = {'id': ident, 'name': f'Requirement {n}', 'category': -1, 'requireds': []}
    elif kind == 'row_design_group':
        base = {'id': ident, 'name': f'Design Group {len(project.setdefault("rowDesignGroups", [])) + 1}', 'activatedId': '', 'elements': [], 'backpackElements': [], 'groupElements': [], 'styling': {}, 'category': -1}
    elif kind == 'choice_design_group':
        base = {'id': ident, 'name': f'Design Group {len(project.setdefault("objectDesignGroups", [])) + 1}', 'activatedId': '', 'elements': [], 'backpackElements': [], 'groupElements': [], 'styling': {}, 'category': -1}
    elif kind == 'sound_effect':
        base = {'id': ident, 'name': 'Sound effect', 'audio': '', 'volume': 1, 'pitch': 0, 'isDefault': False, 'onSelected': False, 'onDeselected': False, 'requireds': [], 'groups': []}
    elif kind == 'category':
        allowed_types = {'point', 'variable', 'group', 'word', 'rDesign', 'cDesign', 'globalReq'}
        typ = values.get('type')
        if not isinstance(typ, str) or typ not in allowed_types:
            raise ValueError('category requires type: point, variable, group, word, rDesign, cDesign, or globalReq')
        used = {
            int(cat.get('idx'))
            for cat in project.get('categories', [])
            if isinstance(cat, dict) and cat.get('type') == typ and isinstance(cat.get('idx'), int) and not isinstance(cat.get('idx'), bool)
        }
        explicit_idx = values.get('idx')
        if explicit_idx is None:
            idx = next((n for n in range(99) if n not in used), None)
            if idx is None:
                raise ValueError(f'category type {typ!r} has no free Creator slot (0-98)')
        else:
            if not isinstance(explicit_idx, int) or isinstance(explicit_idx, bool) or not 0 <= explicit_idx < 99:
                raise ValueError('category idx must be a Creator slot from 0 through 98')
            idx = explicit_idx
            if idx in used:
                raise ValueError(f'category identity already exists: {typ}:{idx}')
        base = {'idx': idx, 'name': f'Slot {idx + 1}', 'type': typ}
    else:
        raise ValueError(f'unsupported factory kind: {kind}')
    return _deep_merge(base, values)


def _reset_score_runtime(score: dict[str, Any]) -> None:
    for key in (
        'isActive', 'isActiveMul', 'isActiveMulMinus', 'setValue',
        'discountScore', 'discountScoreCal', 'tmpDisScore', 'tmpDiscount',
        'discountedFrom', 'dupTextA', 'dupTextB', 'discountTextA',
        'discountTextB', 'appliedDiscount',
    ):
        score.pop(key, None)
    discounts = score.get('discounts')
    if isinstance(discounts, list):
        for discount in discounts:
            if isinstance(discount, dict):
                for key in ('state', 'stack', 'count'):
                    # These are Creator/runtime bookkeeping values. Keep the
                    # declared discount settings but reset transient counters.
                    if key in discount and key in {'state', 'stack'}:
                        discount[key] = 0


def _reset_choice_runtime(choice: dict[str, Any]) -> None:
    choice['isActive'] = False
    for key in ('forcedActivated', 'appliedDisChoices', 'activatedFrom', 'activatedRandom', 'activatedRandomMul', 'tempMultipleValue'):
        choice.pop(key, None)
    for score in choice.get('scores', []) if isinstance(choice.get('scores'), list) else []:
        if isinstance(score, dict):
            _reset_score_runtime(score)
    for addon in choice.get('addons', []) if isinstance(choice.get('addons'), list) else []:
        if isinstance(addon, dict) and addon.get('isSelectable') is True:
            addon['isActive'] = False
            for key in ('forcedActivated', 'appliedDisChoices', 'activatedFrom', 'activatedRandom', 'activatedRandomMul', 'tempMultipleValue'):
                addon.pop(key, None)
            for score in addon.get('scores', []) if isinstance(addon.get('scores'), list) else []:
                if isinstance(score, dict):
                    _reset_score_runtime(score)


def _identity_nodes(value: dict[str, Any], kind: str) -> list[tuple[str, dict[str, Any]]]:
    out: list[tuple[str, dict[str, Any]]] = []
    if kind in {'row', 'backpack_row'}:
        out.append((kind, value))
        for choice in value.get('objects', []) if isinstance(value.get('objects'), list) else []:
            if isinstance(choice, dict):
                out.extend(_identity_nodes(choice, 'choice'))
    elif kind == 'choice':
        out.append(('choice', value))
        for score in value.get('scores', []) if isinstance(value.get('scores'), list) else []:
            if isinstance(score, dict):
                out.append(('score', score))
        for addon in value.get('addons', []) if isinstance(value.get('addons'), list) else []:
            if isinstance(addon, dict) and addon.get('isSelectable') is True:
                out.extend(_identity_nodes(addon, 'selectable_addon'))
    elif kind == 'selectable_addon':
        out.append(('selectable_addon', value))
        for score in value.get('scores', []) if isinstance(value.get('scores'), list) else []:
            if isinstance(score, dict):
                out.append(('score', score))
    elif kind in {'score', 'point', 'variable', 'word', 'group', 'global_requirement', 'row_design_group', 'choice_design_group', 'sound_effect'}:
        out.append((kind, value))
    return out


def _remap_cloned_identities(project: dict[str, Any], value: dict[str, Any], kind: str, *, keep_unique: bool = False) -> dict[str, str]:
    allocator = IdentityAllocator.from_project(project)
    existing = ProjectIndex(project)
    mapping: dict[str, str] = {}
    nodes = _identity_nodes(value, kind)
    for node_kind, node in nodes:
        key = 'idx' if node_kind == 'score' else 'id'
        old = str(node.get(key, ''))
        if not old:
            parent = str(node.get('parentId', '')) or None
            node[key] = allocator.allocate(node_kind, entity_hint(node_kind, node, parent), parent=parent)
            continue
        can_keep = keep_unique and not existing.find(old) and old not in mapping.values()
        if can_keep:
            allocator.reserve(old)
            continue
        parent = str(node.get('parentId', '')) or None
        new = allocator.allocate(node_kind, entity_hint(node_kind, node, parent), parent=parent)
        node[key] = new
        mapping[old] = new
    for old, new in mapping.items():
        rewrite_references(value, old, new)
    # parentId is structural and should always point at the cloned parent.
    if kind in {'row', 'backpack_row'}:
        for choice in value.get('objects', []) if isinstance(value.get('objects'), list) else []:
            if not isinstance(choice, dict):
                continue
            for addon in choice.get('addons', []) if isinstance(choice.get('addons'), list) else []:
                if isinstance(addon, dict):
                    addon['parentId'] = str(choice.get('id', ''))
    elif kind == 'choice':
        for addon in value.get('addons', []) if isinstance(value.get('addons'), list) else []:
            if isinstance(addon, dict):
                addon['parentId'] = str(value.get('id', ''))
    return mapping


def _deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(base)
    for k, v in patch.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict): out[k] = _deep_merge(out[k], v)
        else: out[k] = copy.deepcopy(v)
    return out


def _decode(token: str) -> str:
    return token.replace('~1', '/').replace('~0', '~')


def pointer_get(doc: Any, pointer: str) -> Any:
    if pointer == '': return doc
    if not pointer.startswith('/'): raise ValueError('JSON Pointer must start with /')
    cur = doc
    for raw in pointer[1:].split('/'):
        token = _decode(raw)
        if isinstance(cur, list): cur = cur[int(token)]
        elif isinstance(cur, dict): cur = cur[token]
        else: raise KeyError(pointer)
    return cur


def _parent(doc: Any, pointer: str) -> tuple[Any, str]:
    if not pointer.startswith('/') or pointer == '/':
        raise ValueError('pointer must address a child')
    parts = pointer[1:].split('/')
    parent = doc
    for raw in parts[:-1]:
        token = _decode(raw)
        parent = parent[int(token)] if isinstance(parent, list) else parent[token]
    return parent, _decode(parts[-1])


def pointer_set(doc: Any, pointer: str, value: Any, *, insert: bool = False) -> None:
    parent, token = _parent(doc, pointer)
    if isinstance(parent, list):
        if token == '-': parent.append(value)
        elif insert: parent.insert(int(token), value)
        else: parent[int(token)] = value
    else: parent[token] = value


def pointer_remove(doc: Any, pointer: str) -> Any:
    parent, token = _parent(doc, pointer)
    return parent.pop(int(token)) if isinstance(parent, list) else parent.pop(token)


ARRAY_REFS = {'groups','rowDesignGroups','objectDesignGroups','elements','rowElements','backpackElements','groupElements','designGroups','selGroups','selRows','discountRows','discountChoices','discountGroups','discountPointTypes','hiddenContentsRow','idOfAllowChoice','pointTypeToMultiply','pointTypeToDivide','pointTypeToSet','changedVariables','linkedObjects','appliedDisChoices','activatedRandom'}
SCALAR_REFS = {'parentId','reqId','reqId1','reqId2','reqId3','activatedId','resultGroupId','buttonId','pointTypeRandom','multipleScoreId','duplicateRowId','duplicateRowPlace','scrollObjectId','scrollRowId','idOfTheTextfieldWord','sfxIdOnSelect','sfxIdOnDeselect'}
COMMA_REFS = {'activateThisChoice','deactivateThisChoice','changeTemplatesList','changeWidthList'}


def _replace_token(value: str, old: str, new: str) -> str:
    if value == old: return new
    if value.startswith(old + '/ON#'): return new + value[len(old):]
    return value


def rewrite_references(value: Any, old: str, new: str, parent_key: str = '') -> None:
    if isinstance(value, list):
        if parent_key in ARRAY_REFS:
            for i, item in enumerate(value):
                if isinstance(item, str): value[i] = _replace_token(item, old, new)
        else:
            for item in value: rewrite_references(item, old, new, parent_key)
    elif isinstance(value, dict):
        for key, child in list(value.items()):
            if isinstance(child, str) and key in SCALAR_REFS: value[key] = _replace_token(child, old, new)
            elif isinstance(child, str) and key in COMMA_REFS: value[key] = ','.join(_replace_token(x.strip(), old, new) for x in child.split(','))
            elif isinstance(child, str) and key in {'expValue','expMinValue','expMaxValue','setWithThis'}: value[key] = child.replace('{' + old + '}', '{' + new + '}')
            else: rewrite_references(child, old, new, key)


class ProjectEditor:
    def __init__(self, project: dict[str, Any]):
        self.project = project

    def normalize(self) -> list[str]:
        changes: list[str] = []
        allocator = IdentityAllocator.from_project(self.project)
        # Fill missing identity fields. Existing explicit duplicates are left for validation to reject.
        idx0 = ProjectIndex(self.project)
        for ent in sorted(idx0.entities, key=lambda e: e.path):
            if ent.kind == 'category':
                continue
            key_name = 'idx' if ent.kind == 'score' else 'id'
            if ent.kind in {'row','backpack_row','choice','selectable_addon','score','point','variable','word','group','row_design_group','choice_design_group','global_requirement','sound_effect'} and not str(ent.value.get(key_name, '')).strip():
                parent = ent.parent_id or ent.row_id
                ent.value[key_name] = allocator.allocate(ent.kind, entity_hint(ent.kind, ent.value, parent), parent=parent)
                changes.append(ent.path + '/' + key_name)
        # Categories use the upstream (type, idx) composite identity. Fill missing idx values per type.
        categories = self.project.get('categories', [])
        if isinstance(categories, list):
            used_cat: dict[str, set[int]] = {}
            for cat in categories:
                if isinstance(cat, dict) and isinstance(cat.get('idx'), int):
                    used_cat.setdefault(str(cat.get('type','')), set()).add(int(cat['idx']))
            for ci, cat in enumerate(categories):
                if not isinstance(cat, dict) or isinstance(cat.get('idx'), int):
                    continue
                typ = str(cat.get('type',''))
                n = 0
                while n in used_cat.setdefault(typ, set()):
                    n += 1
                cat['idx'] = n
                used_cat[typ].add(n)
                changes.append(f'/categories/{ci}/idx')
        for key in ('rows', 'backpack'):
            rows = self.project.get(key, [])
            if not isinstance(rows, list): continue
            for ri, row in enumerate(rows):
                if not isinstance(row, dict): continue
                if row.get('index') != ri: row['index'] = ri; changes.append(f'/{key}/{ri}/index')
                rid = str(row.get('id', ''))
                choices = row.get('objects', [])
                if not isinstance(choices, list): continue
                for ci, choice in enumerate(choices):
                    if not isinstance(choice, dict): continue
                    if choice.get('index') != ci: choice['index'] = ci; changes.append(f'/{key}/{ri}/objects/{ci}/index')
                    cid = str(choice.get('id', ''))
                    addons = choice.get('addons', [])
                    if not isinstance(addons, list): continue
                    for ai, addon in enumerate(addons):
                        if isinstance(addon, dict) and addon.get('isSelectable') is True and addon.get('parentId') != cid:
                            addon['parentId'] = cid; changes.append(f'/{key}/{ri}/objects/{ci}/addons/{ai}/parentId')
        # Set-like membership fields should never contain duplicate IDs.
        idx = ProjectIndex(self.project)
        for ent in idx.entities:
            for field in ('groups', 'rowDesignGroups', 'objectDesignGroups', 'designGroups'):
                value = ent.value.get(field)
                if not isinstance(value, list):
                    continue
                unique = list(dict.fromkeys(x for x in value if isinstance(x, str) and x))
                if value != unique:
                    ent.value[field] = unique
                    changes.append(ent.path + '/' + field)

        # ICC Plus stores Group and design-group membership on both the member
        # and the Group object. The member-side list is canonical locally.
        idx = ProjectIndex(self.project)
        selectables = idx.selectables()
        rows = idx.by_kind.get('row', [])
        backpack_rows = idx.by_kind.get('backpack_row', [])
        choices = idx.by_kind.get('choice', [])
        normal_groups = idx.by_kind.get('group', [])

        for group in normal_groups:
            selectable_members = [e.id for e in selectables if group.id in (e.value.get('groups', []) if isinstance(e.value.get('groups'), list) else [])]
            row_members = [e.id for e in rows + backpack_rows if group.id in (e.value.get('groups', []) if isinstance(e.value.get('groups'), list) else [])]
            for field, members in (('elements', selectable_members), ('rowElements', row_members)):
                old_members = list(group.value.get(field, [])) if isinstance(group.value.get(field), list) else []
                if old_members != members:
                    group.value[field] = members
                    changes.append(group.path + '/' + field)

        for design_kind, side_field in (('row_design_group', 'rowDesignGroups'), ('choice_design_group', 'objectDesignGroups')):
            for design in idx.by_kind.get(design_kind, []):
                if design_kind == 'row_design_group':
                    regular_members = [e.id for e in rows if design.id in (e.value.get(side_field, []) if isinstance(e.value.get(side_field), list) else [])]
                    backpack_members = [e.id for e in backpack_rows if design.id in (e.value.get(side_field, []) if isinstance(e.value.get(side_field), list) else [])]
                else:
                    regular_members = [e.id for e in choices if not e.path.startswith('/backpack/') and design.id in (e.value.get(side_field, []) if isinstance(e.value.get(side_field), list) else [])]
                    backpack_members = [e.id for e in choices if e.path.startswith('/backpack/') and design.id in (e.value.get(side_field, []) if isinstance(e.value.get(side_field), list) else [])]
                group_members = [g.id for g in normal_groups if design.id in (g.value.get('designGroups', []) if isinstance(g.value.get('designGroups'), list) else [])]
                for field, members in (('elements', regular_members), ('backpackElements', backpack_members), ('groupElements', group_members)):
                    old_members = list(design.value.get(field, [])) if isinstance(design.value.get(field), list) else []
                    if old_members != members:
                        design.value[field] = members
                        changes.append(design.path + '/' + field)
        return changes

    def assert_unique_identities(self) -> None:
        """Enforce the local authoring invariant that every identity is unique.

        `normalize()` fills missing identity fields. This check runs after
        normalization and rejects ambiguous explicit identities instead of
        guessing which duplicate references should point at.
        """
        idx = ProjectIndex(self.project)
        identity_kinds = {
            'row', 'backpack_row', 'choice', 'selectable_addon',
            'score', 'point', 'variable', 'word', 'group',
            'row_design_group', 'choice_design_group', 'global_requirement',
            'sound_effect',
        }
        missing: list[str] = []
        duplicates: dict[str, list[str]] = {}
        seen: dict[str, list[str]] = {}
        for ent in idx.entities:
            if ent.kind not in identity_kinds:
                continue
            key = 'idx' if ent.kind == 'score' else 'id'
            raw = ent.value.get(key)
            if raw is None or not str(raw).strip():
                missing.append(ent.path + '/' + key)
                continue
            seen.setdefault(str(raw), []).append(ent.path)
        for ident, paths in seen.items():
            if len(paths) > 1:
                duplicates[ident] = paths

        # Categories use the upstream (type, idx) pair instead of a string ID.
        cat_seen: dict[str, list[str]] = {}
        for ent in idx.by_kind.get('category', []):
            if not isinstance(ent.value.get('idx'), int):
                missing.append(ent.path + '/idx')
                continue
            cat_seen.setdefault(ent.id, []).append(ent.path)
        for ident, paths in cat_seen.items():
            if len(paths) > 1:
                duplicates['category:' + ident] = paths

        if missing:
            raise ValueError('missing identity fields after normalization: ' + ', '.join(missing[:8]))
        if duplicates:
            preview = '; '.join(f'{ident}: {paths}' for ident, paths in list(duplicates.items())[:5])
            raise ValueError('duplicate identities are not allowed: ' + preview)

    def normalize_and_check(self) -> list[str]:
        changes = self.normalize()
        self.assert_unique_identities()
        return changes

    def resolve(self, reference: str, kind: str | None = None):
        idx = ProjectIndex(self.project)
        matches = idx.find(reference, kind)
        if not matches:
            raise ValueError(f'entity not found: {reference}')
        if len(matches) != 1:
            raise ValueError(f'entity reference is ambiguous ({len(matches)} matches): {reference}')
        return matches[0]

    def add(self, kind: str, *, parent: str | None = None, values: dict[str, Any] | None = None, normalize: bool = True) -> dict[str, Any]:
        allocator = IdentityAllocator.from_project(self.project)
        value = make_entity(self.project, kind, values, allocator=allocator, parent=parent)
        if kind == 'row': self.project.setdefault('rows', []).append(value)
        elif kind == 'backpack_row': value['isBackpack'] = True; self.project.setdefault('backpack', []).append(value)
        elif kind in {'point','variable','word','group','global_requirement','row_design_group','choice_design_group','sound_effect','category'}:
            key = {'point':'pointTypes','variable':'variables','word':'words','group':'groups','global_requirement':'globalRequirements','row_design_group':'rowDesignGroups','choice_design_group':'objectDesignGroups','sound_effect':'soundEffects','category':'categories'}[kind]
            self.project.setdefault(key, []).append(value)
        else:
            if not parent: raise ValueError(f'{kind} requires --parent')
            p = self.resolve(parent)
            if kind == 'choice' and p.kind in {'row','backpack_row'}:
                value['index'] = len(p.value.setdefault('objects', [])); p.value['objects'].append(value)
            elif kind in {'addon','selectable_addon'} and p.kind == 'choice':
                value['parentId'] = p.id; p.value.setdefault('addons', []).append(value)
            elif kind == 'score' and p.kind in {'choice','selectable_addon'}:
                p.value.setdefault('scores', []).append(value)
            elif kind == 'requirement' and p.kind in {'row','backpack_row','choice','selectable_addon','addon','score','global_requirement','sound_effect','requirement'}:
                p.value.setdefault('requireds', []).append(value)
            else: raise ValueError(f'cannot add {kind} under {p.kind}')
        if normalize: self.normalize()
        return value

    def update_project(self, *, values: dict[str, Any] | None = None, unset: list[str] | None = None, normalize: bool = True) -> dict[str, Any]:
        values = values or {}
        if not isinstance(values, dict):
            raise ValueError('values must be an object')
        validate_known_values('project', values, recursive=True, strict_fields=True)
        merged = _deep_merge(self.project, values)
        for field in unset or []:
            if not isinstance(field, str) or not field:
                raise ValueError('project unset fields must be non-empty strings')
            merged.pop(field, None)
        self.project.clear()
        self.project.update(merged)
        if normalize:
            self.normalize()
        return self.project

    def update(self, reference: str, *, kind: str | None = None, values: dict[str, Any] | None = None, unset: list[str] | None = None, normalize: bool = True) -> dict[str, Any]:
        ent = self.resolve(reference, kind)
        values = values or {}
        if not isinstance(values, dict): raise ValueError('values must be an object')
        validate_known_values(ent.kind, values, recursive=True)
        if ent.kind == 'category':
            for key in ('type', 'idx'):
                if key in values and values[key] != ent.value.get(key):
                    raise ValueError('Category type/idx define its Creator slot; delete and add a category to change them')
        else:
            identifier_key = 'idx' if ent.kind == 'score' else 'id'
            if identifier_key in values and str(values[identifier_key]) != str(ent.value.get(identifier_key, '')):
                raise ValueError('change IDs with rename, not update')
        merged = _deep_merge(ent.value, values)
        for field in unset or []:
            merged.pop(field, None)
        ent.value.clear(); ent.value.update(merged)
        if normalize: self.normalize()
        return ent.value

    def upsert(self, kind: str, *, parent: str | None = None, values: dict[str, Any] | None = None, normalize: bool = True) -> tuple[dict[str, Any], bool]:
        values = values or {}
        if kind == 'category':
            typ = values.get('type')
            idx = values.get('idx')
            if isinstance(typ, str) and isinstance(idx, int) and not isinstance(idx, bool):
                matches = ProjectIndex(self.project).find(f'{typ}:{idx}', 'category')
                if len(matches) > 1:
                    raise ValueError(f'entity reference is ambiguous ({len(matches)} matches): {typ}:{idx}')
                if len(matches) == 1:
                    value = self.update(f'{typ}:{idx}', kind='category', values=values, normalize=normalize)
                    return value, False
            return self.add(kind, parent=parent, values=values, normalize=normalize), True
        identifier_key = 'idx' if kind == 'score' else 'id'
        ident = values.get(identifier_key)
        if ident:
            matches = ProjectIndex(self.project).find(str(ident), kind)
            if len(matches) > 1:
                raise ValueError(f'entity reference is ambiguous ({len(matches)} matches): {ident}')
            if len(matches) == 1:
                value = self.update(str(ident), kind=kind, values=values, normalize=normalize)
                return value, False
        return self.add(kind, parent=parent, values=values, normalize=normalize), True

    def delete(self, reference: str, *, kind: str | None = None, normalize: bool = True) -> dict[str, Any]:
        ent = self.resolve(reference, kind)
        # The Creator unassigns objects from a category before deleting its
        # (type, idx) slot. Mirror that behavior rather than leaving stale
        # category numbers behind.
        if ent.kind == 'category':
            typ = ent.value.get('type')
            idx = ent.value.get('idx')
            source_key = {
                'point': 'pointTypes', 'variable': 'variables', 'group': 'groups',
                'word': 'words', 'rDesign': 'rowDesignGroups',
                'cDesign': 'objectDesignGroups', 'globalReq': 'globalRequirements',
            }.get(str(typ))
            if source_key:
                for item in self.project.get(source_key, []) if isinstance(self.project.get(source_key), list) else []:
                    if isinstance(item, dict) and item.get('category') == idx:
                        item['category'] = -1
        removed = pointer_remove(self.project, ent.path)
        if normalize: self.normalize()
        return {'id': ent.id, 'kind': ent.kind, 'path': ent.path, 'value': removed}

    def rename(self, old: str, new: str, *, normalize: bool = True) -> None:
        idx = ProjectIndex(self.project); matches = [x for x in idx.find(old) if x.kind != 'requirement']
        if len(matches) != 1: raise ValueError(f'ID must identify exactly one entity: {old}')
        if idx.find(new): raise ValueError(f'ID already exists: {new}')
        ent = matches[0]; key = 'idx' if ent.kind == 'score' else 'id'; ent.value[key] = new
        rewrite_references(self.project, old, new)
        if ent.kind == 'point':
            for score in ProjectIndex(self.project).by_kind.get('score', []):
                if score.value.get('id') == old: score.value['id'] = new
        if normalize: self.normalize()

    def _child_array(self, kind: str, parent: str | None = None) -> list[dict[str, Any]]:
        if kind == 'row':
            return self.project.setdefault('rows', [])
        if kind == 'backpack_row':
            return self.project.setdefault('backpack', [])
        top_level = {
            'point': 'pointTypes', 'variable': 'variables', 'word': 'words', 'group': 'groups',
            'global_requirement': 'globalRequirements', 'row_design_group': 'rowDesignGroups',
            'choice_design_group': 'objectDesignGroups', 'sound_effect': 'soundEffects', 'category': 'categories',
        }
        if kind in top_level:
            if parent is not None:
                raise ValueError(f'{kind} is a top-level collection and does not accept parent')
            return self.project.setdefault(top_level[kind], [])
        if not parent:
            raise ValueError(f'{kind} requires a parent for structural ordering')
        p = self.resolve(parent)
        if kind == 'choice' and p.kind in {'row', 'backpack_row'}:
            return p.value.setdefault('objects', [])
        if kind in {'addon', 'selectable_addon'} and p.kind == 'choice':
            return p.value.setdefault('addons', [])
        if kind == 'score' and p.kind in {'choice', 'selectable_addon'}:
            return p.value.setdefault('scores', [])
        if kind == 'requirement' and p.kind in {'row', 'backpack_row', 'choice', 'selectable_addon', 'addon', 'score', 'global_requirement', 'sound_effect', 'requirement'}:
            return p.value.setdefault('requireds', [])
        raise ValueError(f'cannot order {kind} under {p.kind}')

    def reorder(self, kind: str, order: list[str], *, parent: str | None = None, partial: bool = False) -> list[str]:
        if not order or not all(isinstance(x, str) and x for x in order):
            raise ValueError('order must be a non-empty list of IDs')
        if len(order) != len(set(order)):
            raise ValueError('order contains duplicate IDs')
        values = self._child_array(kind, parent)
        def item_id(value: dict[str, Any]) -> str:
            if kind == 'score':
                return str(value.get('idx', ''))
            if kind == 'category':
                return f"{value.get('type', '')}:{value.get('idx', '')}"
            return str(value.get('id', ''))
        by_id = {item_id(x): x for x in values if isinstance(x, dict)}
        missing = [x for x in order if x not in by_id]
        if missing:
            raise ValueError('order contains IDs not present in the target list: ' + ', '.join(missing))
        existing = [item_id(x) for x in values if isinstance(x, dict)]
        if not partial and set(order) != set(existing):
            omitted = [x for x in existing if x not in order]
            raise ValueError('complete reorder must include every target ID; omitted: ' + ', '.join(omitted))
        tail = [x for x in existing if x not in order]
        final = order + tail if partial else order
        values[:] = [by_id[x] for x in final]
        self.normalize()
        return final

    def move(self, reference: str, *, parent: str, index: int | None = None, normalize: bool = True) -> dict[str, Any]:
        ent = self.resolve(reference)
        if ent.kind not in {'choice', 'addon', 'selectable_addon', 'score', 'requirement'}:
            raise ValueError(f'move does not support {ent.kind}; use reorder for rows/top-level collections')
        target = self.resolve(parent)
        allowed = {
            'choice': {'row', 'backpack_row'},
            'addon': {'choice'}, 'selectable_addon': {'choice'},
            'score': {'choice', 'selectable_addon'},
            'requirement': {'row', 'backpack_row', 'choice', 'selectable_addon', 'addon', 'score', 'global_requirement', 'sound_effect', 'requirement'},
        }[ent.kind]
        if target.kind not in allowed:
            raise ValueError(f'cannot move {ent.kind} under {target.kind}')
        value = pointer_remove(self.project, ent.path)
        if ent.kind == 'choice': dest = target.value.setdefault('objects', [])
        elif ent.kind in {'addon', 'selectable_addon'}:
            dest = target.value.setdefault('addons', []); value['parentId'] = target.id
        elif ent.kind == 'score': dest = target.value.setdefault('scores', [])
        else: dest = target.value.setdefault('requireds', [])
        pos = len(dest) if index is None else index
        if not isinstance(pos, int) or isinstance(pos, bool) or pos < 0 or pos > len(dest):
            raise ValueError(f'index must be between 0 and {len(dest)}')
        dest.insert(pos, value)
        if normalize: self.normalize()
        return {'id': ent.id, 'kind': ent.kind, 'parent': target.id, 'index': pos}

    def clone(self, reference: str, *, parent: str | None = None, index: int | None = None, keep_unique_ids: bool = False, normalize: bool = True) -> dict[str, Any]:
        ent = self.resolve(reference)
        supported = {
            'row', 'backpack_row', 'choice', 'addon', 'selectable_addon', 'score', 'requirement',
            'point', 'variable', 'word', 'group', 'global_requirement',
            'row_design_group', 'choice_design_group', 'sound_effect', 'category',
        }
        if ent.kind not in supported:
            raise ValueError(f'clone does not support {ent.kind}')
        clone = copy.deepcopy(ent.value)
        validate_known_values(ent.kind, clone)
        mapping: dict[str, str] = {}
        if ent.kind == 'category':
            clone.pop('idx', None)
            clone = make_entity(self.project, 'category', clone)
        elif ent.kind not in {'addon', 'requirement'} or ent.kind == 'selectable_addon':
            mapping = _remap_cloned_identities(self.project, clone, ent.kind, keep_unique=keep_unique_ids)
        if ent.kind in {'row', 'backpack_row'}:
            for choice in clone.get('objects', []) if isinstance(clone.get('objects'), list) else []:
                if isinstance(choice, dict): _reset_choice_runtime(choice)
            dest = self.project.setdefault('backpack' if ent.kind == 'backpack_row' else 'rows', [])
        elif ent.kind == 'choice':
            _reset_choice_runtime(clone)
            target_parent = parent or ent.parent_id
            if not target_parent: raise ValueError('choice clone requires a destination parent')
            target = self.resolve(target_parent)
            if target.kind not in {'row', 'backpack_row'}: raise ValueError('choice destination must be a row')
            dest = target.value.setdefault('objects', [])
        elif ent.kind in {'addon', 'selectable_addon'}:
            target_parent = parent or ent.parent_id
            if not target_parent: raise ValueError('addon clone requires a destination parent')
            target = self.resolve(target_parent, 'choice')
            clone['parentId'] = target.id
            if ent.kind == 'selectable_addon': _reset_choice_runtime(clone)
            dest = target.value.setdefault('addons', [])
        elif ent.kind == 'score':
            target_parent = parent or ent.parent_id
            if not target_parent: raise ValueError('score clone requires a destination parent')
            target = self.resolve(target_parent)
            if target.kind not in {'choice', 'selectable_addon'}: raise ValueError('score destination must be a choice/selectable addon')
            _reset_score_runtime(clone)
            dest = target.value.setdefault('scores', [])
        elif ent.kind == 'requirement':
            target_parent = parent or ent.parent_id
            if not target_parent: raise ValueError('requirement clone requires a destination parent')
            target = self.resolve(target_parent)
            if target.kind not in {'row','backpack_row','choice','selectable_addon','addon','score','global_requirement','sound_effect','requirement'}:
                raise ValueError('invalid requirement destination')
            dest = target.value.setdefault('requireds', [])
        else:
            top = {
                'point': 'pointTypes', 'variable': 'variables', 'word': 'words', 'group': 'groups',
                'global_requirement': 'globalRequirements', 'row_design_group': 'rowDesignGroups',
                'choice_design_group': 'objectDesignGroups', 'sound_effect': 'soundEffects', 'category': 'categories',
            }
            dest = self.project.setdefault(top[ent.kind], [])
        pos = len(dest) if index is None else index
        if not isinstance(pos, int) or isinstance(pos, bool) or pos < 0 or pos > len(dest):
            raise ValueError(f'index must be between 0 and {len(dest)}')
        dest.insert(pos, clone)
        if normalize: self.normalize()
        if ent.kind == 'category':
            clone_id = f"{clone.get('type', '')}:{clone.get('idx', '')}"
        else:
            key = 'idx' if ent.kind == 'score' else 'id'
            clone_id = str(clone.get(key, ''))
        return {'source': ent.id, 'id': clone_id, 'kind': ent.kind, 'index': pos, 'id_map': mapping, 'value': clone}

    def import_fragment(self, kind: str, value: dict[str, Any], *, parent: str | None = None, index: int | None = None, normalize: bool = True) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise ValueError('fragment must be a JSON object')
        clone = copy.deepcopy(value)
        validate_known_values(kind, clone)
        # Preserve imported IDs when they are unique, like the Creator import
        # path, and deterministically remap only collisions.
        if kind == 'category':
            typ = clone.get('type')
            idx = clone.get('idx')
            collision = any(
                isinstance(cat, dict) and cat.get('type') == typ and cat.get('idx') == idx
                for cat in self.project.get('categories', [])
            )
            if collision:
                clone.pop('idx', None)
                clone = make_entity(self.project, 'category', clone)
            else:
                # Reuse the factory validation for Creator category type and slot bounds.
                clone = make_entity(self.project, 'category', clone)
            mapping = {}
        else:
            mapping = {} if kind in {'addon', 'requirement'} else _remap_cloned_identities(self.project, clone, kind, keep_unique=True)
        if kind in {'row', 'backpack_row'}:
            for choice in clone.get('objects', []) if isinstance(clone.get('objects'), list) else []:
                if isinstance(choice, dict): _reset_choice_runtime(choice)
            dest = self.project.setdefault('backpack' if kind == 'backpack_row' else 'rows', [])
        elif kind == 'choice':
            if not parent: raise ValueError('choice import requires --parent row ID')
            target = self.resolve(parent)
            if target.kind not in {'row','backpack_row'}: raise ValueError('choice destination must be a row')
            _reset_choice_runtime(clone); dest = target.value.setdefault('objects', [])
        elif kind in {'addon','selectable_addon'}:
            if not parent: raise ValueError('addon import requires --parent choice ID')
            target = self.resolve(parent, 'choice'); clone['parentId'] = target.id
            if kind == 'selectable_addon': _reset_choice_runtime(clone)
            dest = target.value.setdefault('addons', [])
        elif kind == 'score':
            if not parent: raise ValueError('score import requires --parent choice/selectable Addon ID')
            target = self.resolve(parent)
            if target.kind not in {'choice','selectable_addon'}: raise ValueError('score destination must be a choice/selectable addon')
            _reset_score_runtime(clone); dest = target.value.setdefault('scores', [])
        elif kind == 'requirement':
            if not parent: raise ValueError('requirement import requires --parent')
            target = self.resolve(parent); dest = target.value.setdefault('requireds', [])
        elif kind in {'point','variable','word','group','global_requirement','row_design_group','choice_design_group','sound_effect','category'}:
            top = {
                'point': 'pointTypes', 'variable': 'variables', 'word': 'words', 'group': 'groups',
                'global_requirement': 'globalRequirements', 'row_design_group': 'rowDesignGroups',
                'choice_design_group': 'objectDesignGroups', 'sound_effect': 'soundEffects', 'category': 'categories',
            }
            dest = self.project.setdefault(top[kind], [])
        else:
            raise ValueError(f'import-fragment does not support {kind}')
        pos = len(dest) if index is None else index
        if not isinstance(pos, int) or isinstance(pos, bool) or pos < 0 or pos > len(dest):
            raise ValueError(f'index must be between 0 and {len(dest)}')
        dest.insert(pos, clone)
        if normalize: self.normalize_and_check()
        if kind == 'category':
            imported_id = f"{clone.get('type', '')}:{clone.get('idx', '')}"
        else:
            key = 'idx' if kind == 'score' else 'id'
            imported_id = str(clone.get(key, ''))
        return {'id': imported_id, 'kind': kind, 'index': pos, 'id_map': mapping, 'value': clone}

    def set(self, pointer: str, value: Any) -> None: pointer_set(self.project, pointer, value)
    def remove(self, pointer: str) -> Any: return pointer_remove(self.project, pointer)
