from __future__ import annotations

"""Viewer-safe sparse serialization for the pinned ICC Plus runtime.

This module is deliberately separate from Creator-complete hydration. Creator
construction defaults and Viewer omission semantics are not the same thing.
Only omission rules proven against the pinned Viewer are applied here.
"""

import argparse
import copy
import json
from collections import Counter
from pathlib import Path
from typing import Any

from .validation import validate_complete
from .upstream_2106 import DEFAULT_APP, ICCPLUS_COMMIT, ICCPLUS_VERSION, json_stringify


# Fields the pinned Viewer removes during load. Their stored value is therefore
# not part of runtime project semantics.
RUNTIME_DISCARDED_TOP_LEVEL = frozenset({
    'autoSaveInterval',
    'bgmFadeInterval',
    'bgmFadeTimer',
    'bgmIsPlaying',
    'bgmObjectId',
    'bgmPlayInterval',
    'bgmTitle',
    'bgmTitleInterval',
    'cancelForcedActivated',
    'comp',
    'compG',
    'compODG',
    'compR',
    'compRDG',
    'curBgmTime',
    'curBgmLength',
    'isSeeking',
    'isFadingOut',
    'lastFadeTime',
    'objectMap',
    'pointTypeMap',
    'wordMap',
})

# When a custom global styling object must remain, these are the only individual
# built-in members currently proven safe to omit.
RETAINED_STYLING_DEFAULTS: dict[str, Any] = {
    'customMultiTextFont': False,
    'multiChoiceCounterPosition': 0,
    'multiChoiceCounterSize': 170,
    'multiChoiceTextFont': 'Times New Roman',
    'multiChoiceTextSize': 100,
}

DESIGN_GROUP_DEFAULTS: dict[str, Any] = {
    'activatedId': '',
    'elements': [],
    'backpackElements': [],
    'groupElements': [],
}

_SPECIAL_TOP_LEVEL = frozenset({'version', 'viewerConfig', 'styling', 'backpack'})
_MISSING = object()


def _record_remove(
    obj: dict[str, Any],
    key: str,
    *,
    path: str,
    rule: str,
    removals: list[dict[str, str]],
) -> bool:
    if key not in obj:
        return False
    del obj[key]
    removals.append({'path': path, 'rule': rule})
    return True


def _strip_null_object_members(value: Any, path: str, removals: list[dict[str, str]]) -> None:
    """Mirror the proven object-property part of the Viewer's removeNulls pass.

    We intentionally do not rewrite list membership here. PR #7 found evidence
    that null/empty-object list entries can also be filtered, but this serializer
    keeps the narrower rule until list filtering is pinned with equally explicit
    source/Viewer coverage.
    """
    if isinstance(value, dict):
        for key in list(value):
            child_path = f'{path}/{key}' if path else f'/{key}'
            if value[key] is None:
                _record_remove(value, key, path=child_path, rule='viewer_remove_null_object_member', removals=removals)
            else:
                _strip_null_object_members(value[key], child_path, removals)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _strip_null_object_members(item, f'{path}/{index}', removals)


def _strip_design_groups(groups: Any, path: str, removals: list[dict[str, str]]) -> None:
    if not isinstance(groups, list):
        return
    for index, group in enumerate(groups):
        if not isinstance(group, dict):
            continue
        base = f'{path}/{index}'
        for key, default in DESIGN_GROUP_DEFAULTS.items():
            if group.get(key, _MISSING) == default:
                _record_remove(group, key, path=f'{base}/{key}', rule='design_group_loader_default', removals=removals)


def _strip_addon(addon: Any, path: str, removals: list[dict[str, str]]) -> None:
    if not isinstance(addon, dict):
        return
    if addon.get('template', _MISSING) == 1:
        _record_remove(addon, 'template', path=f'{path}/template', rule='addon_template_one', removals=removals)
    if 'parentId' in addon:
        _record_remove(addon, 'parentId', path=f'{path}/parentId', rule='addon_parent_derived_from_container', removals=removals)
    if addon.get('requireds', _MISSING) == []:
        _record_remove(addon, 'requireds', path=f'{path}/requireds', rule='addon_requireds_empty_loader_default', removals=removals)


def _strip_choice(
    choice: Any,
    path: str,
    removals: list[dict[str, str]],
    *,
    inherited_addon_justify: Any,
) -> None:
    if not isinstance(choice, dict):
        return

    if 'index' in choice:
        _record_remove(choice, 'index', path=f'{path}/index', rule='choice_index_rebuilt_from_position', removals=removals)

    if (
        choice.get('isSelectableMultiple') is True
        and 'numMultipleTimesMinus' in choice
        and 'initMultipleTimesMinus' in choice
    ):
        derived = 0 if choice.get('forcedActivated') is True else choice.get('numMultipleTimesMinus')
        if choice.get('initMultipleTimesMinus') == derived:
            _record_remove(
                choice,
                'initMultipleTimesMinus',
                path=f'{path}/initMultipleTimesMinus',
                rule='choice_init_multiple_times_minus_derived',
                removals=removals,
            )

    if choice.get('addonJustify', _MISSING) == inherited_addon_justify:
        _record_remove(
            choice,
            'addonJustify',
            path=f'{path}/addonJustify',
            rule='choice_addon_justify_inherited',
            removals=removals,
        )

    addons = choice.get('addons')
    if isinstance(addons, list):
        for index, addon in enumerate(addons):
            _strip_addon(addon, f'{path}/addons/{index}', removals)


def _strip_row(
    row: Any,
    path: str,
    removals: list[dict[str, str]],
    *,
    backpack: bool,
    inherited_addon_justify: Any,
) -> None:
    if not isinstance(row, dict):
        return
    if 'index' in row:
        _record_remove(row, 'index', path=f'{path}/index', rule='row_index_rebuilt_from_position', removals=removals)
    if backpack and row.get('isBackpack') is True:
        _record_remove(row, 'isBackpack', path=f'{path}/isBackpack', rule='backpack_row_flag_forced_true', removals=removals)

    objects = row.get('objects')
    if isinstance(objects, list):
        for index, choice in enumerate(objects):
            _strip_choice(
                choice,
                f'{path}/objects/{index}',
                removals,
                inherited_addon_justify=inherited_addon_justify,
            )


def sparsify_project(
    project: dict[str, Any],
    *,
    require_complete: bool = True,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return a separate Viewer-safe sparse project and an omission receipt.

    The source object is never mutated. By default the input must already be a
    Creator-complete ICC Plus 2.10.7 project; this prevents sparse serialization
    from silently using Creator hydration to invent semantics for an incomplete
    source artifact.
    """
    if not isinstance(project, dict):
        raise ValueError('ICC Plus project JSON must be an object')
    if project.get('version') != ICCPLUS_VERSION:
        raise ValueError(
            f'sparse omission rules are pinned to ICC Plus {ICCPLUS_VERSION} '
            f'({ICCPLUS_COMMIT}); found version {project.get("version")!r}'
        )

    source_validation = None
    if require_complete:
        source_validation = validate_complete(project)
        if source_validation.get('valid') is not True:
            raise ValueError(
                'sparse serialization requires a Creator-complete source project; '
                'validate or explicitly repair the authoring artifact before creating a sparse release artifact'
            )

    source_text = json_stringify(project)
    sparse = copy.deepcopy(project)
    removals: list[dict[str, str]] = []

    # Capture inheritance before top-level defaults are removed from the sparse
    # copy. Missing project default falls back to the pinned Viewer's "start".
    inherited_addon_justify = project.get('defaultAddonJustify', 'start')

    for key in sorted(RUNTIME_DISCARDED_TOP_LEVEL):
        if key in sparse:
            _record_remove(
                sparse,
                key,
                path=f'/{key}',
                rule='viewer_discards_top_level_runtime_field',
                removals=removals,
            )

    # Ordinary top-level values are omitted only on exact equality with the
    # pinned Viewer's built-in defaultApp. Special whole objects are handled
    # separately; version is never omitted because migration reads it first.
    for key, default in DEFAULT_APP.items():
        if key in _SPECIAL_TOP_LEVEL or key in RUNTIME_DISCARDED_TOP_LEVEL:
            continue
        if sparse.get(key, _MISSING) == default:
            _record_remove(
                sparse,
                key,
                path=f'/{key}',
                rule='top_level_exact_default_app_value',
                removals=removals,
            )

    for key in ('viewerConfig', 'styling', 'backpack'):
        if sparse.get(key, _MISSING) == DEFAULT_APP.get(key, _MISSING):
            _record_remove(
                sparse,
                key,
                path=f'/{key}',
                rule=f'{key}_whole_object_exact_builtin',
                removals=removals,
            )

    styling = sparse.get('styling')
    if isinstance(styling, dict):
        for key, default in RETAINED_STYLING_DEFAULTS.items():
            if styling.get(key, _MISSING) == default:
                _record_remove(
                    styling,
                    key,
                    path=f'/styling/{key}',
                    rule='retained_styling_explicit_loader_default',
                    removals=removals,
                )

    rows = sparse.get('rows')
    if isinstance(rows, list):
        for index, row in enumerate(rows):
            _strip_row(
                row,
                f'/rows/{index}',
                removals,
                backpack=False,
                inherited_addon_justify=inherited_addon_justify,
            )

    backpack_rows = sparse.get('backpack')
    if isinstance(backpack_rows, list):
        for index, row in enumerate(backpack_rows):
            _strip_row(
                row,
                f'/backpack/{index}',
                removals,
                backpack=True,
                inherited_addon_justify=inherited_addon_justify,
            )

    point_types = sparse.get('pointTypes')
    if isinstance(point_types, list):
        for index, point in enumerate(point_types):
            if not isinstance(point, dict):
                continue
            if 'initValue' in point and point.get('initValue') == point.get('startingSum'):
                _record_remove(
                    point,
                    'initValue',
                    path=f'/pointTypes/{index}/initValue',
                    rule='point_init_value_equals_starting_sum',
                    removals=removals,
                )

    words = sparse.get('words')
    if isinstance(words, list):
        for index, word in enumerate(words):
            if isinstance(word, dict) and word.get('replaceText', _MISSING) == '':
                _record_remove(
                    word,
                    'replaceText',
                    path=f'/words/{index}/replaceText',
                    rule='word_empty_replace_text_loader_default',
                    removals=removals,
                )

    _strip_design_groups(sparse.get('rowDesignGroups'), '/rowDesignGroups', removals)
    _strip_design_groups(sparse.get('objectDesignGroups'), '/objectDesignGroups', removals)

    _strip_null_object_members(sparse, '', removals)

    sparse_text = json_stringify(sparse)
    by_rule = dict(sorted(Counter(item['rule'] for item in removals).items()))
    report: dict[str, Any] = {
        'target': {
            'icc_plus_version': ICCPLUS_VERSION,
            'source_commit': ICCPLUS_COMMIT,
        },
        'source_complete': source_validation.get('valid') if source_validation is not None else None,
        'source_bytes': len(source_text.encode('utf-8')),
        'sparse_bytes': len(sparse_text.encode('utf-8')),
        'bytes_removed': len(source_text.encode('utf-8')) - len(sparse_text.encode('utf-8')),
        'removed_count': len(removals),
        'removed_by_rule': by_rule,
        'removals': removals,
        'private_style_inference_applied': False,
        'array_null_filtering_applied': False,
        'browser_verification_required': True,
    }
    return sparse, report


def _load_project(path: str) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise ValueError('project JSON must be an object')
    return value


def main(argv: list[str] | None = None) -> int:
    """Compiler/release-facing command for writing a separate sparse artifact."""
    parser = argparse.ArgumentParser(
        prog='iccplus-sparse',
        description='Write a Viewer-safe sparse ICC Plus 2.10.7 release project without modifying the authoring project.',
    )
    parser.add_argument('project')
    parser.add_argument('-o', '--output', required=True)
    parser.add_argument('--pretty', action='store_true', help='Pretty-print the sparse project instead of release-compact JSON.')
    parser.add_argument('--dry-run', action='store_true', help='Calculate omissions without writing the sparse project.')
    args = parser.parse_args(argv)

    try:
        project = _load_project(args.project)
        sparse, report = sparsify_project(project, require_complete=True)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({'ok': False, 'error': str(exc)}, ensure_ascii=False))
        return 2

    written = None
    if not args.dry_run:
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(sparse, indent=2, ensure_ascii=False) + '\n' if args.pretty else json_stringify(sparse)
        target.write_text(text, encoding='utf-8')
        written = str(target)

    print(json.dumps({'ok': True, 'written': written, 'dry_run': bool(args.dry_run), **report}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
