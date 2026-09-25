# ICC Plus effect recipes

Use `EFFECTS_FORMAT.md` for the `effects` operation syntax. This file remains the native-field reference and records cases where direct ICC Plus fields are useful.

These recipes use the operation system or native ICC Plus fields through `update` and `values`.

## Cost or grant points

A positive Score value acts as a cost under normal ICC Plus selection behavior. A negative value grants points.

Operation form:

```json
{"op":"score_many","target":"perk_fast","point":"budget","value":3}
```

Native form:

```json
{
  "scores":[
    {"idx":"score_perk_fast_budget","id":"budget","value":3}
  ]
}
```

## Require or exclude another Choice

Operation form:

```json
{"op":"require","source":"base_power","target":"perk_fast"}
{"op":"exclude","source":"rival_path","target":"perk_fast"}
```

Native requirement:

```json
{
  "type":"id",
  "required":true,
  "reqId":"base_power"
}
```

Set `required` to `false` for an exclusion.

## Hide a Row or Choice until selected

```json
{"op":"gate","source":"unlock_choice","targets":["row_secret","secret_a","secret_b"]}
```

Use this for staged sections. Use `hide_contents` only when the source Choice should redact parts of Choices in target Rows.

## Force another Choice on or off

Operation form:

```json
{
  "op":"effects",
  "target":"controller",
  "effects": {
    "activate":["free_item"],
    "deactivate":["incompatible_item"]
  }
}
```

Native fields:

```json
{
  "activateOtherChoice":true,
  "activateThisChoice":"free_item",
  "deactivateOtherChoice":true,
  "deactivateThisChoice":"incompatible_item"
}
```

Multiple IDs use a comma-separated native string. The Viewer parses those IDs literally, without trimming whitespace. Repeated targets and targets reached again through Groups are not deduplicated. `/ON#` count suffixes use JavaScript `parseInt` behavior. Ordinary self-deactivation is deferred until the selection finishes; explicit positive repeat-count self-deactivation decrements a repeatable Choice.

## Multiple selection

Common native fields:

```json
{
  "isSelectableMultiple":true,
  "isMultipleUseVariable":true,
  "allowSelectByClick":true,
  "multipleUseVariable":0,
  "numMultipleTimesPluss":5,
  "numMultipleTimesMinus":0,
  "useSlider":true
}
```

Test increase, decrease, score multiplication, limits, and save/load behavior. Also confirm which native repeat mode is active. `isMultipleUseVariable` is the signed variable-count mode. `multipleScoreId` is the point-backed mode. `isSelectableMultiple` without either mode is a Viewer no-op and should normally be treated as an authoring error. Negative variable counts are legal when the minus limit permits them. `addToAllowChoice` applies on every repeat step, while ordinary point multiply/divide/set effects do not.

## Adjust a Row selection cap

```json
{
  "addToAllowChoice":true,
  "idOfAllowChoice":["row_companions"],
  "numbAddToAllowChoice":1
}
```

The headless runner models this effect and saves its reversible runtime bookkeeping. On a repeatable Choice the Viewer applies the Row-limit change on every increment and decrement.

## Change Variables

```json
{
  "isChangeVariables":true,
  "changedVariables":["var_oath"],
  "changeType":"true"
}
```

Use the target Viewer source and a local runtime test when using less common `changeType` values.

## Multiply, divide, or set Point Types

Multiply:

```json
{
  "multiplyPointtypeIsOn":true,
  "pointTypeToMultiply":["budget"],
  "multiplyWithThis":2
}
```

Divide:

```json
{
  "dividePointtypeIsOn":true,
  "pointTypeToDivide":["budget"],
  "divideWithThis":2
}
```

Set:

```json
{
  "setPointtypeIsOn":true,
  "pointTypeToSet":["budget"],
  "setWithThis":"10"
}
```

The local simulator models ordinary reversible use. The Viewer applies linked activation/deactivation and Requirement cleanup before these transforms. The affordability guard runs before a later set transform, so `belowZeroNotAllowed` does not retroactively reject a negative value created by that set. These transforms do not run on repeat-counter steps. See `COVERAGE.md` for the boundary.

## Change a Word

```json
{
  "textfieldIsOn":true,
  "idOfTheTextfieldWord":"word_name",
  "wordChangeSelect":"Alice",
  "wordChangeDeselect":""
}
```

Interactive prompt and dialog behavior still belongs in Viewer testing.

## Discount other content

Important native fields include:

```json
{
  "discountOther":true,
  "discountChoices":["perk_a","perk_b"],
  "discountRows":[],
  "discountGroups":[],
  "discountPointTypes":["budget"],
  "discountOperator":"-",
  "discountValue":1,
  "stackableDiscount":false
}
```

Discount stacking has more runtime detail than the current headless runner models exactly. Validate references locally and test final discount behavior in the Viewer.

## Duplicate a Row

```json
{
  "duplicateRow":true,
  "duplicateRowId":"row_source",
  "duplicateRowPlace":"row_destination"
}
```

ICC Plus can suffix IDs inside duplicated Rows. Treat this as browser-heavy behavior for final testing.

## Change template or width

```json
{
  "changeTemplates":true,
  "changeTemplatesList":"row_a,choice_b",
  "changeToThisTemplate":2,
  "changeWidth":true,
  "changeWidthList":"row_a,choice_b",
  "changeToThisWidth":"col-md-6"
}
```

## Sound and music

Choice sound effects use `useSfx`, `sfxIdOnSelect`, `sfxIdOnDeselect`, `sfxOnSelect`, and `sfxOnDeselect`.

BGM fields include `setBgmIsOn`, `bgmId`, fade settings, looping, muting, and audio URL settings.

Audio playback is a Viewer test.

## Random activation

Native fields include `isActivateRandom`, `numActivateRandom`, `activateThisChoice`, and `randomWeight` on weighted Choices.

Random forced activation pools are not exact in the current headless simulator. Keep deterministic local tests around the surrounding rules, then verify the random effect in the Viewer.
