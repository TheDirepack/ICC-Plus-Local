from __future__ import annotations

from typing import Any

HIDE_CONTENT_TYPES = {
    'choice_title': '1', 'title': '1',
    'choice_image': '2', 'image': '2',
    'choice_text': '3', 'text': '3',
    'choice_score': '4', 'score': '4', 'scores': '4',
    'choice_requirement': '5', 'requirement': '5', 'requirements': '5',
    'addon_title': '6', 'addon_image': '7', 'addon_text': '8',
    'unselected_addon': '9', 'unmet_addon': '10',
}

DISCOUNT_OPERATORS = {
    # ICC Plus runtime calcStackDiscount uses 1=subtract and 2=add.
    # Human aliases follow the arithmetic effect, not the Creator's historical labels.
    '1': '1', '-': '1', 'minus': '1', 'subtract': '1',
    '2': '2', '+': '2', 'plus': '2', 'add': '2',
    '3': '3', '*': '3', 'x': '3', 'multiply': '3',
    '4': '4', '/': '4', 'divide': '4',
    '5': '5', '=': '5', 'set': '5', 'assign': '5', 'assignment': '5',
}

VARIABLE_MODES = {
    '1': '1', 'true': '1', 'selected': '1', 'mirror': '1',
    '2': '2', 'false': '2', 'inverse': '2', 'inverted': '2',
    '3': '3', 'toggle': '3',
}


def _list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _strings(value: Any, field: str) -> list[str]:
    out: list[str] = []
    for raw in _list(value):
        text = str(raw).strip()
        if text and text not in out:
            out.append(text)
    if not out and value not in (None, [], ''):
        raise ValueError(f'{field} must contain at least one non-empty ID')
    return out


def _set(values: dict[str, Any], key: str, value: Any, source: str) -> None:
    if key in values and values[key] != value:
        raise ValueError(f'{source} conflicts with explicit native field {key!r}')
    values[key] = value


def _effect_object(raw: Any) -> dict[str, Any]:
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ValueError('effects must be an object')
    return dict(raw)


def _hide_codes(contents: Any) -> list[str]:
    codes: list[str] = []
    for raw in _list(contents):
        key = str(raw).strip().lower().replace('-', '_').replace(' ', '_')
        code = HIDE_CONTENT_TYPES.get(key)
        if not code:
            raise ValueError(f'unknown hide_contents content type: {raw!r}')
        if code not in codes:
            codes.append(code)
    return codes


def _csv_ids(value: Any, field: str) -> str:
    return ','.join(_strings(value, field))


def _apply_activate(values: dict[str, Any], raw: Any, *, deactivate: bool = False) -> None:
    ids = _strings(raw, 'deactivate' if deactivate else 'activate')
    flag = 'deactivateOtherChoice' if deactivate else 'activateOtherChoice'
    target = 'deactivateThisChoice' if deactivate else 'activateThisChoice'
    _set(values, flag, bool(ids), 'effects.deactivate' if deactivate else 'effects.activate')
    _set(values, target, ','.join(ids), 'effects.deactivate' if deactivate else 'effects.activate')


def _apply_hide_contents(values: dict[str, Any], raw: Any) -> None:
    if not isinstance(raw, dict):
        raise ValueError('effects.hide_contents must be an object with rows and contents')
    rows = _strings(raw.get('rows', raw.get('row')), 'effects.hide_contents.rows')
    codes = _hide_codes(raw.get('contents', raw.get('content')))
    if not rows:
        raise ValueError('effects.hide_contents.rows is required')
    if not codes:
        raise ValueError('effects.hide_contents.contents is required')
    _set(values, 'isContentHidden', True, 'effects.hide_contents')
    _set(values, 'hiddenContentsRow', rows, 'effects.hide_contents')
    _set(values, 'hiddenContentsType', codes, 'effects.hide_contents')


def _apply_row_limit(values: dict[str, Any], raw: Any) -> None:
    if not isinstance(raw, dict):
        raise ValueError('effects.row_limit must be an object')
    rows = _strings(raw.get('rows', raw.get('row', raw.get('targets'))), 'effects.row_limit.rows')
    amount = raw.get('add', raw.get('amount', raw.get('value')))
    if not isinstance(amount, (int, float)) or isinstance(amount, bool):
        raise ValueError('effects.row_limit.add must be numeric')
    if not rows:
        raise ValueError('effects.row_limit.rows is required')
    _set(values, 'addToAllowChoice', True, 'effects.row_limit')
    _set(values, 'idOfAllowChoice', rows, 'effects.row_limit')
    _set(values, 'numbAddToAllowChoice', amount, 'effects.row_limit')


def _apply_variables(values: dict[str, Any], raw: Any) -> None:
    if isinstance(raw, (str, list)):
        raw = {'targets': raw, 'mode': 'true'}
    if not isinstance(raw, dict):
        raise ValueError('effects.variables must be an object, ID, or array of IDs')
    ids = _strings(raw.get('targets', raw.get('ids', raw.get('variables'))), 'effects.variables.targets')
    if not ids:
        raise ValueError('effects.variables.targets is required')
    mode_raw = str(raw.get('mode', 'true')).strip().lower()
    mode = VARIABLE_MODES.get(mode_raw)
    if mode is None:
        raise ValueError('effects.variables.mode must be true, false, toggle, selected, inverse, or 1/2/3')
    _set(values, 'isChangeVariables', True, 'effects.variables')
    _set(values, 'changedVariables', ids, 'effects.variables')
    _set(values, 'changeType', mode, 'effects.variables')


def _apply_point_transform(values: dict[str, Any], raw: Any, mode: str) -> None:
    if not isinstance(raw, dict):
        raise ValueError(f'effects.points.{mode} must be an object')
    ids = _strings(raw.get('targets', raw.get('points', raw.get('point'))), f'effects.points.{mode}.targets')
    if not ids:
        raise ValueError(f'effects.points.{mode}.targets is required')
    if mode == 'multiply':
        amount = raw.get('by', raw.get('value'))
        if not isinstance(amount, (int, float, str)) or isinstance(amount, bool):
            raise ValueError('effects.points.multiply.by must be a number or expression string')
        _set(values, 'multiplyPointtypeIsOn', True, 'effects.points.multiply')
        _set(values, 'pointTypeToMultiply', ids, 'effects.points.multiply')
        _set(values, 'multiplyWithThis', amount, 'effects.points.multiply')
        if raw.get('by_id') is True:
            _set(values, 'multiplyPointtypeIsId', True, 'effects.points.multiply')
    elif mode == 'divide':
        amount = raw.get('by', raw.get('value'))
        if not isinstance(amount, (int, float)) or isinstance(amount, bool):
            raise ValueError('effects.points.divide.by must be numeric')
        _set(values, 'dividePointtypeIsOn', True, 'effects.points.divide')
        _set(values, 'pointTypeToDivide', ids, 'effects.points.divide')
        _set(values, 'divideWithThis', amount, 'effects.points.divide')
    elif mode == 'set':
        amount = raw.get('to', raw.get('value'))
        if amount is None:
            raise ValueError('effects.points.set.to is required')
        _set(values, 'setPointtypeIsOn', True, 'effects.points.set')
        _set(values, 'pointTypeToSet', ids, 'effects.points.set')
        _set(values, 'setWithThis', str(amount), 'effects.points.set')


def _apply_points(values: dict[str, Any], raw: Any) -> None:
    if not isinstance(raw, dict):
        raise ValueError('effects.points must be an object')
    known = {'multiply', 'divide', 'set'}
    unknown = set(raw) - known
    if unknown:
        raise ValueError(f'unknown effects.points key(s): {", ".join(sorted(unknown))}')
    for mode in ('multiply', 'divide', 'set'):
        if mode in raw:
            _apply_point_transform(values, raw[mode], mode)


def _apply_word(values: dict[str, Any], raw: Any) -> None:
    if not isinstance(raw, dict):
        raise ValueError('effects.word must be an object')
    word_id = str(raw.get('id', raw.get('word', ''))).strip()
    if not word_id:
        raise ValueError('effects.word.id is required')
    _set(values, 'textfieldIsOn', True, 'effects.word')
    _set(values, 'idOfTheTextfieldWord', word_id, 'effects.word')
    if 'select' in raw or 'on_select' in raw:
        _set(values, 'wordChangeSelect', str(raw.get('on_select', raw.get('select', ''))), 'effects.word')
    if 'deselect' in raw or 'on_deselect' in raw:
        _set(values, 'wordChangeDeselect', str(raw.get('on_deselect', raw.get('deselect', ''))), 'effects.word')
    if 'prompt' in raw:
        _set(values, 'wordPromptText', str(raw['prompt']), 'effects.word')
        _set(values, 'customTextfieldIsOn', True, 'effects.word')


def _apply_multiple(values: dict[str, Any], raw: Any) -> None:
    if raw is True:
        raw = {}
    if not isinstance(raw, dict):
        raise ValueError('effects.multiple must be true or an object')
    _set(values, 'isSelectableMultiple', True, 'effects.multiple')
    _set(values, 'multipleUseVariable', int(raw.get('start', 0)), 'effects.multiple')
    # A normal semantic multiple counter uses the Creator's variable-backed
    # repeat mode. Point-backed mode is selected only when an explicit score
    # ID is supplied.
    if 'score' not in raw:
        _set(values, 'isMultipleUseVariable', True, 'effects.multiple')
    if 'max' in raw:
        maximum = raw['max']
        if not isinstance(maximum, int) or isinstance(maximum, bool) or maximum < 0:
            raise ValueError('effects.multiple.max must be a non-negative integer')
        _set(values, 'numMultipleTimesPluss', maximum, 'effects.multiple')
    if 'min' in raw:
        minimum = raw['min']
        if not isinstance(minimum, int) or isinstance(minimum, bool) or minimum < 0:
            raise ValueError('effects.multiple.min must be a non-negative integer')
        _set(values, 'numMultipleTimesMinus', minimum, 'effects.multiple')
    if 'click' in raw:
        _set(values, 'allowSelectByClick', bool(raw['click']), 'effects.multiple')
    if 'slider' in raw:
        _set(values, 'useSlider', bool(raw['slider']), 'effects.multiple')
    if 'hide_counter' in raw:
        _set(values, 'hideCounter', bool(raw['hide_counter']), 'effects.multiple')
    if 'hide_until_selected' in raw:
        _set(values, 'hideCounterUntilSelect', bool(raw['hide_until_selected']), 'effects.multiple')
    if 'score' in raw:
        _set(values, 'multipleScoreId', str(raw['score']), 'effects.multiple')


def _apply_discount(values: dict[str, Any], raw: Any) -> None:
    if not isinstance(raw, dict):
        raise ValueError('effects.discount must be an object')
    choices = _strings(raw.get('choices'), 'effects.discount.choices')
    rows = _strings(raw.get('rows'), 'effects.discount.rows')
    groups = _strings(raw.get('groups'), 'effects.discount.groups')
    points = _strings(raw.get('points', raw.get('point_types')), 'effects.discount.points')
    if not (choices or rows or groups):
        raise ValueError('effects.discount needs choices/rows or groups')
    operator_raw = str(raw.get('operator', 'subtract')).strip().lower()
    operator = DISCOUNT_OPERATORS.get(operator_raw)
    if operator is None:
        raise ValueError('effects.discount.operator must be add/subtract/multiply/divide/set or 1-5')
    amount = raw.get('value')
    if not isinstance(amount, (int, float)) or isinstance(amount, bool):
        raise ValueError('effects.discount.value must be numeric')
    _set(values, 'discountOther', True, 'effects.discount')
    _set(values, 'discountOperator', operator, 'effects.discount')
    _set(values, 'discountValue', amount, 'effects.discount')
    _set(values, 'discountPointTypes', points, 'effects.discount')
    if choices or rows:
        if groups:
            raise ValueError('effects.discount cannot combine groups with choices/rows; ICC Plus uses one targeting mode at a time')
        _set(values, 'isDisChoices', True, 'effects.discount')
        _set(values, 'discountChoices', choices, 'effects.discount')
        _set(values, 'discountRows', rows, 'effects.discount')
    else:
        _set(values, 'discountGroups', groups, 'effects.discount')
    for source_key, native in (
        ('stackable', 'stackableDiscount'), ('show', 'discountShow'),
        ('replace_text', 'replaceScoreText'), ('hide_value', 'hideScoreValue'),
        ('hide_icon', 'hideScoreIcon'), ('count_per_selection', 'countPerSelection'),
    ):
        if source_key in raw:
            _set(values, native, bool(raw[source_key]), 'effects.discount')
    if 'low_limit' in raw:
        limit = raw['low_limit']
        if not isinstance(limit, (int, float)) or isinstance(limit, bool):
            raise ValueError('effects.discount.low_limit must be numeric')
        _set(values, 'discountLowLimitIsOn', True, 'effects.discount')
        _set(values, 'discountLowLimit', limit, 'effects.discount')
    if 'count' in raw:
        count = raw['count']
        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
            raise ValueError('effects.discount.count must be a non-negative integer')
        _set(values, 'useDiscountCount', True, 'effects.discount')
        _set(values, 'discountCount', count, 'effects.discount')
    if 'before_text' in raw:
        _set(values, 'discountBeforeText', str(raw['before_text']), 'effects.discount')
    if 'after_text' in raw:
        _set(values, 'discountAfterText', str(raw['after_text']), 'effects.discount')


def _apply_random_activate(values: dict[str, Any], raw: Any) -> None:
    if isinstance(raw, (str, list)):
        raw = {'targets': raw, 'count': 1}
    if not isinstance(raw, dict):
        raise ValueError('effects.random_activate must be an object, ID, or array of IDs')
    ids = _strings(raw.get('targets', raw.get('choices')), 'effects.random_activate.targets')
    if not ids:
        raise ValueError('effects.random_activate.targets is required')
    count = raw.get('count', 1)
    if not isinstance(count, int) or isinstance(count, bool) or count < 1:
        raise ValueError('effects.random_activate.count must be a positive integer')
    _set(values, 'isActivateRandom', True, 'effects.random_activate')
    _set(values, 'numActivateRandom', count, 'effects.random_activate')
    _set(values, 'activateThisChoice', ','.join(ids), 'effects.random_activate')


def _apply_scroll(values: dict[str, Any], raw: Any) -> None:
    if isinstance(raw, str):
        raw = {'row': raw}
    if not isinstance(raw, dict):
        raise ValueError('effects.scroll_to must be an object or Row ID')
    row = str(raw.get('row', '')).strip()
    choice = str(raw.get('choice', raw.get('object', ''))).strip()
    if bool(row) == bool(choice):
        raise ValueError('effects.scroll_to must specify exactly one of row or choice')
    if row:
        _set(values, 'scrollToRow', True, 'effects.scroll_to')
        _set(values, 'scrollRowId', row, 'effects.scroll_to')
    else:
        _set(values, 'scrollToObject', True, 'effects.scroll_to')
        _set(values, 'scrollObjectId', choice, 'effects.scroll_to')


def _apply_template(values: dict[str, Any], raw: Any) -> None:
    if not isinstance(raw, dict):
        raise ValueError('effects.template must be an object')
    targets = _strings(raw.get('targets'), 'effects.template.targets')
    template = raw.get('to', raw.get('template'))
    if not targets or not isinstance(template, int) or isinstance(template, bool):
        raise ValueError('effects.template needs targets and integer template/to')
    _set(values, 'changeTemplates', True, 'effects.template')
    _set(values, 'changeTemplatesList', ','.join(targets), 'effects.template')
    _set(values, 'changeToThisTemplate', template, 'effects.template')
    if 'addons' in raw:
        _set(values, 'changeAddonTemplate', bool(raw['addons']), 'effects.template')


def _apply_width(values: dict[str, Any], raw: Any) -> None:
    if not isinstance(raw, dict):
        raise ValueError('effects.width must be an object')
    targets = _strings(raw.get('targets'), 'effects.width.targets')
    width = str(raw.get('to', raw.get('width', ''))).strip()
    if not targets or not width:
        raise ValueError('effects.width needs targets and width/to')
    _set(values, 'changeWidth', True, 'effects.width')
    _set(values, 'changeWidthList', ','.join(targets), 'effects.width')
    _set(values, 'changeToThisWidth', width, 'effects.width')


def _apply_sfx(values: dict[str, Any], raw: Any) -> None:
    if isinstance(raw, str):
        raw = {'select': raw}
    if not isinstance(raw, dict):
        raise ValueError('effects.sfx must be an object or Sound Effect ID')
    select = str(raw.get('select', raw.get('on_select', ''))).strip()
    deselect = str(raw.get('deselect', raw.get('on_deselect', ''))).strip()
    if not select and not deselect:
        raise ValueError('effects.sfx needs select and/or deselect')
    _set(values, 'useSfx', True, 'effects.sfx')
    if select:
        _set(values, 'sfxOnSelect', True, 'effects.sfx')
        _set(values, 'sfxIdOnSelect', select, 'effects.sfx')
    if deselect:
        _set(values, 'sfxOnDeselect', True, 'effects.sfx')
        _set(values, 'sfxIdOnDeselect', deselect, 'effects.sfx')


def _apply_delay(values: dict[str, Any], raw: Any) -> None:
    if not isinstance(raw, dict):
        raise ValueError('effects.delay must be an object')
    if 'select' in raw:
        seconds = raw['select']
        if not isinstance(seconds, (int, float)) or isinstance(seconds, bool) or seconds < 0:
            raise ValueError('effects.delay.select must be a non-negative number')
        _set(values, 'isSelectDelayed', True, 'effects.delay')
        _set(values, 'selectDelayTime', seconds, 'effects.delay')
    if 'deselect' in raw:
        seconds = raw['deselect']
        if not isinstance(seconds, (int, float)) or isinstance(seconds, bool) or seconds < 0:
            raise ValueError('effects.delay.deselect must be a non-negative number')
        _set(values, 'isDeselectDelayed', True, 'effects.delay')
        _set(values, 'deselectDelayTime', seconds, 'effects.delay')
    if 'select' not in raw and 'deselect' not in raw:
        raise ValueError('effects.delay needs select and/or deselect')


def _apply_background(values: dict[str, Any], raw: Any) -> None:
    if isinstance(raw, str):
        raw = {'color': raw}
    if not isinstance(raw, dict):
        raise ValueError('effects.background must be an object or color string')
    color = raw.get('color')
    image = raw.get('image')
    if color is None and image is None:
        raise ValueError('effects.background needs color and/or image')
    _set(values, 'changeBackground', True, 'effects.background')
    if color is not None:
        _set(values, 'changedBgColorCode', str(color), 'effects.background')
    if image is not None:
        _set(values, 'changeBgImage', True, 'effects.background')
        _set(values, 'bgImage', str(image), 'effects.background')


def _apply_point_bar(values: dict[str, Any], raw: Any) -> None:
    if not isinstance(raw, dict):
        raise ValueError('effects.point_bar must be an object')
    if not any(k in raw for k in ('background', 'text', 'icon')):
        raise ValueError('effects.point_bar needs background, text, and/or icon')
    _set(values, 'changePointBar', True, 'effects.point_bar')
    for source_key, flag, native in (
        ('background', 'changeBarBgColorIsOn', 'changedBarBgColor'),
        ('text', 'changeBarTextColorIsOn', 'changedBarTextColor'),
        ('icon', 'changeBarIconColorIsOn', 'changedBarIconColor'),
    ):
        if source_key in raw:
            _set(values, flag, True, 'effects.point_bar')
            _set(values, native, str(raw[source_key]), 'effects.point_bar')


def _apply_selection(values: dict[str, Any], raw: Any) -> None:
    if not isinstance(raw, dict):
        raise ValueError('effects.selection must be an object')
    mapping = {
        'not_selectable': 'isNotSelectable',
        'select_once': 'selectOnce',
        'allow_deselect': 'isAllowDeselect',
        'auto_active': 'isAutoActive',
        'activate_after_reset': 'activateAfterReset',
        'not_deselected_by_clean': 'notDeselectedByClean',
        'clean_activated_on_select': 'cleanACtivatedOnSelect',
        'not_deactivate': 'isNotDeactivate',
        'active_unselectable': 'isNotActiveUnselectable',
        'count_disabled': 'isCountDisabled',
        'deselect_when_no_addon': 'deselectWhenNoAddon',
        'not_searchable': 'isNotSearchable',
        'not_result': 'isNotResult',
        'image_upload': 'isImageUpload',
        'show_debug_title': 'showDebugTitle',
    }
    unknown = set(raw) - set(mapping)
    if unknown:
        raise ValueError(f'unknown effects.selection key(s): {", ".join(sorted(unknown))}')
    for key, native in mapping.items():
        if key in raw:
            _set(values, native, bool(raw[key]), 'effects.selection')


def _apply_duplicate_row(values: dict[str, Any], raw: Any) -> None:
    if isinstance(raw, str):
        raw = {'source': raw}
    if not isinstance(raw, dict):
        raise ValueError('effects.duplicate_row must be an object or Row ID')
    source = str(raw.get('source', raw.get('row', ''))).strip()
    if not source:
        raise ValueError('effects.duplicate_row.source is required')
    _set(values, 'duplicateRow', True, 'effects.duplicate_row')
    _set(values, 'duplicateRowId', source, 'effects.duplicate_row')
    if 'after' in raw:
        _set(values, 'duplicateRowPlace', str(raw['after']), 'effects.duplicate_row')
    if 'preserve_requirement_ids' in raw:
        _set(values, 'dRowAddSufReq', bool(raw['preserve_requirement_ids']), 'effects.duplicate_row')
    if 'preserve_function_ids' in raw:
        _set(values, 'dRowAddSufFunc', bool(raw['preserve_function_ids']), 'effects.duplicate_row')


def _apply_addons(values: dict[str, Any], raw: Any) -> None:
    if not isinstance(raw, dict):
        raise ValueError('effects.addons must be an object')
    mapping = {
        'show_all': 'showAllAddons',
        'separate_layout': 'useSeperateAddon',
        'show_score': 'showScoreInAddon',
        'show_requirements': 'showReqInAddon',
        'show_multiple': 'showMulInAddon',
    }
    unknown = set(raw) - set(mapping)
    if unknown:
        raise ValueError(f'unknown effects.addons key(s): {", ".join(sorted(unknown))}')
    for key, native in mapping.items():
        if key in raw:
            _set(values, native, bool(raw[key]), 'effects.addons')


def _apply_bgm(values: dict[str, Any], raw: Any) -> None:
    if isinstance(raw, str):
        raw = {'id': raw}
    if not isinstance(raw, dict):
        raise ValueError('effects.bgm must be an object or BGM ID/URL')
    allowed = {'id', 'url', 'fade_in', 'fade_out', 'no_loop', 'mute'}
    unknown = set(raw) - allowed
    if unknown:
        raise ValueError(f'unknown effects.bgm key(s): {", ".join(sorted(unknown))}')
    ident = str(raw.get('id', raw.get('url', ''))).strip()
    if ident:
        _set(values, 'setBgmIsOn', True, 'effects.bgm')
        _set(values, 'bgmId', ident, 'effects.bgm')
        if 'url' in raw:
            _set(values, 'useAudioURL', True, 'effects.bgm')
    if 'fade_in' in raw:
        seconds = raw['fade_in']
        if not isinstance(seconds, (int, float)) or isinstance(seconds, bool) or seconds < 0:
            raise ValueError('effects.bgm.fade_in must be a non-negative number')
        _set(values, 'bgmFadeIn', True, 'effects.bgm')
        _set(values, 'bgmFadeInSec', seconds, 'effects.bgm')
    if 'fade_out' in raw:
        seconds = raw['fade_out']
        if not isinstance(seconds, (int, float)) or isinstance(seconds, bool) or seconds < 0:
            raise ValueError('effects.bgm.fade_out must be a non-negative number')
        _set(values, 'bgmFadeOut', True, 'effects.bgm')
        _set(values, 'bgmFadeOutSec', seconds, 'effects.bgm')
    if 'no_loop' in raw:
        _set(values, 'bgmNoLoop', bool(raw['no_loop']), 'effects.bgm')
    if 'mute' in raw:
        _set(values, 'muteBgm', bool(raw['mute']), 'effects.bgm')
    if not ident and not any(k in raw for k in ('mute', 'no_loop', 'fade_in', 'fade_out')):
        raise ValueError('effects.bgm needs id/url or a BGM behavior field')


def _apply_transition(values: dict[str, Any], raw: Any) -> None:
    if raw is True:
        raw = {}
    if not isinstance(raw, dict):
        raise ValueError('effects.transition must be true or an object')
    allowed = {'color', 'time', 'fade_in', 'fade_out'}
    unknown = set(raw) - allowed
    if unknown:
        raise ValueError(f'unknown effects.transition key(s): {", ".join(sorted(unknown))}')
    _set(values, 'isFadeTransition', True, 'effects.transition')
    if 'color' in raw:
        _set(values, 'fadeTransitionColor', str(raw['color']), 'effects.transition')
    for source, native in (('time', 'fadeTransitionTime'), ('fade_in', 'fadeInTransitionTime'), ('fade_out', 'fadeOutTransitionTime')):
        if source in raw:
            val = raw[source]
            if not isinstance(val, (int, float)) or isinstance(val, bool) or val < 0:
                raise ValueError(f'effects.transition.{source} must be a non-negative number')
            _set(values, native, val, 'effects.transition')


def apply_choice_effects(values: dict[str, Any], raw_effects: Any = None, *, consume_legacy: bool = False) -> None:
    """Expand compact, script-friendly effect aliases into native ChoiceFunc fields.

    The function writes ordinary ICC Plus properties. It never creates a second
    runtime representation. Conflicting shorthand and native fields fail early.
    """
    effects = _effect_object(raw_effects)
    if consume_legacy:
        for key in ('activate', 'deactivate', 'hide_contents'):
            if key not in values:
                continue
            if key in effects and effects[key] != values[key]:
                raise ValueError(f'{key} is set both directly and inside effects with different values')
            effects[key] = values.pop(key)

    known = {
        'activate', 'deactivate', 'hide_contents', 'row_limit', 'variables',
        'points', 'word', 'multiple', 'discount', 'random_activate', 'scroll_to',
        'template', 'width', 'sfx', 'delay', 'background', 'point_bar', 'confirm',
        'selection', 'duplicate_row', 'addons', 'bgm', 'transition', 'random_weight',
        'backpack_button_requirement', 'default_image',
    }
    unknown = set(effects) - known
    if unknown:
        raise ValueError(f'unknown effects key(s): {", ".join(sorted(unknown))}')

    if 'activate' in effects:
        _apply_activate(values, effects['activate'])
    if 'deactivate' in effects:
        _apply_activate(values, effects['deactivate'], deactivate=True)
    if 'hide_contents' in effects:
        _apply_hide_contents(values, effects['hide_contents'])
    if 'row_limit' in effects:
        _apply_row_limit(values, effects['row_limit'])
    if 'variables' in effects:
        _apply_variables(values, effects['variables'])
    if 'points' in effects:
        _apply_points(values, effects['points'])
    if 'word' in effects:
        _apply_word(values, effects['word'])
    if 'multiple' in effects:
        _apply_multiple(values, effects['multiple'])
    if 'discount' in effects:
        _apply_discount(values, effects['discount'])
    if 'random_activate' in effects:
        _apply_random_activate(values, effects['random_activate'])
    if 'scroll_to' in effects:
        _apply_scroll(values, effects['scroll_to'])
    if 'template' in effects:
        _apply_template(values, effects['template'])
    if 'width' in effects:
        _apply_width(values, effects['width'])
    if 'sfx' in effects:
        _apply_sfx(values, effects['sfx'])
    if 'delay' in effects:
        _apply_delay(values, effects['delay'])
    if 'background' in effects:
        _apply_background(values, effects['background'])
    if 'point_bar' in effects:
        _apply_point_bar(values, effects['point_bar'])
    if 'confirm' in effects:
        _set(values, 'confirmIsOn', bool(effects['confirm']), 'effects.confirm')
    if 'selection' in effects:
        _apply_selection(values, effects['selection'])
    if 'duplicate_row' in effects:
        _apply_duplicate_row(values, effects['duplicate_row'])
    if 'addons' in effects:
        _apply_addons(values, effects['addons'])
    if 'bgm' in effects:
        _apply_bgm(values, effects['bgm'])
    if 'transition' in effects:
        _apply_transition(values, effects['transition'])
    if 'random_weight' in effects:
        weight = effects['random_weight']
        if not isinstance(weight, (int, float)) or isinstance(weight, bool):
            raise ValueError('effects.random_weight must be numeric')
        _set(values, 'randomWeight', weight, 'effects.random_weight')
    if 'backpack_button_requirement' in effects:
        _set(values, 'backpackBtnRequirement', bool(effects['backpack_button_requirement']), 'effects.backpack_button_requirement')
    if 'default_image' in effects:
        _set(values, 'defaultImage', str(effects['default_image']), 'effects.default_image')
