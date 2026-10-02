from __future__ import annotations

"""Behavior-preserving sparse project serialization for pinned ICC Plus 2.10.7.

Creator construction defaults and Viewer omission semantics are different
contracts. This module removes only values whose absence is proven equivalent
for the pinned Viewer, plus narrow conditional cases with the same result. The
same serializer is used by normal saved project JSON and Viewer packaging.
"""

import argparse
import copy
import json
from collections import Counter
from pathlib import Path
from typing import Any

from .upstream_2106 import DEFAULT_APP, ICCPLUS_COMMIT, ICCPLUS_VERSION, json_stringify
from .validation import validate_complete

RUNTIME_DISCARDED_TOP_LEVEL = frozenset({
    'autoSaveInterval', 'bgmFadeInterval', 'bgmFadeTimer', 'bgmIsPlaying',
    'bgmObjectId', 'bgmPlayInterval', 'bgmTitle', 'bgmTitleInterval',
    'cancelForcedActivated', 'comp', 'compG', 'compODG', 'compR', 'compRDG',
    'curBgmTime', 'curBgmLength', 'isSeeking', 'isFadingOut', 'lastFadeTime',
    'objectMap', 'pointTypeMap', 'wordMap',
})

RETAINED_STYLING_DEFAULTS: dict[str, Any] = {
    'customMultiTextFont': False,
    'multiChoiceCounterPosition': 0,
    'multiChoiceCounterSize': 170,
    'multiChoiceTextFont': 'Times New Roman',
    'multiChoiceTextSize': 100,
}

# These are the private-filter loader defaults, not the global styling defaults.
# In particular, private unselFilterSatur reconstructs to 0 while global style
# uses 1, so an explicit private value of 1 must survive serialization.
PRIVATE_FILTER_DEFAULTS: dict[str, Any] = {
    'unselFilterBlurIsOn': False,
    'unselFilterBlur': 0,
    'unselFilterBrightIsOn': False,
    'unselFilterBright': 100,
    'unselFilterCont': 100,
    'unselFilterGrayIsOn': False,
    'unselFilterGray': 0,
    'unselFilterHueIsOn': False,
    'unselFilterHue': 0,
    'unselFilterInvertIsOn': False,
    'unselFilterInvert': 0,
    'unselFilterOpacIsOn': False,
    'unselFilterOpac': 100,
    'unselFilterSaturIsOn': False,
    'unselFilterSatur': 0,
    'unselFilterSepiaIsOn': False,
    'unselFilterSepia': 0,
}

DESIGN_GROUP_DEFAULTS: dict[str, Any] = {
    'activatedId': '',
    'elements': [],
    'backpackElements': [],
    'groupElements': [],
}

_SPECIAL_TOP_LEVEL = frozenset({'version', 'viewerConfig', 'styling', 'backpack'})
_MISSING = object()


def _remove(
    obj: dict[str, Any],
    key: str,
    path: str,
    rule: str,
    removals: list[dict[str, str]],
) -> None:
    if key in obj:
        del obj[key]
        removals.append({'path': path, 'rule': rule})


def _strip_null_object_members(value: Any, path: str, removals: list[dict[str, str]]) -> None:
    """Mirror only the proven object-property part of Viewer removeNulls()."""
    if isinstance(value, dict):
        for key in list(value):
            child = f'{path}/{key}' if path else f'/{key}'
            if value[key] is None:
                _remove(value, key, child, 'viewer_remove_null_object_member', removals)
            else:
                _strip_null_object_members(value[key], child, removals)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _strip_null_object_members(item, f'{path}/{index}', removals)


def _strip_private_filter_defaults(entity: Any, path: str, removals: list[dict[str, str]]) -> None:
    if not isinstance(entity, dict) or entity.get('privateFilterIsOn') is not True:
        return
    styling = entity.get('styling')
    if not isinstance(styling, dict):
        return
    for key, default in PRIVATE_FILTER_DEFAULTS.items():
        if styling.get(key, _MISSING) == default:
            _remove(styling, key, f'{path}/styling/{key}', 'private_filter_explicit_loader_default', removals)


def _strip_design_groups(groups: Any, path: str, removals: list[dict[str, str]]) -> None:
    if not isinstance(groups, list):
        return
    for index, group in enumerate(groups):
        if not isinstance(group, dict):
            continue
        base = f'{path}/{index}'
        for key, default in DESIGN_GROUP_DEFAULTS.items():
            if group.get(key, _MISSING) == default:
                _remove(group, key, f'{base}/{key}', 'design_group_loader_default', removals)
        _strip_private_filter_defaults(group, base, removals)


def _strip_addon(addon: Any, path: str, removals: list[dict[str, str]]) -> None:
    if not isinstance(addon, dict):
        return
    # Pinned Viewer normalizes both missing and explicit 0 to template 1.
    if addon.get('template', _MISSING) in {0, 1}:
        _remove(addon, 'template', f'{path}/template', 'addon_template_normalizes_to_one', removals)
    if 'parentId' in addon:
        _remove(addon, 'parentId', f'{path}/parentId', 'addon_parent_derived_from_container', removals)
    if addon.get('requireds', _MISSING) == []:
        _remove(addon, 'requireds', f'{path}/requireds', 'addon_requireds_empty_loader_default', removals)


def _strip_choice(
    choice: Any,
    path: str,
    removals: list[dict[str, str]],
    inherited_addon_justify: Any,
) -> None:
    if not isinstance(choice, dict):
        return
    if 'index' in choice:
        _remove(choice, 'index', f'{path}/index', 'choice_index_rebuilt_from_position', removals)

    if choice.get('isSelectableMultiple') is True and 'numMultipleTimesMinus' in choice and 'initMultipleTimesMinus' in choice:
        derived = 0 if choice.get('forcedActivated') is True else choice.get('numMultipleTimesMinus')
        if choice.get('initMultipleTimesMinus') == derived:
            _remove(
                choice,
                'initMultipleTimesMinus',
                f'{path}/initMultipleTimesMinus',
                'choice_init_multiple_times_minus_derived',
                removals,
            )

    if choice.get('addonJustify', _MISSING) == inherited_addon_justify:
        _remove(choice, 'addonJustify', f'{path}/addonJustify', 'choice_addon_justify_inherited', removals)

    _strip_private_filter_defaults(choice, path, removals)
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
        _remove(row, 'index', f'{path}/index', 'row_index_rebuilt_from_position', removals)
    if backpack and row.get('isBackpack') is True:
        _remove(row, 'isBackpack', f'{path}/isBackpack', 'backpack_row_flag_forced_true', removals)
    _strip_private_filter_defaults(row, path, removals)

    objects = row.get('objects')
    if isinstance(objects, list):
        for index, choice in enumerate(objects):
            _strip_choice(choice, f'{path}/objects/{index}', removals, inherited_addon_justify)


def sparsify_project(
    project: dict[str, Any],
    *,
    require_complete: bool = True,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return the default behavior-preserving sparse project and omission receipt."""
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
    inherited_addon_justify = project.get('defaultAddonJustify', 'start')

    for key in sorted(RUNTIME_DISCARDED_TOP_LEVEL):
        if key in sparse:
            _remove(sparse, key, f'/{key}', 'viewer_discards_top_level_runtime_field', removals)

    for key, default in DEFAULT_APP.items():
        if key in _SPECIAL_TOP_LEVEL or key in RUNTIME_DISCARDED_TOP_LEVEL:
            continue
        if sparse.get(key, _MISSING) == default:
            _remove(sparse, key, f'/{key}', 'top_level_exact_default_app_value', removals)

    for key in ('viewerConfig', 'styling', 'backpack'):
        if sparse.get(key, _MISSING) == DEFAULT_APP.get(key, _MISSING):
            _remove(sparse, key, f'/{key}', f'{key}_whole_object_exact_builtin', removals)

    styling = sparse.get('styling')
    if isinstance(styling, dict):
        for key, default in RETAINED_STYLING_DEFAULTS.items():
            if styling.get(key, _MISSING) == default:
                _remove(styling, key, f'/styling/{key}', 'retained_styling_explicit_loader_default', removals)

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
            if isinstance(point, dict) and 'initValue' in point and point.get('initValue') == point.get('startingSum'):
                _remove(point, 'initValue', f'/pointTypes/{index}/initValue', 'point_init_value_equals_starting_sum', removals)

    words = sparse.get('words')
    if isinstance(words, list):
        for index, word in enumerate(words):
            if isinstance(word, dict) and word.get('replaceText', _MISSING) == '':
                _remove(word, 'replaceText', f'/words/{index}/replaceText', 'word_empty_replace_text_loader_default', removals)

    _strip_design_groups(sparse.get('rowDesignGroups'), '/rowDesignGroups', removals)
    _strip_design_groups(sparse.get('objectDesignGroups'), '/objectDesignGroups', removals)
    _strip_null_object_members(sparse, '', removals)

    sparse_text = json_stringify(sparse)
    by_rule = dict(sorted(Counter(item['rule'] for item in removals).items()))
    report: dict[str, Any] = {
        'target': {'icc_plus_version': ICCPLUS_VERSION, 'source_commit': ICCPLUS_COMMIT},
        'source_complete': source_validation.get('valid') if source_validation is not None else None,
        'source_bytes': len(source_text.encode('utf-8')),
        'sparse_bytes': len(sparse_text.encode('utf-8')),
        'bytes_removed': len(source_text.encode('utf-8')) - len(sparse_text.encode('utf-8')),
        'removed_count': len(removals),
        'removed_by_rule': by_rule,
        'removals': removals,
        'private_style_inference_applied': False,
        'array_null_filtering_applied': False,
        'browser_verification_required_for_unproven_rules': True,
    }
    return sparse, report


def runtime_project_text(project: dict[str, Any], *, require_complete: bool = True) -> tuple[str, dict[str, Any]]:
    """Serialize compact runtime JSON with every currently proven omission."""
    sparse, report = sparsify_project(project, require_complete=require_complete)
    return json_stringify(sparse), report


def _load_project(path: str) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise ValueError('project JSON must be an object')
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog='iccplus-sparse',
        description='Write the default behavior-preserving ICC Plus 2.10.7 sparse project without modifying the source project.',
    )
    parser.add_argument('project')
    parser.add_argument('-o', '--output', required=True)
    parser.add_argument('--pretty', action='store_true', help='Pretty-print instead of release-compact JSON.')
    parser.add_argument('--dry-run', action='store_true', help='Calculate omissions without writing the runtime project.')
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
