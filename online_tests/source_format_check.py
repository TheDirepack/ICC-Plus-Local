from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from iccplus_tools.field_catalog import FIELD_CATALOG, STYLE_FIELD_GROUPS
from iccplus_tools.field_types import required_fields

TYPE_FILE = Path('ICCPlus/src/lib/store/types.ts')

# Local catalog kind -> one or more upstream TS types whose fields make up the shape.
TYPE_MAP: dict[str, tuple[str, ...]] = {
    'project': ('App',),
    'requirement': ('Requireds',),
    'score': ('Score',),
    'choice': ('Choice',),
    'row': ('Row',),
    'backpack_row': ('Row',),
    'addon': ('NonSelectableAddon',),
    'selectable_addon': ('SelectableAddon',),
    'point': ('PointType',),
    'variable': ('Variable',),
    'word': ('Word',),
    'group': ('Group',),
    'global_requirement': ('GlobalRequirement',),
    'row_design_group': ('RowDesignGroup',),
    'choice_design_group': ('ObjectDesignGroup',),
    'viewer_config': ('ViewerConfig',),
    'sound_effect': ('SoundEffect',),
    'category': ('Category',),
}

STYLE_TYPES = {
    'filter': 'filterStyling',
    'text': 'textStyling',
    'object_image': 'objectImageStyling',
    'row_image': 'rowImageStyling',
    'addon_image': 'addonImageStyling',
    'background': 'backgroundStyling',
    'object': 'objectStyling',
    'row': 'rowStyling',
    'addon': 'addonStyling',
    'multi_choice': 'multiChoiceStyling',
    'point_bar': 'pointBarStyling',
    'backpack': 'backpackStyling',
}


def _extract_type(text: str, name: str) -> tuple[set[str], list[str]]:
    marker = re.search(rf'export\s+type\s+{re.escape(name)}\s*=\s*', text)
    if not marker:
        raise ValueError(f'upstream type not found: {name}')
    start = text.find('{', marker.end())
    if start < 0:
        raise ValueError(f'upstream type has no object body: {name}')
    depth = 0
    quote: str | None = None
    escaped = False
    end = -1
    fields: set[str] = set()
    line_start = start + 1
    for i in range(start, len(text)):
        c = text[i]
        if quote:
            if escaped:
                escaped = False
            elif c == '\\':
                escaped = True
            elif c == quote:
                quote = None
            continue
        if c in "'\"`":
            quote = c
            continue
        if c == '{':
            if depth == 1:
                # A property whose value type is an inline object starts its
                # nested body before the line ends (e.g. templateStack?: { ... }[]).
                line = text[line_start:i].strip()
                m = re.match(r'([A-Za-z_$][\w$]*)\??\s*:', line)
                if m:
                    fields.add(m.group(1))
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                # Flush the final depth-1 line before ending.
                line = text[line_start:i].strip()
                m = re.match(r'([A-Za-z_$][\w$]*)\??\s*:', line)
                if m:
                    fields.add(m.group(1))
                end = i
                break
        elif c == '\n':
            if depth == 1:
                line = text[line_start:i].strip().rstrip(',;')
                m = re.match(r'([A-Za-z_$][\w$]*)\??\s*:', line)
                if m:
                    fields.add(m.group(1))
            line_start = i + 1
    if end < 0:
        raise ValueError(f'unbalanced upstream type: {name}')
    tail = text[end + 1:]
    inheritance = re.match(r'\s*((?:&\s*[A-Za-z_$][\w$]*\s*)*)', tail)
    trailer = inheritance.group(1) if inheritance else ''
    parents = re.findall(r'&\s*([A-Za-z_$][\w$]*)', trailer)
    return fields, parents


def _resolved_fields(text: str, name: str, cache: dict[str, set[str]], stack: set[str] | None = None) -> set[str]:
    if name in cache:
        return set(cache[name])
    stack = set(stack or ())
    if name in stack:
        raise ValueError(f'type inheritance cycle at {name}')
    stack.add(name)
    fields, parents = _extract_type(text, name)
    for parent in parents:
        fields |= _resolved_fields(text, parent, cache, stack)
    cache[name] = set(fields)
    return fields


def _extract_required(text: str, name: str) -> tuple[set[str], list[str]]:
    marker = re.search(rf'export\s+type\s+{re.escape(name)}\s*=\s*', text)
    if not marker:
        raise ValueError(f'upstream type not found: {name}')
    start = text.find('{', marker.end())
    if start < 0:
        raise ValueError(f'upstream type has no object body: {name}')
    depth = 0
    quote: str | None = None
    escaped = False
    end = -1
    required: set[str] = set()
    line_start = start + 1
    for i in range(start, len(text)):
        c = text[i]
        if quote:
            if escaped:
                escaped = False
            elif c == '\\':
                escaped = True
            elif c == quote:
                quote = None
            continue
        if c in "'\"`":
            quote = c
            continue
        if c == '{':
            if depth == 1:
                line = text[line_start:i].strip()
                m = re.match(r'([A-Za-z_$][\w$]*)(\?)?\s*:', line)
                if m and not m.group(2):
                    required.add(m.group(1))
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                line = text[line_start:i].strip()
                m = re.match(r'([A-Za-z_$][\w$]*)(\?)?\s*:', line)
                if m and not m.group(2):
                    required.add(m.group(1))
                end = i
                break
        elif c == '\n':
            if depth == 1:
                line = text[line_start:i].strip().rstrip(',;')
                m = re.match(r'([A-Za-z_$][\w$]*)(\?)?\s*:', line)
                if m and not m.group(2):
                    required.add(m.group(1))
            line_start = i + 1
    if end < 0:
        raise ValueError(f'unbalanced upstream type: {name}')
    tail = text[end + 1:]
    inheritance = re.match(r'\s*((?:&\s*[A-Za-z_$][\w$]*\s*)*)', tail)
    trailer = inheritance.group(1) if inheritance else ''
    parents = re.findall(r'&\s*([A-Za-z_$][\w$]*)', trailer)
    return required, parents


def _resolved_required(text: str, name: str, cache: dict[str, set[str]], stack: set[str] | None = None) -> set[str]:
    if name in cache:
        return set(cache[name])
    stack = set(stack or ())
    if name in stack:
        raise ValueError(f'type inheritance cycle at {name}')
    stack.add(name)
    fields, parents = _extract_required(text, name)
    for parent in parents:
        fields |= _resolved_required(text, parent, cache, stack)
    cache[name] = set(fields)
    return fields


def compare_type_catalog(repo_root: Path) -> list[str]:
    text = (repo_root / TYPE_FILE).read_text(encoding='utf-8')
    cache: dict[str, set[str]] = {}
    errors: list[str] = []
    for kind, type_names in TYPE_MAP.items():
        expected: set[str] = set()
        for name in type_names:
            expected |= _resolved_fields(text, name, cache)
        actual = set(FIELD_CATALOG[kind])
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        if missing or extra:
            errors.append(f'{kind}: missing={missing} extra={extra}')

    required_cache: dict[str, set[str]] = {}
    for kind, type_names in TYPE_MAP.items():
        expected_required: set[str] = set()
        for name in type_names:
            expected_required |= _resolved_required(text, name, required_cache)
        actual_required = set(required_fields(kind))
        missing = sorted(expected_required - actual_required)
        extra = sorted(actual_required - expected_required)
        if missing or extra:
            errors.append(f'{kind}/required: missing={missing} extra={extra}')

    for group, type_name in STYLE_TYPES.items():
        expected = _resolved_fields(text, type_name, cache)
        actual = set(STYLE_FIELD_GROUPS[group])
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        if missing or extra:
            errors.append(f'styling/{group}: missing={missing} extra={extra}')
        expected_required = _resolved_required(text, type_name, required_cache)
        if expected_required:
            errors.append(f'styling/{group}/required: unexpected required fields={sorted(expected_required)}')
    return errors
