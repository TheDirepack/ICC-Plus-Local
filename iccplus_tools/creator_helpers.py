from __future__ import annotations

from copy import deepcopy
from html.parser import HTMLParser
from typing import Any

from .field_catalog import STYLE_FIELD_GROUPS
from .editor import ProjectEditor
from .field_types import FIELD_TYPE_CODES, validate_known_values
from .model import ProjectIndex
from .upstream_2106 import ICCPLUS_VERSION

_PRIVATE_ROW_FIELDS = (
    'privateAddonImageIsOn', 'privateAddonIsOn', 'privateBackgroundIsOn',
    'privateFilterIsOn', 'privateMultiChoiceIsOn', 'privateObjectImageIsOn',
    'privateObjectIsOn', 'privateRowImageIsOn', 'privateRowIsOn',
    'privateTextIsOn', 'isPrivateStyling', 'styling',
)
CREATOR_SYMBOLS = [
    '✅', '✓', '✔', '🗸', '☑', '🗹', '♂', '♀', '⚥', '⚢', '⚣', '⚤', '⚦', '⚧', '⚨', '⚩',
    '•', '◘', '○', '◙', '•', '‣', '⁃', '⁌', '⁍', '◘', '◦', '⦾', '⦿', '♥', '♡', '🖤', '💙',
    '💚', '💛', '💜', '🧡', '🤍', '🤎', '❣', '❤', '❥', '🎔', '💓', '💔', '💖', '💗', '💕', '💞',
    '💘', '↑', '↓', '→', '←', '↔', '↕', '↨', '▲', '▼', '►', '◄', '⤴', '⤵', '↩', '↪', '🏹', '⭐',
    '★', '☆', '★', '✯',
]

_PRIVATE_CHOICE_FIELDS = (
    'privateAddonImageIsOn', 'privateAddonIsOn', 'privateBackgroundIsOn',
    'privateFilterIsOn', 'privateMultiChoiceIsOn', 'privateObjectImageIsOn',
    'privateObjectIsOn', 'privateTextIsOn', 'isPrivateStyling', 'styling',
)


def js_string_length(value: Any) -> int:
    """JavaScript String.length, measured in UTF-16 code units."""
    if not isinstance(value, str):
        return 0
    return len(value.encode('utf-16-le')) // 2


def project_stats(project: dict[str, Any]) -> dict[str, Any]:
    """Mirror ICC Plus 2.10.6 Creator AppProjectStats.svelte."""
    char_count = 0
    choice_count = 0
    image_count = 0
    row_count = 0
    biggest_size = 0
    biggest_name = ''
    smallest_size = 0
    smallest_name = ''

    def image(value: Any, name: Any) -> None:
        nonlocal image_count, biggest_size, biggest_name, smallest_size, smallest_name
        if not isinstance(value, str) or not value:
            return
        size = js_string_length(value)
        if size > biggest_size:
            biggest_size = size
            biggest_name = str(name or '')
        if smallest_size == 0 or size < smallest_size:
            smallest_size = size
            smallest_name = str(name or '')
        image_count += 1

    for row in list(project.get('rows', []) or []) + list(project.get('backpack', []) or []):
        if not isinstance(row, dict):
            continue
        row_count += 1
        char_count += js_string_length(row.get('title'))
        char_count += js_string_length(row.get('titleText'))
        image(row.get('image'), row.get('title'))
        for choice in row.get('objects', []) if isinstance(row.get('objects'), list) else []:
            if not isinstance(choice, dict):
                continue
            choice_count += 1
            char_count += js_string_length(choice.get('title'))
            char_count += js_string_length(choice.get('text'))
            image(choice.get('image'), choice.get('title'))
            for addon in choice.get('addons', []) if isinstance(choice.get('addons'), list) else []:
                if not isinstance(addon, dict):
                    continue
                char_count += js_string_length(addon.get('title'))
                char_count += js_string_length(addon.get('text'))
                image(addon.get('image'), addon.get('title'))

    raw_minutes = char_count / 175 + image_count * 5
    return {
        'character_count': char_count,
        'choice_count': choice_count,
        'image_count': image_count,
        'row_count': row_count,
        'biggest_image_kb': biggest_size // 1024,
        'biggest_image_name': biggest_name,
        'smallest_image_kb': smallest_size // 1024,
        'smallest_image_name': smallest_name,
        'estimated_minutes': int(raw_minutes // 1),
        'estimated_hours': float(f'{raw_minutes / 60:.1f}'),
        'assumptions': {'characters_per_minute': 175, 'minutes_per_picture': 5},
    }


def clean_private_styling(project: dict[str, Any]) -> dict[str, int]:
    """Mirror the Creator's Clean All Private Styling action exactly."""
    rows_changed = 0
    choices_changed = 0
    fields_removed = 0
    for row in list(project.get('rows', []) or []) + list(project.get('backpack', []) or []):
        if not isinstance(row, dict):
            continue
        changed = False
        for key in _PRIVATE_ROW_FIELDS:
            if key in row:
                del row[key]
                fields_removed += 1
                changed = True
        rows_changed += int(changed)
        for choice in row.get('objects', []) if isinstance(row.get('objects'), list) else []:
            if not isinstance(choice, dict):
                continue
            changed = False
            for key in _PRIVATE_CHOICE_FIELDS:
                if key in choice:
                    del choice[key]
                    fields_removed += 1
                    changed = True
            choices_changed += int(changed)
    return {
        'rows_changed': rows_changed,
        'choices_changed': choices_changed,
        'fields_removed': fields_removed,
    }


# ICC Plus 2.10.6 ``objectWidths`` order from store.svelte.ts.  Row Settings
# sorts against the position in this array, including the empty "inherit Row"
# value at index 0.
OBJECT_WIDTH_ORDER = (
    '', 'col-12', 'col-sm-11', 'col-sm-10', 'col-sm-9', 'col-sm-8',
    'col-sm-7', 'col-sm-6', 'col-sm-5', 'col-md-4', 'col-md-3', 'w-20',
    'col-lg-2', 'w-14', 'w-12', 'w-11', 'w-10', 'w-9', 'col-xl-1',
)
ROW_SORT_MODES = (
    'width-biggest', 'width-smallest', 'text-longest', 'text-shortest',
)


def sort_row_choices(project: dict[str, Any], row_id: str, mode: str) -> list[str]:
    """Mirror the Creator Row Settings ``sortObjects`` action.

    The upstream labels say "biggest"/"smallest" but the implementation sorts
    by the literal index in ``objectWidths``.  This function follows that code,
    not a re-interpretation of the labels.
    """
    if mode not in ROW_SORT_MODES:
        raise ValueError(f'unknown row sort mode: {mode}; expected one of {", ".join(ROW_SORT_MODES)}')
    idx = ProjectIndex(project)
    row = idx.one(row_id, 'row') or idx.one(row_id, 'backpack_row')
    if row is None:
        raise ValueError(f'row not found: {row_id}')
    objects = row.value.get('objects')
    if not isinstance(objects, list):
        raise ValueError(f'row {row_id} objects must be an array')
    width_index = {value: i for i, value in enumerate(OBJECT_WIDTH_ORDER)}
    fallback = len(OBJECT_WIDTH_ORDER)
    if mode == 'width-biggest':
        objects.sort(key=lambda c: width_index.get(c.get('objectWidth') if isinstance(c, dict) else None, fallback), reverse=True)
    elif mode == 'width-smallest':
        objects.sort(key=lambda c: width_index.get(c.get('objectWidth') if isinstance(c, dict) else None, fallback))
    elif mode == 'text-longest':
        objects.sort(key=lambda c: js_string_length(c.get('text') if isinstance(c, dict) else ''), reverse=True)
    else:
        objects.sort(key=lambda c: js_string_length(c.get('text') if isinstance(c, dict) else ''))
    for i, choice in enumerate(objects):
        if isinstance(choice, dict):
            choice['index'] = i
    return [str(c.get('id', '')) for c in objects if isinstance(c, dict)]


_RADIUS_COMPAT_FIELDS = {
    f'{prefix}BorderRadius{side}'
    for prefix in ('addon', 'addonImg', 'object', 'objectImg', 'row', 'rowImg')
    for side in ('TopLeft', 'TopRight', 'BottomLeft', 'BottomRight')
}
_COLOR_COMPAT_FIELDS = {
    'selFilterBgColor', 'selFilterBorderColor', 'selFilterCTitleColor',
    'selFilterCTextColor', 'selFilterATitleColor', 'selFilterATextColor',
    'selFilterSTextColor', 'reqFilterBgColor', 'reqFilterBorderColor',
    'reqFilterCTitleColor', 'reqFilterCTextColor', 'reqFilterATitleColor',
    'reqFilterATextColor', 'reqFilterSTextColor', 'rowTitleColor', 'rowTextColor',
    'objectTitleColor', 'objectTextColor', 'addonTitleColor', 'addonTextColor',
    'scoreTextColor', 'objectImgBorderColor', 'rowImgBorderColor',
    'addonImgBorderColor', 'backgroundColor', 'rowBgColor', 'objectBgColor',
    'objectDropShadowColor', 'objectBorderColor', 'rowDropShadowColor',
    'rowBorderColor', 'addonDropShadowColor', 'addonBorderColor', 'addonBgColor',
    'barTextColor', 'barIconColor', 'barBackgroundColor', 'backpackBgColor',
    'barPointNeg', 'barPointPos',
}
_ROW_IMPORT_REMOVE = set(STYLE_FIELD_GROUPS['point_bar']) | set(STYLE_FIELD_GROUPS['backpack']) | {
    'bgColorIsOn', 'backgroundColor', 'isBackgroundRepeat', 'isBackgroundFitIn', 'backgroundImage',
}
_CHOICE_IMPORT_REMOVE = _ROW_IMPORT_REMOVE | set(STYLE_FIELD_GROUPS['row']) | set(STYLE_FIELD_GROUPS['row_image']) | {
    'rowBgColorIsOn', 'rowBgColor', 'isRowBackgroundRepeat', 'isRowBackgroundFitIn', 'rowBackgroundImage',
}


def _creator_coerce_styling(styling: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Apply the numeric coercions in the pinned Creator's StylingSchema."""
    out = deepcopy(styling)
    coerced: list[str] = []
    for key, value in list(out.items()):
        if FIELD_TYPE_CODES['styling'].get(key) != 'n' or not isinstance(value, str):
            continue
        text = value.strip()
        if not text:
            continue
        try:
            number = float(text)
        except ValueError:
            continue
        out[key] = int(number) if number.is_integer() else number
        coerced.append(key)
    return out, coerced


def prepare_design_import(value: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    """Parse a Creator design file and mirror ``StylingSchema``/``initStyling`` compatibility work."""
    if not isinstance(value, dict):
        raise ValueError('design JSON must be an object')
    version = value.get('version')
    raw = value.get('styling') if isinstance(value.get('styling'), dict) else value
    if not isinstance(raw, dict):
        raise ValueError('design styling must be an object')
    styling, coerced = _creator_coerce_styling(raw)
    old_version = version is None or version == '2.0.0-beta'
    if old_version:
        for key in _RADIUS_COMPAT_FIELDS:
            if key in styling and isinstance(styling[key], (int, float)) and not isinstance(styling[key], bool):
                styling[key] *= 10
    color_objects: list[str] = []
    for key in _COLOR_COMPAT_FIELDS:
        value = styling.get(key)
        if isinstance(value, dict) and isinstance(value.get('hexa'), str):
            styling[key] = value['hexa']
            color_objects.append(key)
    validate_known_values('styling', styling)
    return styling, {
        'source_version': version,
        'legacy_radius_scale': old_version,
        'numeric_coercions': sorted(coerced),
        'color_object_conversions': sorted(color_objects),
    }


def _private_switches(styling: dict[str, Any], *, choice: bool) -> dict[str, bool]:
    groups = {
        'privateFilterIsOn': 'filter',
        'privateTextIsOn': 'text',
        'privateObjectImageIsOn': 'object_image',
        'privateAddonImageIsOn': 'addon_image',
        'privateBackgroundIsOn': 'background',
        'privateObjectIsOn': 'object',
        'privateAddonIsOn': 'addon',
        'privateMultiChoiceIsOn': 'multi_choice',
    }
    if not choice:
        groups.update({'privateRowImageIsOn': 'row_image', 'privateRowIsOn': 'row'})
    return {
        switch: any(key in styling for key in STYLE_FIELD_GROUPS[group])
        for switch, group in groups.items()
    }


def import_design(project: dict[str, Any], target: str, value: Any) -> dict[str, Any]:
    """Import a global, Row, or Choice design like the pinned Creator dialogs."""
    styling, info = prepare_design_import(value)
    removed: list[str] = []
    if target == 'global':
        project['styling'] = styling
        return {**info, 'target': 'global', 'removed_fields': removed, 'field_count': len(styling)}

    idx = ProjectIndex(project)
    ent = idx.one(target)
    supported = {'row', 'backpack_row', 'choice', 'row_design_group', 'choice_design_group'}
    if ent is None or ent.kind not in supported:
        raise ValueError('design target must be global, a Row/Choice ID, or a Row/Choice Design Group ID')
    is_choice_scope = ent.kind in {'choice', 'choice_design_group'}
    illegal = _CHOICE_IMPORT_REMOVE if is_choice_scope else _ROW_IMPORT_REMOVE
    for key in list(styling):
        if key in illegal:
            styling.pop(key, None)
            removed.append(key)
    if ent.kind in {'row', 'backpack_row', 'choice'}:
        ent.value['isPrivateStyling'] = True
    ent.value['styling'] = styling
    switches = _private_switches(styling, choice=is_choice_scope)
    for key, enabled in switches.items():
        ent.value[key] = enabled
    return {
        **info,
        'target': ent.id,
        'kind': ent.kind,
        'removed_fields': sorted(removed),
        'private_switches': switches,
        'field_count': len(styling),
    }


def export_design(project: dict[str, Any], target: str) -> dict[str, Any]:
    """Return the exact design-file shape used by the Creator export buttons."""
    if target == 'global':
        styling = project.get('styling')
    else:
        idx = ProjectIndex(project)
        ent = idx.one(target)
        if ent is None or ent.kind not in {'row', 'backpack_row', 'choice', 'row_design_group', 'choice_design_group'}:
            raise ValueError('design target must be global, a Row/Choice ID, or a Row/Choice Design Group ID')
        styling = ent.value.get('styling')
    if not isinstance(styling, dict):
        raise ValueError(f'design target {target!r} has no styling object')
    return {'version': ICCPLUS_VERSION, 'styling': deepcopy(styling)}


class _BrowserTextContent(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def browser_text_content(value: Any) -> str:
    """Small DOM ``textContent`` equivalent for Creator text utilities."""
    parser = _BrowserTextContent()
    parser.feed(str(value or ''))
    parser.close()
    return ''.join(parser.parts)


def creator_id_csv(project: dict[str, Any]) -> str:
    """Mirror AppIdSearch.svelte CSV export, including BOM and blank Row separators."""
    def escape(value: Any) -> str:
        if value is None or value == '':
            return ''
        result = str(value)
        if result[0] in '=+-@':
            result = "'" + result
        result = result.replace('"', '""')
        if any(ch in result for ch in ('"', ',', '\n', '\r', '\t')) or result[:1].isspace() or result[-1:].isspace():
            result = f'"{result}"'
        return result

    fields = ('id', 'title', 'debugTitle')
    lines = [','.join(fields)]
    # The pinned Creator intentionally exports only app.rows here, not backpack rows.
    for row in project.get('rows', []):
        if not isinstance(row, dict):
            continue
        lines.append(','.join(escape(row.get(k)) for k in fields))
        for choice in row.get('objects', []):
            if isinstance(choice, dict):
                lines.append(','.join(escape(choice.get(k)) for k in fields))
        lines.append('')
    return '\ufeff' + '\n'.join(lines)


def ids_from_titles(project: dict[str, Any]) -> dict[str, Any]:
    """Perform Creator "Change Ids to titles" with reference-aware renames.

    ICC Plus changes its in-memory maps but does not rewrite authored references.
    This scripting equivalent keeps the same title-to-ID conversion and ``_dup``
    collision rule, then uses ProjectEditor.rename so requirements/effects remain valid.
    """
    editor = ProjectEditor(project)
    changed: list[dict[str, str]] = []
    skipped: list[dict[str, str]] = []

    def unique(desired: str, old: str) -> str:
        candidate = desired
        while True:
            hits = [ent for ent in ProjectIndex(project).find(candidate) if ent.kind != 'requirement']
            if not hits or (len(hits) == 1 and hits[0].id == old):
                return candidate
            candidate += '_dup'

    def rename_entity(value: dict[str, Any], default_title: Any) -> None:
        old = str(value.get('id', ''))
        title = value.get('title', '')
        if len(old) <= 2 or title == default_title:
            return
        desired = browser_text_content(str(title).replace(' ', '_').replace(',', '_'))
        if not desired:
            skipped.append({'id': old, 'reason': 'title becomes an empty ID'})
            return
        new = unique(desired, old)
        if new == old:
            return
        editor.rename(old, new, normalize=False)
        changed.append({'old': old, 'new': new})

    for collection in ('rows', 'backpack'):
        for row in list(project.get(collection, [])):
            if not isinstance(row, dict):
                continue
            rename_entity(row, project.get('defaultRowTitle'))
            for choice in list(row.get('objects', [])):
                if isinstance(choice, dict):
                    rename_entity(choice, project.get('defaultChoiceTitle'))
    editor.normalize_and_check()
    return {'changed': changed, 'changed_count': len(changed), 'skipped': skipped}


def font_inventory(project: dict[str, Any]) -> dict[str, list[str]]:
    return {
        'google': list(project.get('googleFonts', [])) if isinstance(project.get('googleFonts', []), list) else [],
        'urls': list(project.get('customFonts', [])) if isinstance(project.get('customFonts', []), list) else [],
    }


def update_font(project: dict[str, Any], source: str, value: str, *, remove: bool = False) -> dict[str, Any]:
    value = value.strip()
    if not value:
        raise ValueError('font value must not be empty')
    if source not in {'google', 'url'}:
        raise ValueError('font source must be google or url')
    field = 'googleFonts' if source == 'google' else 'customFonts'
    items = project.setdefault(field, [])
    if not isinstance(items, list):
        raise ValueError(f'{field} must be an array')
    before = list(items)
    if remove:
        items[:] = [x for x in items if x != value]
    elif value not in items:
        items.append(value)
    return {'source': source, 'value': value, 'remove': remove, 'changed': before != items, 'fonts': list(items)}
