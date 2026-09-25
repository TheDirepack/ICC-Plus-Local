from __future__ import annotations

import copy
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .field_catalog import STYLE_FIELD_GROUPS
from .model import Entity, ProjectIndex
from .selectors import select_entities, check_expected_count
from .image_assets import prepare_image_reference
from .creator_helpers import import_design

VISUAL_KINDS = {'row', 'backpack_row', 'choice', 'addon', 'selectable_addon'}
_STYLE_FIELDS = {field for fields in STYLE_FIELD_GROUPS.values() for field in fields}
_VISUAL_SPEC_KEYS = {
    'image', 'clear_image', 'template', 'width', 'styling', 'copy_from', 'copy_image',
    'replace_styling', 'unset_styling',
}
_ITEM_META_KEYS = {
    'ref', 'id', 'refs', 'where', 'expect', 'allow_empty', 'preset', 'presets',
    'design_group', 'design_groups', 'source', 'credit', 'notes',
}
_DESIGN_GROUP_SPEC_KEYS = {'kind', 'name', 'activated_id', 'category', 'groups', 'styling', 'replace_styling', 'unset_styling'}


def _strings(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(x) for x in value if isinstance(x, str) and x]
    return []


def _display_ref(ent: Entity) -> str:
    return ent.path if ent.id.startswith('@') else ent.id


def _width_field(kind: str) -> str | None:
    if kind in {'row', 'backpack_row', 'choice'}:
        return 'objectWidth'
    if kind in {'addon', 'selectable_addon'}:
        return 'addonWidth'
    return None


def _visual_family(kind: str) -> str:
    if kind in {'row', 'backpack_row'}:
        return 'row'
    if kind == 'choice':
        return 'choice'
    if kind in {'addon', 'selectable_addon'}:
        return 'addon'
    return kind


def _flatten_styling(value: Any, *, label: str = 'styling') -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f'{label} must be an object')
    out: dict[str, Any] = {}
    for key, raw in value.items():
        if key in STYLE_FIELD_GROUPS:
            if not isinstance(raw, dict):
                raise ValueError(f'{label}.{key} must be an object')
            allowed = set(STYLE_FIELD_GROUPS[key])
            unknown = set(raw) - allowed
            if unknown:
                raise ValueError(f'unknown {key} styling field(s): {", ".join(sorted(unknown))}')
            for field, field_value in raw.items():
                if field in out and out[field] != field_value:
                    raise ValueError(f'{label} sets {field!r} more than once with different values')
                out[field] = copy.deepcopy(field_value)
            continue
        if key not in _STYLE_FIELDS:
            raise ValueError(
                f'unknown styling field {key!r}; use `fields styling --contains TEXT` or group fields under a native styling group'
            )
        out[key] = copy.deepcopy(raw)
    return out




def _validate_design_group_spec(name: str, spec: Any) -> dict[str, Any]:
    if not isinstance(spec, dict):
        raise ValueError(f'design_groups.{name} must be an object')
    unknown = set(spec) - _DESIGN_GROUP_SPEC_KEYS
    if unknown:
        raise ValueError(f'unknown design_groups.{name} field(s): {", ".join(sorted(unknown))}')
    kind = spec.get('kind')
    if kind not in {'row', 'choice'}:
        raise ValueError(f'design_groups.{name}.kind must be "row" or "choice"')
    if 'styling' in spec:
        _flatten_styling(spec.get('styling'), label=f'design_groups.{name}.styling')
    unset = spec.get('unset_styling')
    if unset is not None:
        if not isinstance(unset, list) or any(not isinstance(x, str) or not x for x in unset):
            raise ValueError(f'design_groups.{name}.unset_styling must be an array of non-empty strings')
        unknown_style = set(unset) - _STYLE_FIELDS
        if unknown_style:
            raise ValueError(f'unknown design_groups.{name}.unset_styling field(s): {", ".join(sorted(unknown_style))}')
    if 'activated_id' in spec and not isinstance(spec.get('activated_id'), str):
        raise ValueError(f'design_groups.{name}.activated_id must be a string')
    if 'groups' in spec:
        groups = spec.get('groups')
        if not isinstance(groups, list) or any(not isinstance(x, str) or not x.strip() for x in groups):
            raise ValueError(f'design_groups.{name}.groups must be an array of non-empty Group IDs')
    if 'category' in spec and (not isinstance(spec.get('category'), int) or isinstance(spec.get('category'), bool)):
        raise ValueError(f'design_groups.{name}.category must be an integer')
    return spec


def _upsert_design_group(project: dict[str, Any], design_id: str, spec: dict[str, Any]) -> dict[str, Any]:
    _validate_design_group_spec(design_id, spec)
    if not design_id:
        raise ValueError('design group IDs must be non-empty strings')
    entity_kind = 'row_design_group' if spec['kind'] == 'row' else 'choice_design_group'
    collection_key = 'rowDesignGroups' if spec['kind'] == 'row' else 'objectDesignGroups'

    idx = ProjectIndex(project)
    matches = idx.find(design_id)
    same = [ent for ent in matches if ent.kind == entity_kind]
    if len(same) > 1:
        raise ValueError(f'design group ID is ambiguous: {design_id}')
    if matches and not same:
        raise ValueError(f'design group ID {design_id!r} collides with another project entity')

    changed: list[str] = []
    created = not same
    if same:
        group = same[0].value
    else:
        groups = project.setdefault(collection_key, [])
        if not isinstance(groups, list):
            raise ValueError(f'project.{collection_key} must be an array')
        group = {
            'id': design_id,
            'name': str(spec.get('name') or design_id),
            'activatedId': str(spec.get('activated_id') or ''),
            'elements': [],
            'backpackElements': [],
            'groupElements': [],
            'styling': {},
            'category': int(spec.get('category', -1)),
        }
        groups.append(group)
        changed.append('created')

    if 'name' in spec:
        name = str(spec.get('name') or design_id)
        if group.get('name') != name:
            group['name'] = name
            changed.append('name')
    if 'activated_id' in spec:
        value = str(spec.get('activated_id') or '')
        if group.get('activatedId') != value:
            group['activatedId'] = value
            changed.append('activatedId')
    if 'category' in spec:
        value = int(spec['category'])
        if group.get('category') != value:
            group['category'] = value
            changed.append('category')

    if 'groups' in spec:
        linked_groups = list(dict.fromkeys(x.strip() for x in spec.get('groups') or []))
        group_elements = group.get('groupElements')
        if not isinstance(group_elements, list):
            group_elements = []
            group['groupElements'] = group_elements
        idx = ProjectIndex(project)
        for group_id in linked_groups:
            normal_group = idx.one(group_id, 'group')
            if normal_group is None:
                raise ValueError(f'design_groups.{design_id}.groups references missing Group {group_id!r}')
            if group_id not in group_elements:
                group_elements.append(group_id)
                changed.append('groupElements')
            memberships = normal_group.value.get('designGroups')
            if not isinstance(memberships, list):
                memberships = []
                normal_group.value['designGroups'] = memberships
            if design_id not in memberships:
                memberships.append(design_id)
                changed.append(f'group.{group_id}.designGroups')

    if 'styling' in spec or spec.get('replace_styling') is True or spec.get('unset_styling'):
        current = group.get('styling') if isinstance(group.get('styling'), dict) else {}
        final_style = {} if spec.get('replace_styling') is True else copy.deepcopy(current)
        final_style.update(_flatten_styling(spec.get('styling'), label=f'design_groups.{design_id}.styling'))
        for key in spec.get('unset_styling') or []:
            final_style.pop(key, None)
        if final_style != current:
            changed.append('styling')
        info = import_design(project, design_id, {'version': project.get('version'), 'styling': final_style})
        for key in info.get('private_switches', {}):
            changed.append(key)

    return {
        'id': design_id,
        'kind': entity_kind,
        'created': created,
        'changed': list(dict.fromkeys(changed)),
    }


def _design_group_refs(value: Any, *, label: str) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list) or any(not isinstance(x, str) or not x.strip() for x in value):
        raise ValueError(f'{label} must be a non-empty string or array of non-empty strings')
    return list(dict.fromkeys(x.strip() for x in value))


def _assign_design_groups(project: dict[str, Any], ent: Entity, design_ids: list[str]) -> list[str]:
    if not design_ids:
        return []
    if ent.kind in {'row', 'backpack_row'}:
        target_kind = 'row_design_group'
        field = 'rowDesignGroups'
    elif ent.kind == 'choice':
        target_kind = 'choice_design_group'
        field = 'objectDesignGroups'
    else:
        raise ValueError(
            f'official Design Groups apply to Rows and Choices, not {ent.kind}; '
            'style the parent Row/Choice or use private styling only when no reusable scope fits'
        )

    memberships = ent.value.get(field)
    if not isinstance(memberships, list):
        memberships = []
        ent.value[field] = memberships

    idx = ProjectIndex(project)
    changed: list[str] = []
    for design_id in design_ids:
        group = idx.one(design_id, target_kind)
        if group is None:
            other = idx.find(design_id)
            if other:
                raise ValueError(f'design group {design_id!r} exists but is not a {target_kind.replace("_", " ")}')
            raise ValueError(f'design group not found: {design_id}')
        if design_id not in memberships:
            memberships.append(design_id)
            changed.append(field)

        is_backpack = ent.kind == 'backpack_row' or ent.path.startswith('/backpack/')
        member_field = 'backpackElements' if is_backpack else 'elements'
        members = group.value.get(member_field)
        if not isinstance(members, list):
            members = []
            group.value[member_field] = members
        if ent.id not in members:
            members.append(ent.id)
            changed.append(f'{target_kind}.{design_id}.{member_field}')
    return changed


def _image_kind(image: str) -> str:
    if not image:
        return 'none'
    if image.startswith('data:'):
        return 'embedded'
    if image.startswith('//'):
        return 'remote'
    parsed = urlparse(image)
    if parsed.scheme in {'http', 'https'}:
        return 'remote'
    if parsed.scheme:
        return 'external'
    return 'local'


def _validate_visual_spec(spec: Any, *, label: str) -> dict[str, Any]:
    if spec is None:
        return {}
    if not isinstance(spec, dict):
        raise ValueError(f'{label} must be an object')
    unknown = set(spec) - _VISUAL_SPEC_KEYS
    if unknown:
        raise ValueError(f'unknown {label} field(s): {", ".join(sorted(unknown))}')
    if spec.get('clear_image') is True and 'image' in spec:
        raise ValueError(f'{label} cannot set image and clear_image together')
    if 'styling' in spec:
        _flatten_styling(spec.get('styling'), label=f'{label}.styling')
    unset = spec.get('unset_styling')
    if unset is not None:
        if not isinstance(unset, list) or any(not isinstance(x, str) or not x for x in unset):
            raise ValueError(f'{label}.unset_styling must be an array of non-empty strings')
        unknown_style = set(unset) - _STYLE_FIELDS
        if unknown_style:
            raise ValueError(f'unknown {label}.unset_styling field(s): {", ".join(sorted(unknown_style))}')
    return spec


def _style_groups_used(styling: Any) -> dict[str, list[str]]:
    if not isinstance(styling, dict):
        return {}
    keys = set(styling)
    out: dict[str, list[str]] = {}
    for group, fields in STYLE_FIELD_GROUPS.items():
        present = sorted(keys & set(fields))
        if present:
            out[group] = present
    unknown = sorted(keys - _STYLE_FIELDS)
    if unknown:
        out['other'] = unknown
    return out


def _text_excerpt(ent: Entity, limit: int = 180) -> str:
    raw = ent.value.get('text')
    if raw is None:
        raw = ent.value.get('titleText')
    text = ' '.join(str(raw or '').split())
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + '…'


def visual_audit(
    project: dict[str, Any],
    *,
    kinds: list[str] | None = None,
    row: str | None = None,
    group: str | None = None,
    missing_images: bool = False,
    missing_assets: bool = False,
    unstyled: bool = False,
    limit: int | None = None,
    asset_root: str | Path | None = None,
    manifest_stub: bool = False,
    style_values: bool = False,
) -> dict[str, Any]:
    idx = ProjectIndex(project)
    wanted_kinds = set(kinds or ['row', 'choice', 'selectable_addon', 'addon'])
    bad = wanted_kinds - VISUAL_KINDS
    if bad:
        raise ValueError(f'unsupported visual kind(s): {", ".join(sorted(bad))}')
    if missing_assets and not asset_root:
        raise ValueError('--missing-assets requires --asset-root')
    if missing_images and missing_assets:
        raise ValueError('--missing-images and --missing-assets cannot be combined')
    if limit is not None and limit < 0:
        raise ValueError('visual audit limit cannot be negative')

    entities = [e for e in idx.entities if e.kind in wanted_kinds]
    if row:
        entities = [e for e in entities if e.row_id == row or (e.kind in {'row', 'backpack_row'} and e.id == row)]
    if group:
        g = idx.one(group, 'group')
        if not g:
            raise ValueError(f'group not found: {group}')
        members = set(_strings(g.value.get('elements'))) | set(_strings(g.value.get('rowElements')))
        entities = [e for e in entities if e.id in members or group in _strings(e.value.get('groups'))]

    root = Path(asset_root).expanduser().resolve() if asset_root else None
    rows_by_id = {e.id: e for e in idx.by_kind.get('row', []) + idx.by_kind.get('backpack_row', [])}
    matched: list[dict[str, Any]] = []
    totals = {
        'total': 0, 'with_image': 0, 'missing_image': 0, 'inline_styled': 0, 'design_grouped': 0,
        'local_images': 0, 'remote_images': 0, 'embedded_images': 0, 'external_images': 0,
        'missing_local_assets': 0,
    }

    for ent in entities:
        image = str(ent.value.get('image') or '').strip()
        image_kind = _image_kind(image)
        styling = ent.value.get('styling') if isinstance(ent.value.get('styling'), dict) else {}
        design_groups = _strings(ent.value.get('rowDesignGroups')) + _strings(ent.value.get('objectDesignGroups')) + _strings(ent.value.get('designGroups'))
        row_ent = rows_by_id.get(ent.row_id or '')
        item: dict[str, Any] = {
            'ref': _display_ref(ent),
            'id': None if ent.id.startswith('@') else ent.id,
            'kind': ent.kind,
            'title': ent.title,
            'row_id': ent.row_id,
            'row_title': row_ent.title if row_ent else None,
            'parent_id': ent.parent_id,
            'image': image,
            'has_image': bool(image),
            'image_kind': image_kind,
            'template': ent.value.get('template'),
            'width': ent.value.get(_width_field(ent.kind)) if _width_field(ent.kind) else None,
            'text_chars': len(str(ent.value.get('text') or ent.value.get('titleText') or '')),
            'text_excerpt': _text_excerpt(ent),
            'style_groups': _style_groups_used(styling),
            'groups': _strings(ent.value.get('groups')),
            'design_groups': list(dict.fromkeys(design_groups)),
        }
        if style_values and styling:
            item['styling'] = copy.deepcopy(styling)
        if root is not None and image_kind == 'local':
            candidate = (root / image).resolve()
            item['asset_path'] = str(candidate)
            try:
                within = candidate.is_relative_to(root)
            except AttributeError:
                within = str(candidate).startswith(str(root))
            item['asset_within_root'] = within
            item['asset_exists'] = candidate.is_file()
            if candidate.is_file():
                item['asset_bytes'] = candidate.stat().st_size

        if missing_images and image:
            continue
        if missing_assets and not (image_kind == 'local' and item.get('asset_exists') is False):
            continue
        if unstyled and (styling or design_groups):
            continue

        matched.append(item)
        totals['total'] += 1
        totals['with_image' if image else 'missing_image'] += 1
        if styling:
            totals['inline_styled'] += 1
        if design_groups:
            totals['design_grouped'] += 1
        if image_kind == 'local':
            totals['local_images'] += 1
            if root is not None and item.get('asset_exists') is False:
                totals['missing_local_assets'] += 1
        elif image_kind == 'remote':
            totals['remote_images'] += 1
        elif image_kind == 'embedded':
            totals['embedded_images'] += 1
        elif image_kind == 'external':
            totals['external_images'] += 1

    returned = matched if limit is None else matched[:limit]
    totals['returned'] = len(returned)
    totals['truncated'] = len(returned) < len(matched)

    report = {
        'format': 'iccplus-visual-audit',
        'format_version': 1,
        'summary': totals,
        'filters': {
            'kinds': sorted(wanted_kinds),
            'row': row,
            'group': group,
            'missing_images': bool(missing_images),
            'missing_assets': bool(missing_assets),
            'unstyled': bool(unstyled),
            'limit': limit,
            'asset_root': str(root) if root else None,
            'style_values': bool(style_values),
        },
        'items': returned,
    }
    if manifest_stub:
        report['manifest_stub'] = {
            'format': 'iccplus-visual-manifest',
            'format_version': 1,
            'items': [
                ({'id': item['id']} if item.get('id') else {'ref': item['ref']})
                for item in returned
            ],
        }
    return report


def _resolve_target(idx: ProjectIndex, ref: str) -> Entity:
    matches = idx.find(ref)
    if len(matches) != 1:
        if not matches:
            raise ValueError(f'visual target not found: {ref}')
        raise ValueError(f'visual target is ambiguous: {ref}')
    ent = matches[0]
    if ent.kind not in VISUAL_KINDS:
        raise ValueError(f'visual target {ref!r} has unsupported kind {ent.kind!r}')
    return ent


def _merge_style(target: dict[str, Any], values: dict[str, Any]) -> list[str]:
    if not values:
        return []
    styling = target.get('styling')
    if not isinstance(styling, dict):
        styling = {}
        target['styling'] = styling
    changed: list[str] = []
    for key, value in values.items():
        if styling.get(key) != value:
            styling[key] = copy.deepcopy(value)
            changed.append(key)
    return changed


def _apply_visual_spec(ent: Entity, spec: dict[str, Any], *, source: Entity | None = None) -> dict[str, Any]:
    _validate_visual_spec(spec, label=f'visual target {ent.id}')
    target = ent.value
    changed: list[str] = []

    if spec.get('replace_styling') is True:
        current = target.get('styling')
        if current != {}:
            target['styling'] = {}
            changed.append('styling')

    if source is not None:
        if _visual_family(source.kind) != _visual_family(ent.kind):
            raise ValueError(f'copy_from visual family mismatch: {source.kind} -> {ent.kind}')
        for key in ('template',):
            if key in source.value and target.get(key) != source.value.get(key):
                target[key] = copy.deepcopy(source.value.get(key)); changed.append(key)
        sw = _width_field(source.kind); tw = _width_field(ent.kind)
        if sw and tw and sw in source.value and target.get(tw) != source.value.get(sw):
            target[tw] = copy.deepcopy(source.value.get(sw)); changed.append(tw)
        source_style = source.value.get('styling') if isinstance(source.value.get('styling'), dict) else {}
        changed.extend('styling.' + k for k in _merge_style(target, source_style))
        if spec.get('copy_image') is True and target.get('image') != source.value.get('image', ''):
            target['image'] = copy.deepcopy(source.value.get('image', '')); changed.append('image')

    if spec.get('clear_image') is True:
        if target.get('image') != '':
            target['image'] = ''; changed.append('image')
    elif 'image' in spec:
        image = str(spec.get('image') or '')
        if target.get('image') != image:
            target['image'] = image; changed.append('image')

    if 'template' in spec:
        if target.get('template') != spec['template']:
            target['template'] = copy.deepcopy(spec['template']); changed.append('template')
    if 'width' in spec:
        width_field = _width_field(ent.kind)
        if not width_field:
            raise ValueError(f'width is not supported for {ent.kind}')
        if target.get(width_field) != spec['width']:
            target[width_field] = copy.deepcopy(spec['width']); changed.append(width_field)

    style = _flatten_styling(spec.get('styling'), label=f'visual target {ent.id}.styling')
    changed.extend('styling.' + k for k in _merge_style(target, style))

    unset = spec.get('unset_styling') or []
    if unset:
        styling = target.get('styling')
        if isinstance(styling, dict):
            for key in unset:
                if key in styling:
                    del styling[key]
                    changed.append('styling.' + key)
    return {'ref': _display_ref(ent), 'kind': ent.kind, 'changed': list(dict.fromkeys(changed))}


def apply_visual_manifest(
    project: dict[str, Any],
    manifest: dict[str, Any],
    *,
    asset_base: Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if not isinstance(manifest, dict):
        raise ValueError('visual manifest must be an object')
    allowed_top = {'format', 'format_version', 'project', 'design_groups', 'defaults', 'presets', 'items'}
    unknown_top = set(manifest) - allowed_top
    if unknown_top:
        raise ValueError(f'unknown visual manifest field(s): {", ".join(sorted(unknown_top))}')
    if manifest.get('format') not in {None, 'iccplus-visual-manifest'}:
        raise ValueError('unsupported visual manifest format')
    version = manifest.get('format_version', 1)
    if version != 1:
        raise ValueError(f'unsupported visual manifest format_version: {version}')

    updated = copy.deepcopy(project)

    design_group_specs = manifest.get('design_groups') or {}
    if not isinstance(design_group_specs, dict):
        raise ValueError('visual manifest design_groups must be an object')
    design_group_results: list[dict[str, Any]] = []
    for design_id, spec in design_group_specs.items():
        if not isinstance(design_id, str) or not design_id.strip():
            raise ValueError('visual manifest design_groups keys must be non-empty strings')
        design_group_results.append(_upsert_design_group(updated, design_id.strip(), spec))

    presets = manifest.get('presets') or {}
    if not isinstance(presets, dict):
        raise ValueError('visual manifest presets must be an object')
    for name, preset in presets.items():
        _validate_visual_spec(preset, label=f'visual preset {name!r}')
    defaults = manifest.get('defaults') or {}
    _validate_visual_spec(defaults, label='visual manifest defaults')

    project_spec = manifest.get('project') or {}
    if not isinstance(project_spec, dict):
        raise ValueError('visual manifest project must be an object')
    allowed_project = {'styling', 'customCSS', 'customCSSAppend'}
    unknown_project = set(project_spec) - allowed_project
    if unknown_project:
        raise ValueError(f'unknown visual manifest project field(s): {", ".join(sorted(unknown_project))}')
    project_changes: list[str] = []
    if 'styling' in project_spec:
        style = _flatten_styling(project_spec.get('styling'), label='project.styling')
        project_changes.extend('styling.' + k for k in _merge_style(updated, style))
    if 'customCSS' in project_spec:
        css = str(project_spec.get('customCSS') or '')
        if updated.get('customCSS') != css:
            updated['customCSS'] = css; project_changes.append('customCSS')
    if 'customCSSAppend' in project_spec:
        appendix = str(project_spec.get('customCSSAppend') or '')
        if appendix:
            current = str(updated.get('customCSS') or '')
            if appendix not in current:
                joiner = '' if not current or current.endswith('\n') else '\n'
                updated['customCSS'] = current + joiner + appendix
                project_changes.append('customCSS')

    items = manifest.get('items') or []
    if not isinstance(items, list):
        raise ValueError('visual manifest items must be an array')
    idx = ProjectIndex(updated)
    results: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []
    seen_targets: set[str] = set()
    for n, raw in enumerate(items):
        if not isinstance(raw, dict):
            raise ValueError(f'visual manifest items[{n}] must be an object')
        unknown_item = set(raw) - _ITEM_META_KEYS - _VISUAL_SPEC_KEYS
        if unknown_item:
            raise ValueError(f'unknown visual manifest items[{n}] field(s): {", ".join(sorted(unknown_item))}')

        single_ref = str(raw.get('ref') or raw.get('id') or '').strip()
        refs_value = raw.get('refs')
        where_value = raw.get('where')
        target_forms = int(bool(single_ref)) + int(refs_value is not None) + int(where_value is not None)
        if target_forms != 1:
            raise ValueError(f'visual manifest items[{n}] needs exactly one target form: ref/id, refs, or where')
        if refs_value is not None:
            if not isinstance(refs_value, list) or not refs_value or any(not isinstance(x, str) or not x.strip() for x in refs_value):
                raise ValueError(f'visual manifest items[{n}].refs must be a non-empty array of strings')
            target_refs = [x.strip() for x in refs_value]
        elif where_value is not None:
            if not isinstance(where_value, dict):
                raise ValueError(f'visual manifest items[{n}].where must be an object')
            matches = select_entities(updated, where_value)
            if raw.get('expect') is not None:
                check_expected_count(len(matches), raw.get('expect'), label=f'visual manifest items[{n}]')
            if not matches and not bool(raw.get('allow_empty', False)):
                raise ValueError(f'visual manifest items[{n}] selected 0 entities; set allow_empty=true only when that is intentional')
            target_refs = [_display_ref(ent) for ent in matches]
        else:
            target_refs = [single_ref]

        requested_presets = raw.get('presets', raw.get('preset', []))
        if isinstance(requested_presets, str):
            requested_presets = [requested_presets]
        if requested_presets is None:
            requested_presets = []
        if not isinstance(requested_presets, list) or any(not isinstance(x, str) for x in requested_presets):
            raise ValueError(f'visual manifest items[{n}].preset(s) must be a string or array of strings')

        combined: dict[str, Any] = copy.deepcopy(defaults)
        for preset_name in requested_presets:
            preset = presets.get(preset_name)
            if not isinstance(preset, dict):
                raise ValueError(f'visual preset not found or not an object: {preset_name}')
            combined = _deep_merge(combined, preset)
        item_spec = {k: copy.deepcopy(v) for k, v in raw.items() if k in _VISUAL_SPEC_KEYS}
        combined = _deep_merge(combined, item_spec)
        _validate_visual_spec(combined, label=f'visual manifest items[{n}]')
        inline_style = _flatten_styling(combined.get('styling'), label=f'visual manifest items[{n}].styling')
        if inline_style and len(target_refs) > 1:
            raise ValueError(
                f'visual manifest items[{n}] applies private inline styling to {len(target_refs)} targets; '
                'define an official Design Group and assign it instead'
            )
        if 'design_group' in raw and 'design_groups' in raw:
            raise ValueError(f'visual manifest items[{n}] cannot set both design_group and design_groups')
        requested_design_groups = raw.get('design_groups', raw.get('design_group'))
        design_ids = _design_group_refs(
            requested_design_groups,
            label=f'visual manifest items[{n}].design_group(s)',
        ) if requested_design_groups is not None else []

        image_compression = None
        if 'image' in combined and str(combined.get('image') or ''):
            optimized, image_compression = prepare_image_reference(
                str(combined.get('image') or ''),
                base_dir=asset_base,
                embed_local=False,
            )
            combined['image'] = optimized

        for ref in target_refs:
            ent = _resolve_target(idx, ref)
            canonical = _display_ref(ent)
            if canonical in seen_targets:
                raise ValueError(f'visual target appears more than once in one manifest: {canonical}')
            seen_targets.add(canonical)

            source_ent = None
            copy_from = combined.get('copy_from')
            if copy_from:
                source_ent = _resolve_target(idx, str(copy_from))
            result = _apply_visual_spec(ent, combined, source=source_ent)
            design_changes = _assign_design_groups(updated, ent, design_ids)
            if design_changes:
                result['changed'] = list(dict.fromkeys(result['changed'] + design_changes))
            result['design_groups'] = list(design_ids)
            result['presets'] = list(requested_presets)
            result['image'] = str(ent.value.get('image') or '')
            if image_compression is not None:
                result['image_compression'] = copy.deepcopy(image_compression)
            if 'source' in raw or 'credit' in raw or 'notes' in raw:
                record = {'ref': canonical, 'title': ent.title, 'image': result['image']}
                for key in ('source', 'credit', 'notes'):
                    if key in raw:
                        record[key] = copy.deepcopy(raw[key])
                sources.append(record)
            results.append(result)

    return updated, {
        'format': 'iccplus-visual-apply-report',
        'format_version': 1,
        'project_changes': list(dict.fromkeys(project_changes)),
        'design_groups': design_group_results,
        'items': results,
        'source_records': sources,
        'changed_items': sum(1 for x in results if x['changed']),
        'unchanged_items': sum(1 for x in results if not x['changed']),
    }


def _deep_merge(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(left)
    for key, value in right.items():
        if key == 'styling' and isinstance(value, dict) and isinstance(out.get(key), dict):
            # Merge grouped style objects without discarding earlier preset groups.
            merged = copy.deepcopy(out[key])
            for sk, sv in value.items():
                if isinstance(sv, dict) and isinstance(merged.get(sk), dict):
                    inner = copy.deepcopy(merged[sk]); inner.update(copy.deepcopy(sv)); merged[sk] = inner
                else:
                    merged[sk] = copy.deepcopy(sv)
            out[key] = merged
        else:
            out[key] = copy.deepcopy(value)
    return out
