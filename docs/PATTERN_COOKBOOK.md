# ICC Plus scripted pattern cookbook

Use these patterns when generating or repairing `project.json`. Prefer the generation shorthands for common rules. Use native ICC Plus fields for uncommon behavior so the project stays close to the Viewer format.

Before generating, run:

```bash
iccplus-local reference capabilities --brief
iccplus-local template entity row
iccplus-local template entity choice
```

After a change, use the write receipt plus the smallest `play` audit that covers the mechanic. Use `project validate` for the final Creator-complete check.

## Pick one or pick N

A Row selection limit is the simplest local pick rule.

```json
{
  "id": "row_origin",
  "title": "Origin",
  "pick": 1,
  "choices": [
    {"id": "origin_city", "title": "City"},
    {"id": "origin_rural", "title": "Rural"}
  ]
}
```

`pick` is generation shorthand for native `allowedChoices`. Use a larger integer for Pick N. Test what should happen when a player selects another Choice at the cap because ICC Plus can replace an older selection.

## Point budget

Define a Point Type once, then use `costs` on Choices.

```json
{
  "pointTypes": [
    {"id": "budget", "name": "Budget", "startingSum": 20, "belowZeroNotAllowed": true}
  ],
  "rows": [
    {
      "id": "row_powers",
      "title": "Powers",
      "choices": [
        {"id": "power_flight", "title": "Flight", "costs": {"budget": 4}},
        {"id": "power_healing", "title": "Healing", "costs": {"budget": 6}}
      ]
    }
  ]
}
```

A positive Score is normally a cost. A negative value grants points.

## Simple prerequisite

```json
{"id":"upgrade_two","title":"Tier Two","requires":["upgrade_one"]}
```

This expands to an ICC Plus `id` Requirement with `required: true`.

## Mutual exclusion

```json
{"id":"path_sun","title":"Sun","excludes":["path_moon"]}
```

If the exclusion is meant to be symmetric, put the opposite exclusion on `path_moon` too. Do not assume one negative Requirement automatically creates a two-way rule.

## Hide a Row until a Choice is selected

```json
{
  "id": "row_secret",
  "title": "Secret powers",
  "hidden_until": "unlock_secret",
  "choices": []
}
```

Rows disappear while their Requirements fail in the target Viewer.

For an existing project:

```json
{"op":"gate","source":"unlock_secret","targets":["row_secret"]}
```

## Hide several Choices until one Choice is selected

```json
{"op":"gate","source":"choose_magic","targets":["spell_fire","spell_ice","spell_wind"]}
```

For Choice targets, `gate` adds the Requirement and the ICC Plus unmet-requirement visibility filter. This differs from merely making a Choice invalid but still visible.

## Hide parts of Choices in target Rows

This is ICC Plus "Hide the Contents of Choices", not a prerequisite gate.

```json
{
  "op": "hide_contents",
  "source": "mystery_mode",
  "rows": ["row_rewards"],
  "contents": ["choice_title", "choice_image", "choice_text", "choice_score"]
}
```

Use `clear_hide_contents` to remove the effect. See `VISIBILITY_AND_HIDING.md` for all ten content codes.

## Selectable Addon

```json
{
  "id": "weapon_sword",
  "title": "Sword",
  "addons": [
    {
      "id": "weapon_sword_flame",
      "isSelectable": true,
      "title": "Flaming",
      "costs": {"budget": 2}
    }
  ]
}
```

The generator writes the native `parentId`. The identity checker covers the Addon and its nested Scores and Requirements.

## Non-selectable Addon

```json
{
  "id": "weapon_sword",
  "title": "Sword",
  "addons": [
    {"id":"","title":"Note","text":"A family heirloom."}
  ]
}
```

Use this for attached explanation or display content that should not create another selectable build item.

## Repeated purchase

Use native ICC Plus fields for multi-select because projects vary in how the counter should behave.

```json
{
  "id": "resource_drone",
  "title": "Drone",
  "isSelectableMultiple": true,
  "isMultipleUseVariable": true,
  "allowSelectByClick": true,
  "multipleUseVariable": 0,
  "numMultipleTimesPluss": 10,
  "numMultipleTimesMinus": 0,
  "useSlider": true,
  "scores": [
    {"idx":"score_drone_budget","id":"budget","value":1,"multiplyByTimes":true}
  ]
}
```

Test increasing, decreasing, limits, points, zero crossing when negative counts are allowed, Row-cap displacement, and save/restore. `isSelectableMultiple` without `isMultipleUseVariable` or `multipleScoreId` is not a working repeat counter in ICC Plus 2.10.6.

## Force another Choice active

Generation shorthand:

```json
{"id":"package_a","activate":["included_item"]}
```

Native ICC Plus supports comma-separated target IDs through `activateThisChoice`. Forced activation has ownership bookkeeping, so use `session` for ordered select/deselect tests.

## Force another Choice inactive

```json
{"id":"path_a","deactivate":["path_b"]}
```

Use this when selecting A should actively remove B. Use an exclusion Requirement instead when B should simply be unavailable.

## Boolean Variable

Project state:

```json
{"variables":[{"id":"var_oath","isTrue":false}]}
```

Choice effect:

```json
{
  "id":"take_oath",
  "isChangeVariables":true,
  "changedVariables":["var_oath"],
  "changeType":"true"
}
```

Use a Variable when an action must store state that cannot be expressed cleanly by selected Choice Requirements.

## Word replacement

Project state:

```json
{"words":[{"id":"word_name","replaceText":"Traveler"}]}
```

Noninteractive Choice change:

```json
{
  "textfieldIsOn": true,
  "idOfTheTextfieldWord": "word_name",
  "wordChangeSelect": "Alice",
  "wordChangeDeselect": "Traveler"
}
```

Dialog-driven text entry belongs in Viewer testing.

## Increase or decrease a Row selection cap

```json
{
  "id":"extra_companion_slot",
  "addToAllowChoice":true,
  "idOfAllowChoice":["row_companions"],
  "numbAddToAllowChoice":1
}
```

A negative value reduces the cap. Use a persistent `session` when the effect may later be removed.

## Multiply, divide, or set points

Multiply:

```json
{"multiplyPointtypeIsOn":true,"pointTypeToMultiply":["budget"],"multiplyWithThis":2}
```

Divide:

```json
{"dividePointtypeIsOn":true,"pointTypeToDivide":["budget"],"divideWithThis":2}
```

Set:

```json
{"setPointtypeIsOn":true,"pointTypeToSet":["budget"],"setWithThis":"10"}
```

The headless runner models ordinary reversible use. Check `COVERAGE.md` before relying on more complicated stacks.

## Ordinary Group

Generation can use the Group side:

```json
{
  "groups": [
    {"id":"group_magic","name":"Magic","elements":["spell_fire","spell_ice"],"rowElements":["row_magic"]}
  ]
}
```

Or use the member side:

```json
{"id":"spell_fire","groups":["group_magic"]}
```

Generation and `normalize` reconcile both forms. For edits, prefer:

```json
{"op":"group_members","group":"group_magic","members":["row_magic","spell_fire","spell_ice"]}
```

## Design Group

Use the bulk helper so native membership arrays stay synchronized:

```json
{"op":"design_group_members","group":"design_magic","members":["spell_fire","spell_ice"]}
```

The helper handles normal and Backpack member arrays. A normal Group can also be a design-group member through ICC Plus `designGroups`.

## Result Row

A basic result Row uses native fields:

```json
{
  "id":"row_result",
  "title":"Your build",
  "isResultRow":true,
  "resultGroupId":""
}
```

With an empty `resultGroupId`, current Viewer behavior gathers selected result-eligible Choices. Use a Group ID when the result should be scoped. Test result presentation in the Viewer.

## Group Row

```json
{
  "id":"row_group_view",
  "title":"Magic choices",
  "isGroupRow":true,
  "resultGroupId":"group_magic"
}
```

Use a Group Row for group-driven display, not as a substitute for ordinary project organization.

## Information Row

```json
{"id":"row_rules","title":"Rules","isInfoRow":true,"choices":[]}
```

Use an information Row for text that is not a player selection.

## Button Row

Button behavior has several native modes. Start from the exact installed factory:

```bash
iccplus-local template entity row
```

Common fields include `isButtonRow`, `buttonType`, `buttonId`, `buttonText`, `buttonRandom`, `buttonRandomNumber`, `isWeightedRandom`, `allowActivateUnselectable`, `btnPointAddon`, `pointTypeRandom`, `randomMin`, `randomMax`, `onlyUnselectedChoices`, and `onlyIfNoChoices`.

Button and random behavior should receive a target Viewer test when the project depends on it.

## Discount targets

Use native fields:

```json
{
  "discountOther":true,
  "discountChoices":["perk_a","perk_b"],
  "discountPointTypes":["budget"],
  "discountOperator":"-",
  "discountValue":1,
  "stackableDiscount":false
}
```

The local validator checks references. Complex discount stacking still needs Viewer verification.

## Duplicate a Row

```json
{
  "duplicateRow":true,
  "duplicateRowId":"row_source",
  "duplicateRowPlace":"row_destination"
}
```

The Viewer can suffix IDs in duplicated Rows. Treat dynamic duplication as a Viewer-heavy feature.

## Choice visibility states

ICC Plus styling can hide a Choice in selected, unmet-requirement, or unselected state with:

```text
selFilterVisibleIsOn
reqFilterVisibleIsOn
unselFilterVisibleIsOn
```

For ordinary hidden-until logic, use `hidden_until` or `gate` instead of setting these fields manually.

## Sound effects and BGM

Choice SFX fields include `useSfx`, `sfxIdOnSelect`, `sfxIdOnDeselect`, `sfxOnSelect`, and `sfxOnDeselect`.

BGM fields include `setBgmIsOn`, `bgmId`, fade settings, loop settings, muting, and audio URL settings. Audio playback is a Viewer test.

## Template and width changes

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

Keep presentation changes native. They are easier to compare with the target Viewer source that way.

## Safe bulk repair loop

A reliable scripted repair cycle is:

```bash
iccplus-local inspect project.json @inspect.json
iccplus-local rules project.json @repair-rules.json
iccplus-local project validate project.json
```

If a batch operation or static validation fails, `apply` leaves the output file unchanged. Use `--allow-invalid` only for an intentional invalid intermediate file.

## Continuing a playtest

Do not rebuild a later state from selected IDs. Keep the complete runtime state in a private continuation file:

```bash
iccplus-local play project.json --state play.json --select origin_city
iccplus-local play project.json --state play.json --select power_flight
```

`play` resumes and rewrites the state file automatically. The file contains hidden bookkeeping needed for correct reversal and continuation, so keep it outside the LM player context. Use `state-check project.json play.json` if the file may have been edited, truncated, copied from another project, or otherwise damaged. If it cannot be recovered, `play project.json --state play.json --reset` replaces it without loading the bad file.
