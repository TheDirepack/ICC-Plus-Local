# Compact effects format

The `effects` object is a script-friendly way to author common ICC Plus Choice functions without remembering clusters of native field names. It works on Choices and selectable Addons.

The CLI expands `effects` into ordinary ICC Plus JSON. It does not add a second runtime format. The finished `project.json` contains the normal native fields used by the Viewer.

If an `effects` operation would disagree with an existing native field, the operation fails instead of silently choosing one value.

## Use through the operation system

```json
{
  "op": "effects",
  "target": "origin_mage",
  "effects": {
    "activate": ["gift_spellbook"],
    "row_limit": {"rows": ["row_spells"], "add": 2},
    "variables": {"targets": ["var_magic"], "mode": "true"},
    "confirm": true
  }
}
```

## Use during bulk edits

```json
{
  "op": "effects",
  "where": {"kind": "choice", "row": "row_magic", "id_prefix": "spell_"},
  "expect": 18,
  "effects": {
    "sfx": {"select": "sfx_spell"},
    "delay": {"select": 0.15}
  }
}
```

The bulk `effects` operation accepts the same `where`, `expect`, and `allow_empty` controls described in `BULK_SELECTORS.md`.

## Activation

```json
"effects": {
  "activate": ["choice_a", "choice_b"],
  "deactivate": "choice_c"
}
```

These expand to the native activate/deactivate Choice fields.

Native target strings are source-sensitive. Comma-separated target IDs are not trimmed, repeated or Group-overlapping targets are not deduplicated, and `/ON#` counts use JavaScript-style numeric-prefix parsing. Linked self-deactivation is deferred until the current selection finishes.

Random activation uses the same native target field, so do not combine deterministic `activate` and `random_activate` on the same Choice.

```json
"effects": {
  "random_activate": {
    "targets": ["choice_a", "choice_b", "choice_c"],
    "count": 1
  }
}
```

## Hide parts of Choices in target Rows

```json
"effects": {
  "hide_contents": {
    "rows": ["row_secret"],
    "contents": ["title", "image", "text", "scores", "requirements"]
  }
}
```

Accepted content names include `title`, `image`, `text`, `score` or `scores`, `requirement` or `requirements`, `addon_title`, `addon_image`, `addon_text`, `unselected_addon`, and `unmet_addon`.

This is the ICC Plus "Hide the Contents of Choices" effect. It is different from `hidden_until`, which hides a Row or Choice while its Requirement is unmet.

## Change a Row selection limit

```json
"effects": {
  "row_limit": {
    "rows": ["row_companions"],
    "add": 1
  }
}
```

Use a negative `add` value to reduce the allowed-choice count.

## Change Variables

```json
"effects": {
  "variables": {
    "targets": ["var_awakened", "var_magic"],
    "mode": "true"
  }
}
```

Modes are:

- `true`, `selected`, `mirror`, or `1`: true while selected and false after deselection.
- `false`, `inverse`, or `2`: false while selected and true after deselection.
- `toggle` or `3`: toggle the current value on each state change.

ICC Plus gives one change mode to the whole changed-variable list on a Choice. Use separate Choices when different Variables need different modes.

## Point Type transforms

```json
"effects": {
  "points": {
    "multiply": {"targets": ["power"], "by": 2},
    "divide": {"targets": ["cost"], "by": 2},
    "set": {"targets": ["rank"], "to": 5}
  }
}
```

These map to ICC Plus Point Type multiply, divide, and assignment fields. Expression strings are allowed for multiply and set where the native engine accepts them.

These transforms belong to ordinary Choice selection. They do not run on each repeat-counter increment or decrement. On ordinary selection the Viewer processes linked activation/deactivation and Requirement cleanup before multiply/divide/set transforms. The `belowZeroNotAllowed` affordability guard also runs before a later set transform, so a set effect can still leave the Point Type below zero.

## Word changes

```json
"effects": {
  "word": {
    "id": "word_name",
    "on_select": "Archmage",
    "on_deselect": "Mage"
  }
}
```

Add `"prompt": "Enter a callsign"` when the Viewer should ask the player for text through the native text-field behavior.

## Multiple selection

```json
"effects": {
  "multiple": {
    "start": 0,
    "min": 0,
    "max": 5,
    "click": true,
    "slider": true,
    "hide_counter": false,
    "hide_until_selected": false,
    "score": "budget"
  }
}
```

Use only the fields that matter. The tool writes the corresponding native multiple-selection fields. ICC Plus 2.10.6 has three different repeatable modes. Variable-count mode uses `isMultipleUseVariable`; point-backed mode uses `multipleScoreId`; `isSelectableMultiple` with neither mode is a malformed counter whose click/counter action is a Viewer no-op. Do not treat the third case as an ordinary quantity counter. Variable counts can move below zero when `numMultipleTimesMinus` permits it.

## Discounts

Apply a discount to specific Rows or Choices:

```json
"effects": {
  "discount": {
    "rows": ["row_weapons"],
    "choices": ["armor_light"],
    "points": ["budget"],
    "operator": "subtract",
    "value": 2,
    "stackable": true,
    "low_limit": 0
  }
}
```

Or target Groups:

```json
"effects": {
  "discount": {
    "groups": ["group_fire_spells"],
    "points": ["mana"],
    "operator": "multiply",
    "value": 0.5
  }
}
```

Do not mix Group targeting with Row/Choice targeting in one discount effect because ICC Plus uses one target mode at a time.

Readable arithmetic operators are `add`, `subtract`, `multiply`, `divide`, and `set`. Symbols are accepted too. The helper maps these names to the native ICC Plus operator codes according to runtime arithmetic.

Optional discount keys are `stackable`, `show`, `replace_text`, `hide_value`, `hide_icon`, `low_limit`, `count`, `count_per_selection`, `before_text`, and `after_text`.

## Scroll, template, and width

```json
"effects": {
  "scroll_to": {"row": "row_results"},
  "template": {"targets": ["choice_a", "choice_b"], "to": 2, "addons": true},
  "width": {"targets": ["choice_a", "choice_b"], "to": "col-sm-6"}
}
```

`scroll_to` must name exactly one Row or Choice.

## Selection behavior

```json
"effects": {
  "selection": {
    "select_once": true,
    "allow_deselect": false,
    "auto_active": false,
    "not_searchable": true
  }
}
```

Supported keys are `not_selectable`, `select_once`, `allow_deselect`, `auto_active`, `activate_after_reset`, `not_deselected_by_clean`, `clean_activated_on_select`, `not_deactivate`, `active_unselectable`, `count_disabled`, `deselect_when_no_addon`, `not_searchable`, `not_result`, `image_upload`, and `show_debug_title`.

These are thin aliases for native flags. Use the field catalog before using a flag whose ICC Plus behavior is unfamiliar.

## Duplicate a Row

```json
"effects": {
  "duplicate_row": {
    "source": "row_template",
    "after": "row_current"
  }
}
```

Optional `preserve_requirement_ids` and `preserve_function_ids` map to ICC Plus's "Do Not Add Suffix" settings. Preserving IDs can create collisions in duplicated content, so use it only when the native behavior is specifically required.

## Addon display behavior

```json
"effects": {
  "addons": {
    "show_all": true,
    "separate_layout": true,
    "show_score": true,
    "show_requirements": true,
    "show_multiple": true
  }
}
```

## Sound effects and BGM

```json
"effects": {
  "sfx": {
    "select": "sfx_open",
    "deselect": "sfx_close"
  },
  "bgm": {
    "id": "theme_battle",
    "fade_in": 1.5,
    "fade_out": 1.0,
    "no_loop": false
  }
}
```

Use `url` instead of `id` for the native audio-URL mode. `mute` maps to the native BGM mute effect.

Audio playback still needs a Viewer test.

## Delays and fade transition

```json
"effects": {
  "delay": {"select": 0.25, "deselect": 0.1},
  "transition": {
    "color": "#000000FF",
    "time": 0.3
  }
}
```

`transition` also accepts `fade_in` and `fade_out` for the matching native timing fields.

## Background and point bar

```json
"effects": {
  "background": {
    "color": "#10131AFF",
    "image": "assets/night.avif"
  },
  "point_bar": {
    "background": "#000000CC",
    "text": "#FFFFFFFF",
    "icon": "#FFFFFFFF"
  }
}
```

## Other compact flags

```json
"effects": {
  "confirm": true,
  "random_weight": 75,
  "backpack_button_requirement": true,
  "default_image": "assets/fallback.webp"
}
```

## Native fields remain available

The compact format is not meant to hide ICC Plus. It covers common multi-field effects and error-prone field bundles. For a feature not wrapped here, query the pinned native field catalog:

```bash
iccplus-local reference fields choice --contains bgm
iccplus-local reference fields choice --contains random
iccplus-local reference fields choice --contains addon
```

Then use the native fields in generation JSON, `update`, `update_many`, or `values` in an operation script.

This keeps new ICC Plus fields usable before a dedicated convenience alias is added.
