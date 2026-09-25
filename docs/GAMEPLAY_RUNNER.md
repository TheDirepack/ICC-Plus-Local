# Player-safe gameplay audit

`play` is the canonical simulator and audit interface.

It returns only what the Viewer player can currently observe. Hidden Rows, Choices, Addons, raw Requirement traces, private runtime state, RNG state, project fingerprints, and raw event internals are not returned. A guessed hidden ID receives the same unavailable result as a nonexistent ID.

## Visible structure

The player view exposes the visible hierarchy in two forms at once:

- `rows`: visible Row records. Every Row has `choice_ids` in visible order. The older nested `rows[].choices` field remains for compatibility: verbose views contain Choice objects there, compact views contain Choice IDs.
- `choices`: a separate flat list of visible direct Choices. Every Choice has `row_id`, a visible-order `index`, and `addon_ids`.
- `addons`: a separate flat list of visible Addons. Every Addon has `row_id`, `choice_id`, and a visible-order `index` under its parent Choice.
- `row_ids`, `choice_ids`, and `addon_ids`: direct ordered indexes for the visible entities.
- `selectable_addon_ids` and `informational_addon_ids`: split visible Addons by gameplay role.

The indices are relative to currently visible content, so they do not reveal the positions or counts of hidden entities.

Selection state is also split explicitly. `available_selection_ids` and `deselectable_selection_ids` contain every visible selectable entity. `available_direct_choice_ids` / `deselectable_direct_choice_ids` contain direct Choices only, while `available_selectable_addon_ids` / `deselectable_selectable_addon_ids` contain selectable Addons only. The historical `available_choice_ids` and `deselectable_choice_ids` fields remain compatibility aliases for all selectable entities.

A compact view is therefore enough to understand both the current choices and their structure without traversing nested verbose data.


For new automation, treat the flat `rows`, `choices`, and `addons` lists as canonical. Use `rows[].choices` only when maintaining an older caller. A reliable compact-view traversal is:

1. Read `row_ids` and the matching Row records.
2. Use each Row's `choice_ids` to get the visible direct Choices under it.
3. Use the flat `choices` list for Choice state and parent `row_id`.
4. Follow a Choice's `addon_ids` into the flat `addons` list when Addons matter.
5. Use the explicit direct-Choice and selectable-Addon availability fields before acting.

See `PLAY_STRUCTURE.md` for the current field-by-field structure.

## One action at a time

```bash
iccplus-local play project.json --state run.json --select origin_human
iccplus-local play project.json --state run.json --status class_mage
iccplus-local play project.json --state run.json --deselect origin_human
```

The state file is private continuation data and does not need to enter the LLM context.

## Multi-step audit

```bash
iccplus-local play project.json @audit.json --state run.json
```

Example:

```json
{
  "steps": [
    {
      "select": "key",
      "expect": {
        "points": {"budget": 7},
        "selected": ["key"],
        "available": ["cheap", "six_cost"],
        "visible": ["unlocked"],
        "hidden": ["secret_row"],
        "row_choices": {"unlocked": ["cheap", "six_cost"]},
        "choice_rows": {"cheap": "unlocked", "six_cost": "unlocked"}
      }
    },
    {
      "select": "cheap",
      "expect": {
        "points": {"budget": 5},
        "not_available": ["six_cost"]
      }
    }
  ]
}
```

`row_choices` compares the complete visible Choice order for each named Row. `choice_rows` checks the visible parent Row of each named Choice. Every step returns the sanitized action result plus the player-visible view after that action. Failed expectations make the audit fail without exposing hidden state.
