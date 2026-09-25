# ICC Plus field reference for scripted work

This is a compact field catalog for the ICC Plus 2.10.7 source snapshot used by this release. It is not a replacement for the official Viewer source. It exists so a generator can find the native field names without opening the Creator UI.

## Requirement

Core fields:

```text
id
required
requireds
orRequired
orRequireds
type
reqId
reqId1
reqId2
reqId3
reqPoints
operator
showRequired
hideRequired
hideRequired2
beforeText
afterText
orNum
selNum
selFromOperators
selGroups
selRows
more
customTextIsOn
customText
```

Common `type` values modeled locally are `id`, `points`, `or`, `pointCompare`, `selFromGroups`, `selFromRows`, `selFromWhole`, `gid`, and `word`.

## Score

```text
idx
id
value
type
requireds
beforeText
afterText
showScore
hideValue
removeSpace
isRandom
minValue
maxValue
setValue
isNotRecalculatable
isNotDiscountable
discounts
discountIsOn
discountShow
discountBeforeText
discountAfterText
discountScore
multiplyByTimes
displayMulScore
replaceText
useExpression
expValue
expMinValue
expMaxValue
```

`idx` is the Score identity. `id` points to the Point Type.

## Choice and selectable Addon function fields

Selection and state:

```text
hideMultipleCounter
allowSelectByClick
hideCounterUntilSelect
isSelectableMultiple
isMultipleUseVariable
multipleScoreId
numMultipleTimesMinus
numMultipleTimesPluss
isNotSelectable
selectOnce
notDeselectedByClean
isNotResult
cleanACtivatedOnSelect
isAllowDeselect
activateAfterReset
isNotActiveUnselectable
isAutoActive
isCountDisabled
deselectWhenNoAddon
```

`isSelectableMultiple` only enables the repeatable UI path. A working counter also needs a mode. `isMultipleUseVariable: true` uses the signed `multipleUseVariable` count. `multipleScoreId` uses a Point Type-backed count. If neither mode is present, ICC Plus 2.10.7 leaves the counter inert.

Activation:

```text
activateOtherChoice
isActivateRandom
numActivateRandom
activateThisChoice
deactivateOtherChoice
deactivateThisChoice
randomWeight
```

Activation and deactivation target strings are parsed with source quirks. Comma-separated IDs are not trimmed or deduplicated, `/ON#` counts use JavaScript numeric-prefix parsing, and ordinary self-deactivation is deferred until the current selection finishes.

Discounts:

```text
discountOther
discountLowLimitIsOn
discountLowLimit
discountShow
replaceScoreText
hideScoreValue
hideScoreIcon
discountBeforeText
discountAfterText
isDisChoices
discountRows
discountChoices
discountGroups
discountPointTypes
discountOperator
discountValue
stackableDiscount
useDiscountCount
discountCount
numDiscountChoices
```

Row and content changes:

```text
duplicateRow
dRowAddSufReq
dRowAddSufFunc
duplicateRowId
duplicateRowPlace
isContentHidden
hiddenContentsRow
hiddenContentsType
addToAllowChoice
idOfAllowChoice
numbAddToAllowChoice
showAllAddons
```

Template, width, and navigation:

```text
changeTemplates
changeAddonTemplate
changeTemplatesList
changeToThisTemplate
changeWidth
changeWidthList
changeToThisWidth
scrollToRow
scrollToObject
scrollObjectId
scrollRowId
```

Point changes:

```text
multiplyPointtypeIsOn
pointTypeToMultiply
multiplyWithThis
multiplyPointtypeIsId
dividePointtypeIsOn
pointTypeToDivide
divideWithThis
setPointtypeIsOn
pointTypeToSet
setWithThis
```

Variables and Words:

```text
isChangeVariables
changedVariables
changeType
textfieldIsOn
customTextfieldIsOn
idOfTheTextfieldWord
wordPromptText
wordChangeSelect
wordChangeDeselect
confirmIsOn
```

Audio and transition fields:

```text
setBgmIsOn
bgmId
bgmFadeIn
bgmFadeOut
bgmFadeInSec
bgmFadeOutSec
bgmNoLoop
muteBgm
useAudioURL
isFadeTransition
fadeTransitionColor
fadeTransitionTime
fadeInTransitionTime
fadeOutTransitionTime
useSfx
sfxIdOnSelect
sfxIdOnDeselect
sfxOnSelect
sfxOnDeselect
```

Timing and search:

```text
isSelectDelayed
selectDelayTime
isDeselectDelayed
deselectDelayTime
isNotSearchable
```

## Choice

Important data fields:

```text
id
index
title
text
debugTitle
image
template
objectWidth
isActive
multipleUseVariable
selectedThisManyTimesProp
requireds
addons
scores
groups
objectDesignGroups
linkedObjects
addonJustify
styling
```

Private styling switches include `privateFilterIsOn`, `privateTextIsOn`, `privateObjectImageIsOn`, `privateObjectIsOn`, `privateAddonImageIsOn`, `privateAddonIsOn`, `privateBackgroundIsOn`, and `privateMultiChoiceIsOn`.

## Addon

Base Addon fields:

```text
id
title
text
template
image
requireds
parentId
showAddon
hideAddon
skipIndex
defaultTemplate
addonWidth
```

A selectable Addon adds:

```text
isSelectable: true
scores
groups
multipleUseVariable
isActive
deselectParent
countAsChoice
```

and may use the Choice function fields above.

## Row

Core fields:

```text
id
index
title
titleText
debugTitle
objectWidth
image
template
allowedChoices
currentChoices
requireds
objects
rowDesignGroups
groups
rowJustify
```

Mode and result fields:

```text
isBackpack
isButtonRow
buttonType
buttonId
buttonText
buttonRandom
buttonRandomNumber
isWeightedRandom
allowActivateUnselectable
isResultRow
resultGroupId
isInfoRow
isGroupRow
```

Layout and display fields include `defaultAspectWidth`, `defaultAspectHeight`, `overrideWidth`, `preserveWidth`, `choicesShareTemplate`, `defaultTemplate`, `defaultWidth`, removal flags for object and Addon content, and Row private styling fields.

Button random Point fields include `btnPointAddon`, `pointTypeRandom`, `randomMin`, `randomMax`, `onlyUnselectedChoices`, and `onlyIfNoChoices`.

## Point Type

```text
id
name
startingSum
initValue
activatedId
beforeText
afterText
belowZeroNotAllowed
isNotShownPointBar
isNotShownObjects
allowFloat
decimalPlaces
category
useScoreText
scoreBeforeText
scoreAfterText
```

Point Types also support positive and negative colors, images, icons, and placement fields.

## Variable

```text
id
isTrue
category
```

## Word

```text
id
replaceText
category
```

## Group

```text
id
name
category
elements
rowElements
designGroups
```

The CLI normalizer rebuilds `elements` from the selectable-side `groups` arrays.

## Global Requirement

```text
id
name
category
requireds
```

Global Requirements may reference other Global Requirements. The validator checks cycles.

## Design Groups

Row and Choice Design Groups contain an ID, name, activation ID, member arrays, category, private styling switches, and a `styling` object.

## Sound Effect

```text
id
name
audio
volume
pitch
isDefault
onSelected
onDeselected
requireds
groups
```

## Viewer configuration

Core fields are:

```text
title
favicon
loadingType
loadingBgColor
loadingBgImage
loadingCircleColor
loadingTrackColor
loadingText
loadingTextColor
loadingTextFont
loadingTextShadow
useSeparateImages
useLocalViewer
```

`useSeparateImages` and `useLocalViewer` are mutually exclusive export modes. The validator reports an error if both are true.

## Styling visibility fields

The fields most useful for scripted reveal logic are:

```text
selFilterVisibleIsOn
reqFilterVisibleIsOn
unselFilterVisibleIsOn
```

For a hidden-until Choice, the CLI sets `privateFilterIsOn: true` and `styling.reqFilterVisibleIsOn: true` together with an ordinary Requirement.

The Styling object also supports filter, color, border, image, text, background, Row, Addon, multi-choice, point-bar, and Backpack settings. Use raw ICC Plus fields when a design pass needs exact styling control.
