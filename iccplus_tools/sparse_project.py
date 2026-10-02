from __future__ import annotations

"""Behavior-preserving runtime serialization for pinned ICC Plus 2.10.7.

Creator construction defaults and Viewer omission semantics are different
contracts. This module removes only values whose absence is proven equivalent
for the pinned Viewer, plus narrow conditional cases with the same result.
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

# These values belong to Creator authoring state or entity-construction defaults.
# The pinned standalone Viewer never consumes them. Keep Viewer-sensitive app
# defaults such as defaultChoiceMaxNum, defaultAddonJustify, requirement text
# ordering, cropperPosition, tooltipDelay, and display/runtime settings explicit.
CREATOR_ONLY_TOP_LEVEL = frozenset({
    'isEditModeOnAll',
    'tmpRow', 'tmpChoice', 'tmpRequired', 'tmpScore', 'tmpAddon', 'tmpGroup', 'tmpDesignGroup',
    'printThis',
    'autoSaveIsOn', 'buildAutoSaveIsOn', 'buildAutoSaveInterval',
    'checkDeleteRow', 'checkDeleteObject', 'checkSelectAll',
    'compressImageAuto', 'useTextEditor', 'useChoiceEditBtn', 'enableShortcut',
    'defaultRowTitle', 'defaultRowText',
    'defaultChoiceTitle', 'defaultChoiceText',
    'defaultBeforePoint', 'defaultAfterPoint',
    'defaultBeforeReq', 'defaultAfterReq',
    'defaultAddonTitle', 'defaultAddonText',
    'defaultRowTemplate', 'defaultRowWidth', 'defaultRowJustify', 'defaultRowAllowedChoices',
    'defaultChoiceTemplate', 'defaultChoiceWidth',
    'defaultAddonTemplate', 'defaultAddonWidth',
    'defaultUseSeperateAddon', 'defaultUseShowAddon', 'defaultUseHideAddon',
    'defaultUseShowScore', 'defaultUseHideValue', 'defaultUseShowReq',
})
ROW_CREATOR_ONLY_FIELDS = frozenset({'isEditModeOn', 'isSimpleEditMode', 'isRequirementOpen'})
CHOICE_CREATOR_ONLY_FIELDS = frozenset({'isEditModeOn'})
ADDON_CREATOR_ONLY_FIELDS = frozenset({'isEditModeOn'})
GROUP_CREATOR_ONLY_FIELDS = frozenset({'name'})
DESIGN_GROUP_CREATOR_ONLY_FIELDS = frozenset({'name'})
GLOBAL_REQUIREMENT_CREATOR_ONLY_FIELDS = frozenset({'name'})
SOUND_EFFECT_CREATOR_ONLY_FIELDS = frozenset({'name', 'isDefault', 'onSelected', 'onDeselected', 'groups'})

# These fields survive Creator/schema export but have no pinned Viewer read path.
ROW_VIEWER_UNUSED_FIELDS = frozenset({'imageIsUrl'})
CHOICE_VIEWER_UNUSED_FIELDS = frozenset({'selectedThisManyTimesProp'})
POINT_VIEWER_UNUSED_FIELDS = frozenset({'imageIsURL'})
SCORE_VIEWER_UNUSED_FIELDS = frozenset({'type'})

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

GROUP_DEFAULTS: dict[str, Any] = {
    'elements': [],
    'rowElements': [],
}

DESIGN_GROUP_DEFAULTS: dict[str, Any] = {
    'activatedId': '',
    'elements': [],
    'backpackElements': [],
    'groupElements': [],
}

CREATOR_CATEGORY_COLLECTIONS = (
    'pointTypes',
    'variables',
    'words',
    'groups',
    'globalRequirements',
    'rowDesignGroups',
    'objectDesignGroups',
)

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


def _strip_creator_only_fields(
    entity: Any,
    fields: frozenset[str],
    path: str,
    removals: list[dict[str, str]],
    *,
    rule: str = 'viewer_ignores_creator_edit_state',
) -> None:
    if not isinstance(entity, dict):
        return
    for key in fields:
        if key in entity:
            _remove(entity, key, f'{path}/{key}', rule, removals)


def _strip_viewer_unused_fields(
    entity: Any,
    fields: frozenset[str],
    path: str,
    removals: list[dict[str, str]],
) -> None:
    if not isinstance(entity, dict):
        return
    for key in fields:
        if key in entity:
            _remove(entity, key, f'{path}/{key}', 'viewer_ignores_entity_field', removals)


def _strip_creator_category_metadata(app: dict[str, Any], removals: list[dict[str, str]]) -> None:
    # Categories organize Creator dialogs only. The pinned Viewer store never
    # reads app.categories or an entity's category index.
    if 'categories' in app:
        _remove(app, 'categories', '/categories', 'viewer_ignores_creator_categories', removals)
    for collection_name in CREATOR_CATEGORY_COLLECTIONS:
        collection = app.get(collection_name)
        if not isinstance(collection, list):
            continue
        for index, entity in enumerate(collection):
            if isinstance(entity, dict) and 'category' in entity:
                _remove(
                    entity,
                    'category',
                    f'/{collection_name}/{index}/category',
                    'viewer_ignores_creator_category_metadata',
                    removals,
                )


def _strip_redundant_legacy_sfx_id(entity: Any, path: str, removals: list[dict[str, str]]) -> None:
    if not isinstance(entity, dict) or 'sfxId' not in entity:
        return
    # initializeApp only uses legacy sfxId to backfill a missing direction ID,
    # then unconditionally deletes sfxId. If every enabled direction already
    # has an explicit modern ID, the legacy source field cannot affect runtime.
    if entity.get('sfxOnSelect') and 'sfxIdOnSelect' not in entity:
        return
    if entity.get('sfxOnDeselect') and 'sfxIdOnDeselect' not in entity:
        return
    _remove(entity, 'sfxId', f'{path}/sfxId', 'legacy_sfx_id_redundant_after_explicit_direction_ids', removals)


def _strip_legacy_fade_transition(
    entity: Any,
    path: str,
    removals: list[dict[str, str]],
    *,
    loader_migrates: bool,
) -> None:
    """Remove old transition fields only when their loader effect is redundant."""
    if not isinstance(entity, dict):
        return
    has_flag = 'fadeTransitionIsOn' in entity
    has_time = 'fadeTransitionTime' in entity
    if not has_flag and not has_time:
        return

    if not loader_migrates:
        # The pinned Addon load path never consults these legacy fields; modern
        # selectable-Addon runtime behavior uses isFadeTransition and the
        # separate fadeIn/fadeOut times.
        if has_flag:
            _remove(entity, 'fadeTransitionIsOn', f'{path}/fadeTransitionIsOn', 'legacy_fade_transition_unused_on_addon', removals)
        if has_time:
            _remove(entity, 'fadeTransitionTime', f'{path}/fadeTransitionTime', 'legacy_fade_transition_unused_on_addon', removals)
        return

    legacy_enabled = entity.get('fadeTransitionIsOn') is True
    if not legacy_enabled or not has_time:
        # On Choices the loader only migrates when both conditions are true.
        # Outside that condition neither legacy member has a runtime read path.
        if has_flag:
            _remove(entity, 'fadeTransitionIsOn', f'{path}/fadeTransitionIsOn', 'legacy_fade_transition_no_loader_effect', removals)
        if has_time:
            _remove(entity, 'fadeTransitionTime', f'{path}/fadeTransitionTime', 'legacy_fade_transition_no_loader_effect', removals)
        return

    legacy_time = entity.get('fadeTransitionTime')
    if (
        entity.get('fadeInTransitionTime', _MISSING) == legacy_time
        and entity.get('fadeOutTransitionTime', _MISSING) == legacy_time
    ):
        _remove(entity, 'fadeTransitionIsOn', f'{path}/fadeTransitionIsOn', 'legacy_fade_transition_matches_modern_times', removals)
        _remove(entity, 'fadeTransitionTime', f'{path}/fadeTransitionTime', 'legacy_fade_transition_matches_modern_times', removals)


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
        _strip_creator_only_fields(
            group,
            DESIGN_GROUP_CREATOR_ONLY_FIELDS,
            base,
            removals,
            rule='viewer_ignores_creator_entity_metadata',
        )
        for key, default in DESIGN_GROUP_DEFAULTS.items():
            if group.get(key, _MISSING) == default:
                _remove(group, key, f'{base}/{key}', 'design_group_loader_default', removals)


def _strip_groups(groups: Any, path: str, removals: list[dict[str, str]]) -> None:
    if not isinstance(groups, list):
        return
    for index, group in enumerate(groups):
        if not isinstance(group, dict):
            continue
        base = f'{path}/{index}'
        _strip_creator_only_fields(
            group,
            GROUP_CREATOR_ONLY_FIELDS,
            base,
            removals,
            rule='viewer_ignores_creator_entity_metadata',
        )
        for key, default in GROUP_DEFAULTS.items():
            if group.get(key, _MISSING) == default:
                _remove(group, key, f'{base}/{key}', 'group_loader_default', removals)


def _strip_requirement_noise(requireds: Any, path: str, removals: list[dict[str, str]]) -> None:
    """Remove Requirement members with no pinned Viewer read path."""
    if not isinstance(requireds, list):
        return
    for index, req in enumerate(requireds):
        if not isinstance(req, dict):
            continue
        req_path = f'{path}/{index}'
        if 'id' in req:
            _remove(req, 'id', f'{req_path}/id', 'viewer_ignores_requirement_structural_id', removals)
        if req.get('more', _MISSING) == []:
            _remove(req, 'more', f'{req_path}/more', 'requirement_empty_more_is_noop', removals)
        _strip_requirement_noise(req.get('requireds'), f'{req_path}/requireds', removals)
        _strip_requirement_noise(req.get('orRequireds'), f'{req_path}/orRequireds', removals)


def _derived_legacy_or_requireds(req: Any) -> Any:
    """Return the exact orRequireds list initializeApp derives from legacy orRequired."""
    if not isinstance(req, dict) or req.get('type') != 'or':
        return _MISSING
    legacy = req.get('orRequired', _MISSING)
    if not isinstance(legacy, list):
        return _MISSING

    derived: list[dict[str, Any]] = []
    inherited = ('showRequired', 'operator', 'afterText', 'beforeText', 'orNum', 'selNum')
    for item in legacy:
        raw_req = item.get('req') if isinstance(item, dict) else None
        child: dict[str, Any] = {
            'required': True,
            'requireds': [],
            'orRequired': [],
            'orRequireds': [],
            'id': '',
            'type': 'id',
            'reqId': raw_req or '',
            'reqId1': '',
            'reqId2': '',
            'reqId3': '',
            'reqPoints': 0,
            'selFromOperators': '1',
            'more': [],
        }
        for key in inherited:
            if key in req:
                child[key] = copy.deepcopy(req[key])
        derived.append(child)
    return derived


def _strip_loader_migrated_or_requireds(requireds: Any, path: str, removals: list[dict[str, str]]) -> None:
    """Mirror the pinned loader's top-level + one-nested-level OR migration."""
    if not isinstance(requireds, list):
        return

    def strip_one(req: Any, req_path: str) -> None:
        if not isinstance(req, dict):
            return
        derived = _derived_legacy_or_requireds(req)
        if derived is not _MISSING and req.get('orRequireds', _MISSING) == derived:
            _remove(
                req,
                'orRequireds',
                f'{req_path}/orRequireds',
                'requirement_or_requireds_legacy_derived',
                removals,
            )

    for index, req in enumerate(requireds):
        req_path = f'{path}/{index}'
        strip_one(req, req_path)
        if isinstance(req, dict):
            nested = req.get('requireds')
            if isinstance(nested, list):
                for nested_index, nested_req in enumerate(nested):
                    strip_one(nested_req, f'{req_path}/requireds/{nested_index}')


def _strip_score(
    score: Any,
    path: str,
    removals: list[dict[str, str]],
    *,
    loader_migrates_or: bool,
) -> None:
    if not isinstance(score, dict):
        return
    # The Viewer assigns a fresh unique internal idx whenever it is absent and
    # no player behavior reads the serialized score idx afterward.
    if 'idx' in score:
        _remove(score, 'idx', f'{path}/idx', 'score_index_rebuilt_on_load', removals)
    _strip_viewer_unused_fields(score, SCORE_VIEWER_UNUSED_FIELDS, path, removals)
    if loader_migrates_or:
        _strip_loader_migrated_or_requireds(score.get('requireds'), f'{path}/requireds', removals)
    _strip_requirement_noise(score.get('requireds'), f'{path}/requireds', removals)


def _strip_addon(addon: Any, path: str, removals: list[dict[str, str]]) -> None:
    if not isinstance(addon, dict):
        return
    _strip_creator_only_fields(addon, ADDON_CREATOR_ONLY_FIELDS, path, removals)
    _strip_redundant_legacy_sfx_id(addon, path, removals)
    _strip_legacy_fade_transition(addon, path, removals, loader_migrates=False)
    # Pinned Viewer normalizes both missing and explicit 0 to template 1.
    if addon.get('template', _MISSING) in {0, 1}:
        _remove(addon, 'template', f'{path}/template', 'addon_template_normalizes_to_one', removals)
    if 'parentId' in addon:
        _remove(addon, 'parentId', f'{path}/parentId', 'addon_parent_derived_from_container', removals)
    if addon.get('skipIndex', _MISSING) is False:
        _remove(addon, 'skipIndex', f'{path}/skipIndex', 'addon_false_skip_index_is_missing_equivalent', removals)
    _strip_loader_migrated_or_requireds(addon.get('requireds'), f'{path}/requireds', removals)
    _strip_requirement_noise(addon.get('requireds'), f'{path}/requireds', removals)
    if addon.get('requireds', _MISSING) == []:
        _remove(addon, 'requireds', f'{path}/requireds', 'addon_requireds_empty_loader_default', removals)
    scores = addon.get('scores')
    if isinstance(scores, list):
        for index, score in enumerate(scores):
            _strip_score(score, f'{path}/scores/{index}', removals, loader_migrates_or=False)


def _strip_choice(
    choice: Any,
    path: str,
    removals: list[dict[str, str]],
    inherited_addon_justify: Any,
) -> None:
    if not isinstance(choice, dict):
        return
    _strip_creator_only_fields(choice, CHOICE_CREATOR_ONLY_FIELDS, path, removals)
    _strip_viewer_unused_fields(choice, CHOICE_VIEWER_UNUSED_FIELDS, path, removals)
    _strip_redundant_legacy_sfx_id(choice, path, removals)
    _strip_legacy_fade_transition(choice, path, removals, loader_migrates=True)
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

    _strip_loader_migrated_or_requireds(choice.get('requireds'), f'{path}/requireds', removals)
    _strip_requirement_noise(choice.get('requireds'), f'{path}/requireds', removals)
    scores = choice.get('scores')
    if isinstance(scores, list):
        for index, score in enumerate(scores):
            _strip_score(score, f'{path}/scores/{index}', removals, loader_migrates_or=True)

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
    _strip_creator_only_fields(row, ROW_CREATOR_ONLY_FIELDS, path, removals)
    _strip_viewer_unused_fields(row, ROW_VIEWER_UNUSED_FIELDS, path, removals)
    if 'index' in row:
        _remove(row, 'index', f'{path}/index', 'row_index_rebuilt_from_position', removals)
    if backpack and row.get('isBackpack') is True:
        _remove(row, 'isBackpack', f'{path}/isBackpack', 'backpack_row_flag_forced_true', removals)
    if row.get('width', _MISSING) is False:
        _remove(row, 'width', f'{path}/width', 'row_false_width_is_missing_equivalent', removals)
    _strip_loader_migrated_or_requireds(row.get('requireds'), f'{path}/requireds', removals)
    _strip_requirement_noise(row.get('requireds'), f'{path}/requireds', removals)
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
    """Return the default behavior-preserving runtime payload and omission receipt."""
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

    for key in sorted(CREATOR_ONLY_TOP_LEVEL):
        if key in sparse:
            _remove(sparse, key, f'/{key}', 'viewer_ignores_creator_edit_state', removals)

    for key, default in DEFAULT_APP.items():
        if key in _SPECIAL_TOP_LEVEL or key in RUNTIME_DISCARDED_TOP_LEVEL or key in CREATOR_ONLY_TOP_LEVEL:
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
            if not isinstance(point, dict):
                continue
            _strip_viewer_unused_fields(point, POINT_VIEWER_UNUSED_FIELDS, f'/pointTypes/{index}', removals)
            if 'initValue' in point and point.get('initValue') == point.get('startingSum'):
                _remove(point, 'initValue', f'/pointTypes/{index}/initValue', 'point_init_value_equals_starting_sum', removals)

    words = sparse.get('words')
    if isinstance(words, list):
        for index, word in enumerate(words):
            if isinstance(word, dict) and word.get('replaceText', _MISSING) == '':
                _remove(word, 'replaceText', f'/words/{index}/replaceText', 'word_empty_replace_text_loader_default', removals)

    global_requirements = sparse.get('globalRequirements')
    if isinstance(global_requirements, list):
        for index, global_requirement in enumerate(global_requirements):
            if isinstance(global_requirement, dict):
                base = f'/globalRequirements/{index}'
                _strip_creator_only_fields(
                    global_requirement,
                    GLOBAL_REQUIREMENT_CREATOR_ONLY_FIELDS,
                    base,
                    removals,
                    rule='viewer_ignores_creator_entity_metadata',
                )
                _strip_loader_migrated_or_requireds(
                    global_requirement.get('requireds'),
                    f'{base}/requireds',
                    removals,
                )
                _strip_requirement_noise(global_requirement.get('requireds'), f'{base}/requireds', removals)

    sound_effects = sparse.get('soundEffects')
    if isinstance(sound_effects, list):
        for index, sound_effect in enumerate(sound_effects):
            if not isinstance(sound_effect, dict):
                continue
            base = f'/soundEffects/{index}'
            _strip_creator_only_fields(
                sound_effect,
                SOUND_EFFECT_CREATOR_ONLY_FIELDS,
                base,
                removals,
                rule='viewer_ignores_creator_entity_metadata',
            )
            _strip_requirement_noise(sound_effect.get('requireds'), f'{base}/requireds', removals)

    _strip_creator_category_metadata(sparse, removals)
    _strip_groups(sparse.get('groups'), '/groups', removals)
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
        description='Write the default behavior-preserving ICC Plus 2.10.7 runtime project without modifying the authoring project.',
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
