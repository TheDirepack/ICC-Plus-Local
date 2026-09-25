# Entity formats

This file describes the JSON shapes most often produced or edited by scripts. Use `iccplus-local template KIND` to print the current default shape from the installed tool.

## Identity summary

| Entity | Identity field | Parent |
| --- | --- | --- |
| Row | `id` | project |
| Backpack Row | `id` | project |
| Choice | `id` | Row |
| Addon | structural `id: ""` | Choice |
| selectable Addon | `id` | Choice |
| Score | `idx` | Choice or selectable Addon |
| Requirement | structural `id: ""` | any Requirement-bearing entity |
| Point Type | `id` | project |
| Variable | `id` | project |
| Word | `id` | project |
| Group | `id` | project |
| Global Requirement | `id` | project |
| Row design group | `id` | project |
| Choice design group | `id` | project |
| Sound Effect | `id` | project |
| Category | `(type, idx)` | project |

Score `id` is a Point Type reference, not the Score identity.

## Row

Minimal generated form:

```json
{
  "id": "row_origin",
  "title": "Origin",
  "titleText": "Choose one.",
  "pick": 1,
  "choices": []
}
```

Native output uses `objects` and `allowedChoices`.

Useful native fields include `template`, `objectWidth`, `rowJustify`, `requireds`, `groups`, `rowDesignGroups`, `isInfoRow`, `isResultRow`, `resultGroupId`, button fields, random-row fields, and private styling fields.

A Row with unmet Requirements is hidden by the Viewer. `hidden_until` is therefore a small shorthand for a Row Requirement.

## Choice

```json
{
  "id": "origin_human",
  "title": "Human",
  "text": "",
  "image": "",
  "costs": {"budget": 2},
  "requires": [],
  "excludes": [],
  "addons": [],
  "groups": []
}
```

The generator expands common shortcuts and preserves native Choice function fields such as activation, discount, variable, point, audio, and Row-change effects.

## Addon

A non-selectable Addon is display content attached to a Choice. The Creator factory uses an empty structural ID:

```json
{
  "id": "",
  "title": "Note",
  "text": "Extra information",
  "requireds": []
}
```

A selectable Addon sets `isSelectable`:

```json
{
  "id": "addon_sword_sharp",
  "isSelectable": true,
  "title": "Sharpened",
  "costs": {"budget": 1},
  "groups": []
}
```

When an Addon becomes selectable, ICC Plus assigns a real identity and adds the eager selectable fields, including `isSelectable: true` and `scores: []`. Other selectable fields remain lazy. The CLI writes `parentId` for selectable Addons when it builds them.

## Score

```json
{
  "idx": "score_fast_budget",
  "id": "budget",
  "value": 2,
  "requireds": [],
  "showScore": true
}
```

`idx` is unique project-wide. `id` names the Point Type. Under ordinary ICC Plus selection behavior, a positive value is a cost because it is subtracted from the Point Type on selection. A negative value grants points.

Scores can have their own Requirements, random values, expressions, discounts, display settings, and recalculation settings.

## Requirement

```json
{
  "id": "",
  "type": "id",
  "required": true,
  "reqId": "origin_human",
  "requireds": [],
  "orRequireds": []
}
```

Nested `requireds` control when the parent Requirement participates. `orRequireds` are used by `type: "or"`.

The blank Requirement `id` is source-compatible structure, not a missing project identity.

See `REQUIREMENT_RECIPES.md` for every locally modeled Requirement type.

## Point Type

```json
{
  "id": "budget",
  "name": "Budget",
  "startingSum": 20,
  "belowZeroNotAllowed": true
}
```

Other native fields control Point Bar visibility, icons, colors, floats, decimal places, categories, and Score text.

## Variable

```json
{
  "id": "var_oath",
  "isTrue": false
}
```

Variables can satisfy `id` Requirements and can be changed by Choice function fields.

## Word

```json
{
  "id": "word_name",
  "replaceText": "Alex"
}
```

Words support text replacement and `word` Requirements.

## Group

```json
{
  "id": "group_fire",
  "name": "Fire choices",
  "elements": ["spell_fireball"],
  "rowElements": []
}
```

Use a Group when ICC Plus behavior acts on a set of Choices or Rows. Do not duplicate the same member in the array. The validator reports repeated references.

## Global Requirement

```json
{
  "id": "greq_can_cast",
  "name": "Can cast",
  "requireds": [
    {"type": "id", "required": true, "reqId": "origin_mage"}
  ]
}
```

Reference it with a Requirement whose `type` is `gid` and `reqId` is the Global Requirement ID.

## Design groups

Row design group:

```json
{
  "id": "rowdesign_dark",
  "name": "Dark Rows",
  "elements": ["row_magic"],
  "backpackElements": [],
  "groupElements": [],
  "styling": {}
}
```

Choice design groups use the same general structure and target Choices.

## Sound Effect

```json
{
  "id": "sfx_select_magic",
  "name": "Magic select",
  "audio": "assets/magic.ogg",
  "volume": 1,
  "pitch": 1,
  "requireds": [],
  "groups": []
}
```

Playback belongs to Viewer testing.

## Category

ICC Plus categories do not use a string ID in the reviewed 2.10.7 type. Their identity is `(type, idx)`:

```json
{
  "idx": 0,
  "name": "Mechanics",
  "type": "choice"
}
```

The CLI checks that composite identity for uniqueness.
