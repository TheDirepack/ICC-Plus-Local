from __future__ import annotations

"""Official-project completeness and hydration helpers.

The canonical baseline is the blank project exported by the pinned ICC Plus
Creator. Hydration only fills missing project-level values from that baseline;
it never overwrites an existing value. Completeness validation then checks the
baseline sections plus the eager fields the official Creator writes when it
creates entities.
"""

import copy
from typing import Any

from .field_types import field_type_code, value_matches, expected_text
from .model import ProjectIndex
from .upstream_2106 import ICCPLUS_VERSION, default_export_project


ENTITY_REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
    'row': (
        'index', 'id', 'title', 'titleText', 'debugTitle', 'objectWidth',
        'image', 'template', 'isButtonRow', 'isResultRow', 'resultGroupId',
        'isInfoRow', 'defaultAspectWidth', 'defaultAspectHeight',
        'allowedChoices', 'currentChoices', 'rowJustify', 'requireds',
        'isEditModeOn', 'isRequirementOpen', 'objects', 'rowDesignGroups',
    ),
    'backpack_row': (
        'index', 'id', 'isBackpack', 'title', 'titleText', 'debugTitle',
        'objectWidth', 'image', 'template', 'isButtonRow', 'buttonType',
        'buttonId', 'buttonText', 'buttonRandom', 'buttonRandomNumber',
        'isResultRow', 'resultGroupId', 'isInfoRow', 'defaultAspectWidth',
        'defaultAspectHeight', 'allowedChoices', 'currentChoices', 'requireds',
        'isEditModeOn', 'isRequirementOpen', 'objects', 'rowDesignGroups',
    ),
    'choice': (
        'index', 'id', 'title', 'text', 'debugTitle', 'image', 'template',
        'objectWidth', 'isActive', 'multipleUseVariable',
        'initMultipleTimesMinus', 'selectedThisManyTimesProp', 'requireds',
        'addons', 'scores', 'groups', 'objectDesignGroups',
    ),
    'addon': (
        'id', 'title', 'text', 'template', 'addonWidth', 'image',
        'requireds', 'parentId',
    ),
    'selectable_addon': (
        'id', 'title', 'text', 'template', 'addonWidth', 'image',
        'requireds', 'parentId', 'isSelectable', 'scores',
    ),
    'score': (
        'idx', 'id', 'value', 'type', 'requireds', 'beforeText',
        'afterText', 'showScore',
    ),
    'requirement': (
        'required', 'requireds', 'orRequired', 'orRequireds', 'id', 'type',
        'reqId', 'reqId1', 'reqId2', 'reqId3', 'reqPoints', 'showRequired',
        'operator', 'afterText', 'beforeText', 'orNum', 'selNum',
        'selFromOperators', 'more',
    ),
    'point': (
        'id', 'name', 'startingSum', 'initValue', 'activatedId',
        'beforeText', 'afterText', 'category',
    ),
    'variable': ('id', 'isTrue', 'category'),
    'word': ('id', 'replaceText', 'category'),
    'group': ('id', 'name', 'category', 'elements', 'rowElements'),
    'global_requirement': ('id', 'name', 'category', 'requireds'),
    'row_design_group': (
        'id', 'name', 'activatedId', 'elements', 'backpackElements',
        'groupElements', 'styling', 'category',
    ),
    'choice_design_group': (
        'id', 'name', 'activatedId', 'elements', 'backpackElements',
        'groupElements', 'styling', 'category',
    ),
    'sound_effect': (
        'id', 'name', 'audio', 'volume', 'pitch', 'isDefault',
        'onSelected', 'onDeselected', 'requireds', 'groups',
    ),
    'category': ('idx', 'name', 'type'),
}


def _path(parent: str, key: str) -> str:
    return f'{parent}/{key}' if parent else f'/{key}'


def _expected_type_name(value: Any) -> str:
    if isinstance(value, bool):
        return 'boolean'
    if isinstance(value, str):
        return 'string'
    if isinstance(value, list):
        return 'array'
    if isinstance(value, dict):
        return 'object'
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return 'number'
    if value is None:
        return 'null'
    return type(value).__name__


def _same_wire_type(expected: Any, actual: Any) -> bool:
    if isinstance(expected, bool):
        return isinstance(actual, bool)
    if isinstance(expected, str):
        return isinstance(actual, str)
    if isinstance(expected, list):
        return isinstance(actual, list)
    if isinstance(expected, dict):
        return isinstance(actual, dict)
    if isinstance(expected, (int, float)) and not isinstance(expected, bool):
        return isinstance(actual, (int, float)) and not isinstance(actual, bool)
    if expected is None:
        return actual is None
    return isinstance(actual, type(expected))


def hydrate_project(project: dict[str, Any], *, upgrade_version: bool = False) -> list[dict[str, Any]]:
    """Fill missing official project-level fields in place.

    Existing values always win. Nested official objects (currently global
    styling and Viewer configuration) are filled recursively. Lists are treated
    atomically: an existing empty list is intentional, while a missing list gets
    the official Creator default.
    """
    if not isinstance(project, dict):
        raise ValueError('ICC Plus project JSON must be an object')

    baseline = default_export_project()
    changes: list[dict[str, Any]] = []

    def fill(target: dict[str, Any], defaults: dict[str, Any], parent: str = '') -> None:
        for key, default in defaults.items():
            p = _path(parent, key)
            if key not in target:
                target[key] = copy.deepcopy(default)
                changes.append({'path': p, 'action': 'filled', 'source': 'official_creator_default'})
                continue
            current = target[key]
            if isinstance(default, dict) and isinstance(current, dict):
                fill(current, default, p)

    fill(project, baseline)
    if upgrade_version and project.get('version') != ICCPLUS_VERSION:
        previous = project.get('version')
        project['version'] = ICCPLUS_VERSION
        changes.append({
            'path': '/version',
            'action': 'upgraded',
            'from': previous,
            'to': ICCPLUS_VERSION,
            'source': 'pinned_official_target',
        })
    return changes


def _baseline_issues(project: dict[str, Any]) -> list[dict[str, Any]]:
    baseline = default_export_project()
    issues: list[dict[str, Any]] = []

    def check(target: Any, defaults: dict[str, Any], parent: str = '') -> None:
        if not isinstance(target, dict):
            return
        for key, default in defaults.items():
            p = _path(parent, key)
            if key not in target:
                issues.append({
                    'code': 'complete.missing_field',
                    'path': p,
                    'message': f'Missing official Creator project field {key!r}.',
                    'suggestion': 'Hydrate the project from the official Creator defaults.',
                })
                continue
            current = target[key]
            if not _same_wire_type(default, current):
                issues.append({
                    'code': 'complete.wrong_type',
                    'path': p,
                    'message': f'{key} must be {_expected_type_name(default)}, got {_expected_type_name(current)}.',
                })
                continue
            if isinstance(default, dict):
                check(current, default, p)

    check(project, baseline)

    version = project.get('version')
    if version != ICCPLUS_VERSION:
        issues.append({
            'code': 'complete.target_version',
            'path': '/version',
            'message': f'Complete generated projects must target ICC Plus {ICCPLUS_VERSION}; found {version!r}.',
            'suggestion': f'Upgrade the project version to {ICCPLUS_VERSION} after verifying compatibility.',
        })
    return issues


def _known_type_issues(project: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []

    def check_mapping(kind: str, value: dict[str, Any], parent: str) -> None:
        for field, field_value in value.items():
            code = field_type_code(kind, field)
            if code is None or value_matches(code, field_value):
                continue
            issues.append({
                'code': 'complete.field_type',
                'path': _path(parent, field),
                'message': f'{kind}.{field} expects {expected_text(kind, field)}, got {type(field_value).__name__}.',
            })

    check_mapping('project', project, '')
    styling = project.get('styling')
    if isinstance(styling, dict):
        check_mapping('styling', styling, '/styling')
    viewer = project.get('viewerConfig')
    if isinstance(viewer, dict):
        check_mapping('viewer_config', viewer, '/viewerConfig')

    index = ProjectIndex(project)
    for ent in index.entities:
        if not isinstance(ent.value, dict):
            continue
        check_mapping(ent.kind, ent.value, ent.path)
    return issues


def _entity_shape_issues(project: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    index = ProjectIndex(project)
    for ent in index.entities:
        required = ENTITY_REQUIRED_FIELDS.get(ent.kind)
        if not required or not isinstance(ent.value, dict):
            continue
        for field in required:
            if field in ent.value:
                continue
            issues.append({
                'code': 'complete.entity_missing_field',
                'path': _path(ent.path, field),
                'entity_id': ent.id,
                'message': f'{ent.kind} is missing Creator-eager field {field!r}.',
                'suggestion': 'Recreate or repair this entity using the official Creator-shaped factory.',
            })
    return issues


def completeness_issues(project: Any) -> list[dict[str, Any]]:
    if not isinstance(project, dict):
        return [{
            'code': 'complete.not_object',
            'path': '',
            'message': 'ICC Plus project JSON must be an object.',
        }]
    return [
        *_baseline_issues(project),
        *_known_type_issues(project),
        *_entity_shape_issues(project),
    ]


def completeness_summary(project: Any) -> dict[str, Any]:
    issues = completeness_issues(project)
    return {
        'complete': not issues,
        'target_version': ICCPLUS_VERSION,
        'issue_count': len(issues),
        'issues': issues,
    }
