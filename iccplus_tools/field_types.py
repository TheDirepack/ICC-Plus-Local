from __future__ import annotations

"""Pinned ICC Plus 2.10.7 native field type metadata.

The field names and primitive/container types in this module are transcribed from
``ICCPlus/src/lib/store/types.ts`` at commit
``1ea9db888cde2286d18d0d5de50933cb8773b739``.  The catalog remains the source
of truth for which fields exist; this module adds the value shape needed by
scripts, schemas, generated type declarations, and LLM-facing help.
"""

from dataclasses import dataclass
from typing import Any

from .field_catalog import (
    FIELD_CATALOG,
    STYLE_FIELD_GROUPS,
    SOURCE_COMMIT,
    SOURCE_FILE,
    SOURCE_REPOSITORY,
    ICC_PLUS_VERSION,
)
from .upstream_2106 import DEFAULT_APP, STYLING


@dataclass(frozen=True)
class FieldType:
    code: str
    typescript: str
    json_types: tuple[str, ...]
    description: str
    literal: Any = None


_TYPE_INFO: dict[str, FieldType] = {
    'b': FieldType('b', 'boolean', ('boolean',), 'boolean'),
    'n': FieldType('n', 'number', ('number',), 'number'),
    's': FieldType('s', 'string', ('string',), 'string'),
    'sa': FieldType('sa', 'string[]', ('array',), 'array of strings'),
    'na': FieldType('na', 'number[]', ('array',), 'array of numbers'),
    'ba': FieldType('ba', 'boolean[]', ('array',), 'array of booleans'),
    'ssa': FieldType('ssa', 'string[][]', ('array',), 'array of string arrays'),
    'ns': FieldType('ns', 'number | string', ('number', 'string'), 'number or string'),
    'o': FieldType('o', 'Record<string, unknown>', ('object',), 'object'),
    'oa': FieldType('oa', 'Record<string, unknown>[]', ('array',), 'array of objects'),
    'true': FieldType('true', 'true', ('boolean',), 'literal true', True),
    'false': FieldType('false', 'false', ('boolean',), 'literal false', False),
}


def _parse(spec: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in spec.split(';'):
        item = item.strip()
        if not item:
            continue
        name, code = item.split(':', 1)
        out[name] = code
    return out


# Compact forms keep the pinned source audit reviewable.  ``oa`` means a typed
# object array in upstream TypeScript; nested object schemas are handled by the
# dedicated entity schemas where a stable named type exists.
_TYPE_SPECS: dict[str, str] = {
    'project': '''version:s;isEditModeOnAll:b;isPointerCursor:b;importedChoicesIsOpen:b;curVolume:n;isMute:b;showMusicPlayer:b;fadeTransitionColor:s;fadeTransitionTime:n;fadeTransitionIsOn:b;hideBackpackBtn:n;btnBackpackIsOn:n;showAllAddons:n;tmpRow:oa;tmpChoice:oa;tmpRequired:oa;tmpScore:oa;tmpAddon:oa;tmpGroup:sa;tmpDesignGroup:sa;rowIdLength:n;objectIdLength:n;words:oa;groups:oa;rowDesignGroups:oa;objectDesignGroups:oa;objectsPerRow:s;globalRequirements:oa;soundEffects:oa;googleFonts:sa;customFonts:sa;compressImageAuto:b;useTextEditor:b;useToolbarBtn:b;useChoiceEditBtn:b;hideScoresUpdated:b;hideChoiceDT:b;hideImages:b;preloadImages:b;preloadExternalImages:b;useVW:b;addPrefix:b;mdObjects:sa;printThis:b;autoSaveIsOn:b;autoSaveInterval:n;buildAutoSaveIsOn:b;buildAutoSaveInterval:n;tooltipDelay:n;checkDeleteRow:b;checkDeleteObject:b;checkSelectAll:b;enableShortcut:b;defaultBgColor:s;defaultBgImage:s;defaultBarBgColor:s;defaultBarTextColor:s;defaultBarIconColor:s;bgColorStack:oa;bgImageStack:oa;barBgColorStack:oa;barTextColorStack:oa;barIconColorStack:oa;customCSS:s;variables:oa;pointTypes:oa;activated:sa;rows:oa;backpack:oa;styling:o;categories:oa;cropperPosition:n;enableSearch:b;useDesignGroupBtn:b;smallerScreenPx:n;enableHalfRow:b;minimizeTemplate:b;hideRowMenu:b;viewerConfig:o;defaultRowTitle:s;defaultRowText:s;defaultChoiceTitle:s;defaultChoiceText:s;defaultBeforePoint:s;defaultAfterPoint:s;defaultBeforeReq:s;defaultAfterReq:s;defaultAddonTitle:s;defaultAddonText:s;orderOrReqText:s;defaultOrReq:s;orderSelReqText:s;defaultSelReq:s;defaultRowTemplate:n;defaultRowWidth:s;defaultRowJustify:s;defaultRowAllowedChoices:n;defaultChoiceTemplate:n;defaultChoiceWidth:s;defaultChoiceMaxNum:n;defaultAddonJustify:s;defaultAddonTemplate:n;defaultAddonWidth:s;defaultUseSeperateAddon:b;defaultUseShowAddon:b;defaultUseHideAddon:b;defaultUseShowScore:b;defaultUseHideValue:b;defaultUseShowReq:b''',
    'requirement': '''required:b;requireds:oa;orRequired:oa;orRequireds:oa;id:s;type:s;reqId:s;reqId1:s;reqId2:s;reqId3:s;reqPoints:n;showRequired:b;hideRequired:b;hideRequired2:b;operator:s;afterText:s;beforeText:s;orNum:n;selNum:n;selFromOperators:s;selGroups:sa;selRows:sa;more:oa;customTextIsOn:b;customText:s''',
    'score': '''idx:s;id:s;value:n;type:s;beforeText:s;afterText:s;requireds:oa;showScore:b;isActive:b;isActiveMul:ba;isActiveMulMinus:ba;hideValue:b;isNotRecalculatable:b;isNotRecalculateSelf:b;isNotDiscountable:b;isRandom:b;minValue:n;maxValue:n;setValue:b;discounts:oa;discountIsOn:b;discountShow:b;discountBeforeText:s;discountAfterText:s;discountScore:n;discountScoreCal:n;isChangeDiscount:b;discountNum:n;tmpDisScore:n;tmpDiscount:oa;discountedFrom:sa;dupTextA:o;dupTextB:o;discountTextA:sa;discountTextB:sa;notStackableDiscount:b;multiplyByTimes:b;displayMulScore:b;appliedDiscount:b;replaceText:b;hideDisValue:b;hideDisIcon:b;useExpression:b;expValue:s;expMinValue:s;expMaxValue:s;mulValue:na;removeSpace:b''',
    'choice': '''id:s;index:n;title:s;text:s;debugTitle:s;image:s;imageSourceTooltip:s;template:n;objectWidth:s;isActive:b;multipleUseVariable:n;initMultipleTimesMinus:n;selectedThisManyTimesProp:n;requireds:oa;addons:oa;scores:oa;groups:sa;objectDesignGroups:sa;isPrivateStyling:b;privateFilterIsOn:b;privateTextIsOn:b;privateObjectImageIsOn:b;privateObjectIsOn:b;privateAddonImageIsOn:b;privateAddonIsOn:b;privateBackgroundIsOn:b;privateMultiChoiceIsOn:b;styling:o;addonJustify:s;linkedObjects:sa;hideMultipleCounter:b;allowSelectByClick:b;hideCounterUntilSelect:b;isSelectableMultiple:b;isMultipleUseVariable:b;multipleScoreId:s;numMultipleTimesMinus:n;numMultipleTimesPluss:n;isNotSelectable:b;selectOnce:b;notDeselectedByClean:b;isNotResult:b;isNotBuild:b;isImageUpload:b;cleanACtivatedOnSelect:b;activateOtherChoice:b;isNotDeactivate:b;isAllowDeselect:b;activateAfterReset:b;isActivateRandom:b;numActivateRandom:n;activateThisChoice:s;isNotActiveUnselectable:b;deactivateOtherChoice:b;deactivateThisChoice:s;discountOther:b;discountLowLimitIsOn:b;discountLowLimit:n;discountShow:b;replaceScoreText:b;hideScoreValue:b;hideScoreIcon:b;discountBeforeText:s;discountAfterText:s;isDisChoices:b;discountRows:sa;discountChoices:sa;discountGroups:sa;discountPointTypes:sa;discountOperator:s;discountValue:n;stackableDiscount:b;useDiscountCount:b;discountCount:n;countPerSelection:b;numDiscountChoices:n;appliedDisChoices:sa;duplicateRow:b;dRowAddSufReq:b;dRowAddSufFunc:b;duplicateRowId:s;duplicateRowPlace:s;isContentHidden:b;hiddenContentsRow:sa;hiddenContentsType:sa;addToAllowChoice:b;idOfAllowChoice:sa;numbAddToAllowChoice:n;showAllAddons:b;changeTemplates:b;changeAddonTemplate:b;changeWidth:b;changeTemplatesList:s;changeToThisTemplate:n;changeWidthList:s;changeToThisWidth:s;defaultTemplate:n;defaultWidth:s;scrollToRow:b;scrollToObject:b;scrollObjectId:s;scrollRowId:s;changePointBar:b;changeBarBgColorIsOn:b;changeBarTextColorIsOn:b;changeBarIconColorIsOn:b;changedBarBgColor:s;changedBarTextColor:s;changedBarIconColor:s;changeBackground:b;changeBgImage:b;changedBgColorCode:s;bgImage:s;setBgmIsOn:b;bgmId:s;bgmFadeIn:b;bgmFadeOut:b;bgmFadeInSec:n;bgmFadeOutSec:n;bgmNoLoop:b;muteBgm:b;useAudioURL:b;isFadeTransition:b;fadeTransitionColor:s;fadeTransitionTime:n;fadeInTransitionTime:n;fadeOutTransitionTime:n;multiplyPointtypeIsOn:b;pointTypeToMultiply:sa;multiplyWithThis:ns;multiplyPointtypeIsId:b;dividePointtypeIsOn:b;pointTypeToDivide:sa;divideWithThis:n;startingSumAtMultiply:oa;startingSumAtDivide:oa;startingSumAtSet:oa;multiplyPointtypeIsOnCheck:b;dividePointtypeIsOnCheck:b;setPointtypeIsOnCheck:b;isChangeVariables:b;changedVariables:sa;changeType:s;textfieldIsOn:b;customTextfieldIsOn:b;idOfTheTextfieldWord:s;wordPromptText:s;wordChangeSelect:s;wordChangeDeselect:s;confirmIsOn:b;backpackBtnRequirement:b;forcedActivated:b;activatedFrom:n;activatedRandom:sa;activatedRandomMul:ssa;defaultImage:s;tempMultipleValue:n;randomWeight:n;useSeperateAddon:b;useSlider:b;hideCounter:b;templateStack:oa;widthStack:oa;isEditModeOn:b;isSelectDelayed:b;selectDelayTime:n;selectDelayTimer:b;isDeselectDelayed:b;deselectDelayTime:n;deselectDelayTimer:b;showScoreInAddon:b;showReqInAddon:b;showMulInAddon:b;setPointtypeIsOn:b;pointTypeToSet:sa;setWithThis:s;isNotSearchable:b;isAutoActive:b;useSfx:b;sfxIdOnSelect:s;sfxIdOnDeselect:s;sfxOnSelect:b;sfxOnDeselect:b;isCountDisabled:b;deselectWhenNoAddon:b;showDebugTitle:b''',
    'row': '''id:s;index:n;isBackpack:b;title:s;titleText:s;debugTitle:s;objectWidth:s;image:s;template:n;isButtonRow:b;buttonType:b;buttonId:s;buttonText:s;buttonRandom:b;buttonRandomNumber:n;isWeightedRandom:b;allowActivateUnselectable:b;isResultRow:b;resultGroupId:s;isInfoRow:b;isGroupRow:b;defaultAspectWidth:n;defaultAspectHeight:n;allowedChoices:n;currentChoices:n;requireds:oa;isEditModeOn:b;isSimpleEditMode:b;isRequirementOpen:b;objects:oa;rowDesignGroups:sa;imageIsUrl:b;width:b;deselectChoices:b;rowJustify:s;groups:sa;imageSourceTooltip:s;isPrivateStyling:b;privateFilterIsOn:b;privateTextIsOn:b;privateObjectImageIsOn:b;privateObjectIsOn:b;privateRowImageIsOn:b;privateRowIsOn:b;privateAddonImageIsOn:b;privateAddonIsOn:b;privateBackgroundIsOn:b;privateMultiChoiceIsOn:b;styling:o;objectImgObjectFillHeight:n;resultShowRowTitle:b;textIsRemoved:b;objectTitleRemoved:b;objectImageRemoved:b;objectTextRemoved:b;objectScoreRemoved:b;objectRequirementRemoved:b;addonTitleRemoved:b;addonImageRemoved:b;addonTextRemoved:b;unselAddonRemoved:b;unmetAddonRemoved:b;buttonTypeRadio:s;btnPointAddon:b;pointTypeRandom:s;randomMin:n;randomMax:n;onlyUnselectedChoices:b;onlyIfNoChoices:b;choicesShareTemplate:b;defaultTemplate:n;defaultWidth:s;overrideWidth:b;preserveWidth:b;templateStack:oa;widthStack:oa''',
    'addon': '''id:s;title:s;text:s;template:n;image:s;imageSourceTooltip:s;requireds:oa;parentId:s;showAddon:b;hideAddon:b;skipIndex:b;defaultTemplate:n;templateStack:oa;addonWidth:s;isSelectable:false''',
    'point': '''id:s;name:s;startingSum:n;initValue:n;activatedId:s;beforeText:s;afterText:s;belowZeroNotAllowed:b;isNotShownPointBar:b;isNotShownObjects:b;plussOrMinusAdded:b;plussOrMinusInverted:b;pointColorsIsOn:b;positiveColor:s;negativeColor:s;iconIsOn:b;useSeperatePosition:b;image:s;imageOnSide:b;imageSidePlacement:b;imageOnSideInChoice:b;imageSidePlacementInChoice:b;iconWidth:n;iconHeight:n;negativeIconIsOn:b;negativeImage:s;negativeImageOnSide:b;negativeImageSidePlacement:b;negativeImageOnSideInChoice:b;negativeImageSidePlacementInChoice:b;negativeIconWidth:n;negativeIconHeight:n;pointPrivateColorIsOn:b;privateColor:s;privateNegativeColor:s;treatZeroAsNegative:b;imageIsURL:b;allowFloat:b;decimalPlaces:n;category:n;useScoreText:b;scoreBeforeText:s;scoreAfterText:s''',
    'variable': 'id:s;isTrue:b;category:n',
    'word': 'id:s;replaceText:s;category:n',
    'group': 'id:s;name:s;category:n;elements:sa;rowElements:sa;designGroups:sa',
    'global_requirement': 'id:s;name:s;category:n;requireds:oa',
    'row_design_group': 'id:s;name:s;activatedId:s;elements:sa;backpackElements:sa;groupElements:sa;privateFilterIsOn:b;privateTextIsOn:b;privateObjectImageIsOn:b;privateObjectIsOn:b;privateRowImageIsOn:b;privateRowIsOn:b;privateAddonImageIsOn:b;privateAddonIsOn:b;privateBackgroundIsOn:b;category:n;styling:o',
    'choice_design_group': 'id:s;name:s;activatedId:s;elements:sa;backpackElements:sa;groupElements:sa;privateFilterIsOn:b;privateTextIsOn:b;privateObjectImageIsOn:b;privateObjectIsOn:b;privateAddonImageIsOn:b;privateAddonIsOn:b;privateBackgroundIsOn:b;category:n;styling:o',
    'viewer_config': 'title:s;favicon:s;loadingType:s;loadingBgColor:s;loadingBgImage:s;loadingCircleColor:s;loadingTrackColor:s;loadingText:s;loadingTextColor:s;loadingTextFont:s;loadingTextShadow:s;useSeparateImages:b;useLocalViewer:b',
    'sound_effect': 'id:s;name:s;audio:s;volume:n;pitch:n;isDefault:b;onSelected:b;onDeselected:b;requireds:oa;groups:sa',
    'category': 'idx:n;name:s;type:s',
    'defaults': 'defaultRowTitle:s;defaultRowText:s;defaultChoiceTitle:s;defaultChoiceText:s;defaultBeforePoint:s;defaultAfterPoint:s;defaultBeforeReq:s;defaultAfterReq:s;defaultAddonTitle:s;defaultAddonText:s;orderOrReqText:s;defaultOrReq:s;orderSelReqText:s;defaultSelReq:s;defaultRowTemplate:n;defaultRowWidth:s;defaultRowJustify:s;defaultRowAllowedChoices:n;defaultChoiceTemplate:n;defaultChoiceWidth:s;defaultChoiceMaxNum:n;defaultAddonJustify:s;defaultAddonTemplate:n;defaultAddonWidth:s;defaultUseSeperateAddon:b;defaultUseShowAddon:b;defaultUseHideAddon:b;defaultUseShowScore:b;defaultUseHideValue:b;defaultUseShowReq:b',
}



# Fields without ``?`` in the pinned TypeScript declarations. Patch schemas keep
# every field optional; native schemas/declarations use this map to expose the
# source contract directly.
_REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
    'project': ('isEditModeOnAll','isPointerCursor','importedChoicesIsOpen','curVolume','isMute','showMusicPlayer','fadeTransitionColor','fadeTransitionTime','fadeTransitionIsOn','hideBackpackBtn','btnBackpackIsOn','showAllAddons','tmpRow','tmpChoice','tmpRequired','tmpScore','tmpAddon','tmpGroup','tmpDesignGroup','rowIdLength','objectIdLength','words','groups','objectDesignGroups','objectsPerRow','soundEffects','googleFonts','customFonts','compressImageAuto','useTextEditor','useToolbarBtn','useChoiceEditBtn','hideScoresUpdated','hideChoiceDT','hideImages','preloadImages','preloadExternalImages','useVW','mdObjects','printThis','autoSaveIsOn','autoSaveInterval','buildAutoSaveIsOn','buildAutoSaveInterval','checkDeleteRow','checkDeleteObject','checkSelectAll','enableShortcut','variables','pointTypes','activated','rows','backpack','styling','categories','cropperPosition','enableSearch','useDesignGroupBtn','smallerScreenPx','enableHalfRow','minimizeTemplate','hideRowMenu','viewerConfig','defaultRowTitle','defaultRowText','defaultChoiceTitle','defaultChoiceText','defaultBeforePoint','defaultAfterPoint','defaultBeforeReq','defaultAfterReq','defaultAddonTitle','defaultAddonText','orderOrReqText','defaultOrReq','orderSelReqText','defaultSelReq','defaultRowTemplate','defaultRowWidth','defaultRowJustify','defaultRowAllowedChoices','defaultChoiceTemplate','defaultChoiceWidth','defaultChoiceMaxNum','defaultAddonJustify','defaultAddonTemplate','defaultAddonWidth','defaultUseSeperateAddon','defaultUseShowAddon','defaultUseHideAddon','defaultUseShowScore','defaultUseHideValue','defaultUseShowReq'),
    'requirement': ('required','requireds','orRequired','id','type','reqId','reqId1','reqId2','reqId3','reqPoints','showRequired','afterText','beforeText'),
    'score': ('idx','id','value','type','beforeText','afterText','requireds','showScore'),
    'choice': ('id','index','title','text','debugTitle','image','template','objectWidth','isActive','multipleUseVariable','selectedThisManyTimesProp','requireds','addons','scores','groups'),
    'addon': ('title','text','template','image','requireds'),
    'selectable_addon': ('title','text','template','image','requireds','isSelectable','scores','groups','multipleUseVariable','isActive'),
    'row': ('id','index','title','titleText','objectWidth','image','template','defaultAspectWidth','defaultAspectHeight','allowedChoices','currentChoices','requireds','objects'),
    'point': ('id','name','startingSum','initValue','activatedId','beforeText','afterText'),
    'variable': ('id','isTrue'),
    'word': ('id','replaceText'),
    'group': ('id','name','rowElements'),
    'global_requirement': ('id','name','requireds'),
    'row_design_group': ('id','name','activatedId','elements','backpackElements','groupElements'),
    'choice_design_group': ('id','name','activatedId','elements','backpackElements','groupElements'),
    'sound_effect': ('id','name','audio','volume','pitch','isDefault','onSelected','onDeselected','requireds','groups'),
    'category': ('idx','name','type'),
    'viewer_config': ('title','favicon','loadingType','loadingBgColor','loadingBgImage','loadingCircleColor','loadingTrackColor','loadingText','loadingTextColor','loadingTextFont','loadingTextShadow','useSeparateImages','useLocalViewer'),
}

def required_fields(kind: str) -> tuple[str, ...]:
    return _REQUIRED_FIELDS.get(normalize_kind(kind), ())

FIELD_TYPE_CODES: dict[str, dict[str, str]] = {kind: _parse(spec) for kind, spec in _TYPE_SPECS.items()}
FIELD_TYPE_CODES['backpack_row'] = FIELD_TYPE_CODES['row']

# A selectable Addon combines BaseAddon, SelectableAddon, and ChoiceFunc.  Reuse
# the audited ChoiceFunc field types from Choice instead of maintaining a second
# long copy that could drift.
_selectable: dict[str, str] = {}
for field in FIELD_CATALOG['selectable_addon']:
    if field == 'isSelectable':
        _selectable[field] = 'true'
    elif field in FIELD_TYPE_CODES['addon']:
        _selectable[field] = FIELD_TYPE_CODES['addon'][field]
    elif field in FIELD_TYPE_CODES['choice']:
        _selectable[field] = FIELD_TYPE_CODES['choice'][field]
    elif field in {'scores'}:
        _selectable[field] = 'oa'
    elif field in {'groups'}:
        _selectable[field] = 'sa'
    elif field in {'multipleUseVariable'}:
        _selectable[field] = 'n'
    elif field in {'isActive', 'deselectParent', 'countAsChoice'}:
        _selectable[field] = 'b'
FIELD_TYPE_CODES['selectable_addon'] = _selectable

# Styling has 334 pinned fields.  The upstream default object supplies exact
# runtime primitive types for nearly all of them.  Three source-typed fields do
# not occur under their exact source spelling in the default object.
_style_types: dict[str, str] = {}
for field in FIELD_CATALOG['styling']:
    if field in STYLING:
        value = STYLING[field]
        if isinstance(value, bool):
            _style_types[field] = 'b'
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            _style_types[field] = 'n'
        elif isinstance(value, str):
            _style_types[field] = 's'
        else:
            _style_types[field] = 'o'
    else:
        _style_types[field] = 's'  # reqFilterImgBorderColor, borderRadiusSuffix, barBackgroundImage
FIELD_TYPE_CODES['styling'] = _style_types

# The pinned default project still serializes two historical misspellings even
# though ``types.ts`` and the active Creator controls use the corrected names.
# Keep the field catalog source-exact, but accept these optional keys when a
# native/wire object is being typed or validated so the official 2.10.7 default
# export validates without normalization. New authoring should use the corrected
# source field names.
WIRE_COMPAT_FIELDS: dict[str, dict[str, str]] = {
    'styling': {
        'barBacktroundImage': 's',
        'reqImgFilterBorderColor': 's',
    },
}
WIRE_COMPAT_ALIASES: dict[str, dict[str, str]] = {
    'styling': {
        'barBacktroundImage': 'barBackgroundImage',
        'reqImgFilterBorderColor': 'reqFilterImgBorderColor',
    },
}


def _validate_metadata() -> None:
    missing: dict[str, list[str]] = {}
    extras: dict[str, list[str]] = {}
    for kind, fields in FIELD_CATALOG.items():
        if kind == 'backpack_row':
            continue
        typed = FIELD_TYPE_CODES.get(kind, {})
        m = [field for field in fields if field not in typed]
        e = [field for field in typed if field not in fields]
        if m:
            missing[kind] = m
        if e:
            extras[kind] = e
    if missing or extras:
        raise RuntimeError(f'field type metadata drift: missing={missing!r}, extras={extras!r}')


_validate_metadata()


def normalize_kind(kind: str) -> str:
    return 'row' if kind == 'backpack_row' else kind


def field_type_code(kind: str, field: str) -> str | None:
    return FIELD_TYPE_CODES.get(normalize_kind(kind), {}).get(field)


def field_type(kind: str, field: str) -> FieldType | None:
    code = field_type_code(kind, field)
    return _TYPE_INFO.get(code) if code else None


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def value_matches(code: str, value: Any) -> bool:
    if code == 'b':
        return isinstance(value, bool)
    if code == 'n':
        return _is_number(value)
    if code == 's':
        return isinstance(value, str)
    if code == 'sa':
        return isinstance(value, list) and all(isinstance(x, str) for x in value)
    if code == 'na':
        return isinstance(value, list) and all(_is_number(x) for x in value)
    if code == 'ba':
        return isinstance(value, list) and all(isinstance(x, bool) for x in value)
    if code == 'ssa':
        return isinstance(value, list) and all(isinstance(x, list) and all(isinstance(y, str) for y in x) for x in value)
    if code == 'ns':
        return isinstance(value, str) or _is_number(value)
    if code == 'o':
        return isinstance(value, dict)
    if code == 'oa':
        return isinstance(value, list) and all(isinstance(x, dict) for x in value)
    if code == 'true':
        return value is True
    if code == 'false':
        # Upstream NonSelectableAddon spells this as false | undefined.  If a
        # field is explicitly supplied, false is the only valid value.
        return value is False
    return True


def expected_text(kind: str, field: str) -> str:
    info = field_type(kind, field)
    return info.description if info else 'unknown'


def validate_field_value(kind: str, field: str, value: Any, *, path: str | None = None) -> None:
    code = field_type_code(kind, field)
    if code is None:
        return
    if value_matches(code, value):
        return
    label = path or f'{normalize_kind(kind)}.{field}'
    raise ValueError(f'{label} expects {expected_text(kind, field)}, got {type(value).__name__}')


def validate_known_values(
    kind: str,
    values: dict[str, Any],
    *,
    path: str | None = None,
    recursive: bool = False,
    strict_fields: bool = False,
) -> None:
    catalog_kind = normalize_kind(kind)
    catalog = set(FIELD_CATALOG.get(catalog_kind, []))
    if strict_fields:
        unknown = sorted(set(values) - catalog)
        if unknown:
            label = path or catalog_kind
            raise ValueError(f'{label} has unknown native field(s): {", ".join(unknown)}')
    for field, value in values.items():
        if field not in catalog:
            continue
        field_path = f'{path}.{field}' if path else f'{catalog_kind}.{field}'
        validate_field_value(catalog_kind, field, value, path=field_path)
        if not recursive:
            continue
        if catalog_kind == 'choice' and field == 'addons' and isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    nested_kind = 'selectable_addon' if item.get('isSelectable') is True else 'addon'
                    validate_known_values(nested_kind, item, path=f'{field_path}[{i}]', recursive=True, strict_fields=strict_fields)
            continue
        nested_kind = _NESTED_TYPES.get((catalog_kind, field))
        if nested_kind is None:
            continue
        code = field_type_code(catalog_kind, field)
        if code == 'oa' and isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    validate_known_values(nested_kind, item, path=f'{field_path}[{i}]', recursive=True, strict_fields=strict_fields)
        elif isinstance(value, dict):
            validate_known_values(nested_kind, value, path=field_path, recursive=True, strict_fields=strict_fields)


def field_default(kind: str, field: str) -> tuple[bool, Any]:
    catalog_kind = normalize_kind(kind)
    if catalog_kind in {'project', 'defaults'} and field in DEFAULT_APP:
        return True, DEFAULT_APP[field]
    if catalog_kind == 'styling':
        if field in STYLING:
            return True, STYLING[field]
        # Exact type names differ from two historical default spellings in the
        # pinned source.  Do not invent a default for those fields.
    return False, None


def field_details(kind: str, field: str) -> dict[str, Any]:
    catalog_kind = normalize_kind(kind)
    if field not in FIELD_CATALOG.get(catalog_kind, []):
        raise ValueError(f'unknown native field {field!r} for {catalog_kind}')
    info = field_type(catalog_kind, field)
    has_default, default = field_default(catalog_kind, field)
    out: dict[str, Any] = {
        'name': field,
        'type': info.typescript if info else 'unknown',
        'value_shape': info.description if info else 'unknown',
    }
    if has_default:
        out['default'] = default
    return out


def fields_details(kind: str, fields: list[str]) -> list[dict[str, Any]]:
    return [field_details(kind, field) for field in fields]


_NESTED_TYPES: dict[tuple[str, str], str] = {
    ('project', 'rows'): 'row', ('project', 'backpack'): 'row',
    ('project', 'pointTypes'): 'point', ('project', 'variables'): 'variable',
    ('project', 'words'): 'word', ('project', 'groups'): 'group',
    ('project', 'rowDesignGroups'): 'row_design_group', ('project', 'objectDesignGroups'): 'choice_design_group',
    ('project', 'globalRequirements'): 'global_requirement', ('project', 'soundEffects'): 'sound_effect',
    ('project', 'categories'): 'category', ('project', 'viewerConfig'): 'viewer_config', ('project', 'styling'): 'styling',
    ('row', 'objects'): 'choice', ('row', 'requireds'): 'requirement', ('row', 'styling'): 'styling',
    ('choice', 'requireds'): 'requirement', ('choice', 'scores'): 'score', ('choice', 'styling'): 'styling',
    ('selectable_addon', 'requireds'): 'requirement', ('selectable_addon', 'scores'): 'score',
    ('addon', 'requireds'): 'requirement',
    ('score', 'requireds'): 'requirement',
    ('requirement', 'requireds'): 'requirement', ('requirement', 'orRequireds'): 'requirement',
    ('global_requirement', 'requireds'): 'requirement',
    ('sound_effect', 'requireds'): 'requirement',
    ('row_design_group', 'styling'): 'styling', ('choice_design_group', 'styling'): 'styling',
}


def _ts_type_for_field(kind: str, field: str, *, suffix: str = 'Patch') -> str:
    nested = _NESTED_TYPES.get((normalize_kind(kind), field))
    if nested:
        name = _type_name(nested, suffix)
        code = field_type_code(kind, field)
        return f'{name}[]' if code == 'oa' else name
    if normalize_kind(kind) == 'choice' and field == 'addons':
        return f'(Addon{suffix} | SelectableAddon{suffix})[]'
    info = field_type(kind, field)
    return info.typescript if info else 'unknown'


def _python_type_for_field(kind: str, field: str, *, suffix: str = 'Patch') -> str:
    nested = _NESTED_TYPES.get((normalize_kind(kind), field))
    if nested:
        name = _type_name(nested, suffix)
        code = field_type_code(kind, field)
        return f'list[{name}]' if code == 'oa' else name
    if normalize_kind(kind) == 'choice' and field == 'addons':
        return f'list[Addon{suffix} | SelectableAddon{suffix}]'
    return _python_type(field_type_code(kind, field) or '')


def _schema_for_field(kind: str, field: str) -> dict[str, Any]:
    nested = _NESTED_TYPES.get((normalize_kind(kind), field))
    if nested:
        ref = {'$ref': f'#/$defs/{normalize_kind(nested)}'}
        return {'type': 'array', 'items': ref} if field_type_code(kind, field) == 'oa' else ref
    if normalize_kind(kind) == 'choice' and field == 'addons':
        return {'type': 'array', 'items': {'oneOf': [{'$ref': '#/$defs/addon'}, {'$ref': '#/$defs/selectable_addon'}]}}
    return _schema_for_code(field_type_code(kind, field) or '')


def _schema_definition(kind: str, additional_properties: bool, *, mode: str = 'patch') -> dict[str, Any]:
    catalog_kind = normalize_kind(kind)
    properties = {field: _schema_for_field(catalog_kind, field) for field in FIELD_CATALOG[catalog_kind]}
    if mode == 'native':
        for field, code in WIRE_COMPAT_FIELDS.get(catalog_kind, {}).items():
            properties[field] = {
                **_schema_for_code(code),
                'deprecated': True,
                'description': f'ICC Plus 2.10.7 serialized compatibility spelling; author new data as {WIRE_COMPAT_ALIASES[catalog_kind][field]}.',
            }
    out: dict[str, Any] = {
        'type': 'object',
        'properties': properties,
        'additionalProperties': additional_properties,
    }
    if mode == 'native':
        required = [field for field in required_fields(catalog_kind) if field in FIELD_CATALOG[catalog_kind]]
        if required:
            out['required'] = required
    return out


def _schema_dependencies(kind: str) -> set[str]:
    root = normalize_kind(kind)
    seen: set[str] = set()
    todo = [root]
    while todo:
        current = todo.pop()
        for (owner, field), nested in _NESTED_TYPES.items():
            if owner == current and nested not in seen and nested != root:
                seen.add(nested); todo.append(nested)
        if current == 'choice':
            for nested in ('addon', 'selectable_addon'):
                if nested not in seen and nested != root:
                    seen.add(nested); todo.append(nested)
    return seen


def _schema_for_code(code: str) -> dict[str, Any]:
    if code == 'b':
        return {'type': 'boolean'}
    if code == 'n':
        return {'type': 'number'}
    if code == 's':
        return {'type': 'string'}
    if code == 'sa':
        return {'type': 'array', 'items': {'type': 'string'}}
    if code == 'na':
        return {'type': 'array', 'items': {'type': 'number'}}
    if code == 'ba':
        return {'type': 'array', 'items': {'type': 'boolean'}}
    if code == 'ssa':
        return {'type': 'array', 'items': {'type': 'array', 'items': {'type': 'string'}}}
    if code == 'ns':
        return {'type': ['number', 'string']}
    if code == 'o':
        return {'type': 'object'}
    if code == 'oa':
        return {'type': 'array', 'items': {'type': 'object'}}
    if code == 'true':
        return {'const': True}
    if code == 'false':
        return {'const': False}
    return {}


def json_schema_for_kind(kind: str, *, additional_properties: bool = False, mode: str = 'patch') -> dict[str, Any]:
    catalog_kind = normalize_kind(kind)
    if catalog_kind not in FIELD_CATALOG:
        raise ValueError(f'unknown field catalog kind: {kind}')
    if mode not in {'patch', 'native'}:
        raise ValueError(f'unknown schema mode: {mode}')
    root = _schema_definition(catalog_kind, additional_properties, mode=mode)
    root.update({
        '$schema': 'https://json-schema.org/draft/2020-12/schema',
        '$id': f'https://iccplus.local/schema/native/{catalog_kind}.schema.json',
        'title': f'ICC Plus 2.10.7 {catalog_kind} native fields',
        'description': f'Field/value shapes transcribed from {SOURCE_FILE} at {SOURCE_COMMIT}. Mode: {mode}.',
        'x-iccplus-mode': mode,
        'x-iccplus-source': {
            'version': ICC_PLUS_VERSION,
            'repository': SOURCE_REPOSITORY,
            'commit': SOURCE_COMMIT,
            'file': SOURCE_FILE,
        },
    })
    if mode == 'native' and WIRE_COMPAT_ALIASES.get(catalog_kind):
        root['x-iccplus-wire-compat-aliases'] = WIRE_COMPAT_ALIASES[catalog_kind]
    deps = _schema_dependencies(catalog_kind)
    if deps:
        root['$defs'] = {dep: _schema_definition(dep, additional_properties, mode=mode) for dep in sorted(deps)}
    return root


def _type_name(kind: str, suffix: str) -> str:
    return ''.join(part.capitalize() for part in kind.split('_')) + suffix


def _declaration_kinds(kinds: list[str] | None) -> list[str]:
    """Return requested declarations plus every named type they reference.

    A narrowed declaration export must still compile on its own.  Dependencies
    are emitted before the requested roots so ``types --kind choice`` does not
    leave dangling ``ScoreNative`` or ``RequirementNative`` references.
    """
    if kinds is None:
        return [k for k in FIELD_CATALOG if k != 'backpack_row']

    roots = list(dict.fromkeys(kinds))
    for kind in roots:
        if normalize_kind(kind) not in FIELD_CATALOG:
            raise ValueError(f'unknown field catalog kind: {kind}')

    ordered: list[str] = []
    emitted: set[str] = set()
    visiting: set[str] = set()

    def visit(kind: str, *, root_name: str | None = None) -> None:
        catalog_kind = normalize_kind(kind)
        key = root_name or catalog_kind
        if key in emitted:
            return
        if catalog_kind in visiting:
            return
        visiting.add(catalog_kind)
        for dep in sorted(_schema_dependencies(catalog_kind)):
            visit(dep)
        visiting.discard(catalog_kind)
        if key not in emitted:
            ordered.append(key)
            emitted.add(key)

    for root in roots:
        # Keep the public alias name for an explicitly requested backpack_row,
        # but resolve all of its dependencies from the native Row shape.
        visit(root, root_name=root)
    return ordered


def typescript_declarations(kinds: list[str] | None = None, *, mode: str = 'patch') -> str:
    if mode not in {'patch', 'native'}:
        raise ValueError(f'unknown declaration mode: {mode}')
    chosen = _declaration_kinds(kinds)
    suffix = 'Patch' if mode == 'patch' else 'Native'
    lines = [
        '// Generated by iccplus-local from the pinned ICC Plus 2.10.7 field catalog.',
        f'// Source: {SOURCE_REPOSITORY} {SOURCE_COMMIT} {SOURCE_FILE}',
        f'// Mode: {mode}',
        '',
    ]
    for kind in chosen:
        catalog_kind = normalize_kind(kind)
        lines.append(f'export interface {_type_name(kind, suffix)} {{')
        required = set(required_fields(catalog_kind)) if mode == 'native' else set()
        for field in FIELD_CATALOG[catalog_kind]:
            optional = '' if field in required else '?'
            lines.append(f'  {field}{optional}: {_ts_type_for_field(catalog_kind, field, suffix=suffix)};')
        if mode == 'native':
            for field, code in WIRE_COMPAT_FIELDS.get(catalog_kind, {}).items():
                alias = WIRE_COMPAT_ALIASES[catalog_kind][field]
                lines.append(f'  /** @deprecated 2.10.7 wire spelling; author new data as {alias}. */')
                lines.append(f'  {field}?: {_TYPE_INFO[code].typescript};')
        lines.extend(['}', ''])
    return '\n'.join(lines)


def _python_type(code: str) -> str:
    return {
        'b': 'bool', 'n': 'float', 's': 'str', 'sa': 'list[str]', 'na': 'list[float]',
        'ba': 'list[bool]', 'ssa': 'list[list[str]]', 'ns': 'float | str',
        'o': 'dict[str, Any]', 'oa': 'list[dict[str, Any]]', 'true': 'Literal[True]',
        'false': 'Literal[False]',
    }.get(code, 'Any')


def python_typeddicts(kinds: list[str] | None = None, *, mode: str = 'patch') -> str:
    if mode not in {'patch', 'native'}:
        raise ValueError(f'unknown declaration mode: {mode}')
    chosen = _declaration_kinds(kinds)
    suffix = 'Patch' if mode == 'patch' else 'Native'
    lines = [
        'from __future__ import annotations',
        'from typing import Any, Literal, NotRequired, TypedDict',
        '',
        f'# Generated from {SOURCE_REPOSITORY} {SOURCE_COMMIT} {SOURCE_FILE}',
        f'# Mode: {mode}',
        '',
    ]
    for kind in chosen:
        catalog_kind = normalize_kind(kind)
        required = set(required_fields(catalog_kind)) if mode == 'native' else set()
        total = 'True' if mode == 'native' else 'False'
        lines.append(f'class {_type_name(kind, suffix)}(TypedDict, total={total}):')
        fields = FIELD_CATALOG[catalog_kind]
        if not fields:
            lines.append('    pass')
        for field in fields:
            typ = _python_type_for_field(catalog_kind, field, suffix=suffix)
            if mode == 'native' and field not in required:
                typ = f'NotRequired[{typ}]'
            lines.append(f'    {field}: {typ}')
        if mode == 'native':
            for field, code in WIRE_COMPAT_FIELDS.get(catalog_kind, {}).items():
                lines.append(f'    {field}: NotRequired[{_python_type(code)}]')
        lines.append('')
    return '\n'.join(lines)

def metadata_report() -> dict[str, Any]:
    return {
        'source': {
            'icc_plus_version': ICC_PLUS_VERSION,
            'repository': SOURCE_REPOSITORY,
            'commit': SOURCE_COMMIT,
            'file': SOURCE_FILE,
        },
        'kinds': {kind: len(fields) for kind, fields in FIELD_CATALOG.items()},
        'typed_fields': {kind: len(FIELD_TYPE_CODES.get(normalize_kind(kind), {})) for kind in FIELD_CATALOG},
    }
