# Play structure in ICC Plus Local 0.10.0rc11

This file describes the player-visible hierarchy returned by `iccplus-local play`.

## The main rule

Rows, direct Choices, and Addons are separate entity types. The rc11 player view exposes each type separately and includes explicit links between them. New automation should use those links instead of reconstructing hierarchy from nested JSON.

The response still includes the older `rows[].choices` compatibility field. It is not the preferred representation.

## Top-level indexes

A compact player view includes ordered indexes for every visible entity type:

```json
{
  "row_ids": ["row_a", "row_b"],
  "choice_ids": ["choice_a", "choice_b", "choice_c"],
  "addon_ids": ["info_a", "addon_a"],
  "selectable_addon_ids": ["addon_a"],
  "informational_addon_ids": ["info_a"]
}
```

These orders are based only on currently visible content. Hidden entities do not leave gaps or reveal their positions.

## Rows

Each object in `rows` is one currently visible normal Row.

Important fields:

```json
{
  "id": "row_a",
  "kind": "row",
  "index": 0,
  "title": "Example Row",
  "current_choices": 0,
  "allowed_choices": 1,
  "choice_ids": ["choice_a", "choice_b"],
  "selected_choice_ids": [],
  "available_choice_ids": ["choice_a", "choice_b"],
  "deselectable_choice_ids": [],
  "choices": ["choice_a", "choice_b"]
}
```

`choice_ids` is the ordered list of visible direct Choices under that Row. The Row-level `available_choice_ids` and `deselectable_choice_ids` refer only to direct Choices in that Row.

`rows[].choices` is retained for older callers. A compact view stores Choice IDs there. A verbose view stores nested Choice records there.

## Direct Choices

Each object in top-level `choices` is one visible direct Choice. Selectable Addons are not mixed into this list.

Important fields:

```json
{
  "id": "choice_a",
  "kind": "choice",
  "row_id": "row_a",
  "index": 0,
  "active": false,
  "count": 0,
  "can_select": true,
  "can_deselect": false,
  "addon_ids": ["info_a", "addon_a"],
  "informational_addon_ids": ["info_a"],
  "selectable_addon_ids": ["addon_a"]
}
```

`row_id` gives the visible parent Row. `index` is the Choice's visible position inside that Row. `addon_ids` is the visible Addon order under the Choice.

## Addons

Each object in top-level `addons` is one visible Addon. Informational and selectable Addons stay in the same Addon entity list and are distinguished by `kind`.

Important fields:

```json
{
  "id": "addon_a",
  "kind": "selectable_addon",
  "choice_id": "choice_a",
  "row_id": "row_a",
  "index": 1
}
```

For an informational Addon, `kind` is `addon`. For a selectable Addon, `kind` is `selectable_addon`.

`choice_id` identifies the direct parent Choice. `row_id` identifies the containing Row. `index` is the Addon's visible order under its parent Choice.

## Selection fields

The top-level view exposes both compatibility fields and explicit rc11 fields.

Use these fields for new automation:

```text
available_selection_ids
  All visible selectable entities, direct Choices plus selectable Addons.

deselectable_selection_ids
  All visible entities that can currently be deselected.

available_direct_choice_ids
  Direct Choices that can currently be selected.

deselectable_direct_choice_ids
  Direct Choices that can currently be deselected.

available_selectable_addon_ids
  Selectable Addons that can currently be selected.

deselectable_selectable_addon_ids
  Selectable Addons that can currently be deselected.
```

The older names `available_choice_ids` and `deselectable_choice_ids` remain for compatibility. They contain all selectable entities, including selectable Addons. Do not interpret those old names as direct-Choice-only fields.

## Selected IDs

The view also separates selected entities:

```text
selected_ids
  All currently selected visible selectable entities.

selected_choice_ids
  Selected visible direct Choices only.

selected_selectable_addon_ids
  Selected visible selectable Addons only.
```

## Structural expectations

A multi-step audit can check the hierarchy without reading raw project JSON:

```json
{
  "steps": [
    {
      "view": true,
      "expect": {
        "row_choices": {
          "row_a": ["choice_a", "choice_b"]
        },
        "choice_rows": {
          "choice_a": "row_a",
          "choice_b": "row_a"
        }
      }
    }
  ]
}
```

`row_choices` compares the complete visible direct-Choice order under each named Row. `choice_rows` checks a visible Choice's parent Row.

These assertions operate on the player-safe view. Hidden content remains hidden.

## Backpack Rows

Backpack Rows are excluded unless the caller requests them. With backpack inclusion enabled, `backpack_row_ids` and `backpack` are added separately. Normal `row_ids` and `rows` continue to represent normal Rows.

## Recommended agent traversal

For most playtesting, use the compact view and traverse it this way:

1. Read `row_ids` and `rows`.
2. For each relevant Row, read `choice_ids`.
3. Look up those IDs in the flat `choices` list for state such as `can_select`, `active`, and `row_id`.
4. If a Choice has Addons, read `addon_ids` and look them up in the flat `addons` list.
5. Use the explicit direct-Choice and selectable-Addon availability fields before selecting anything.

This avoids repeated nested searches and keeps Row, Choice, and Addon semantics separate.

## Visibility and privacy

The player view omits hidden Rows, Choices, and Addons rather than listing them as inaccessible. It also omits private runtime state, raw Requirement traces, RNG state, project fingerprints, and raw event details. A hidden guessed ID and a nonexistent ID return the same player-safe unavailable result.
