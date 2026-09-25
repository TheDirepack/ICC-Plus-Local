# Native field catalog

`iccplus-local reference fields` exposes native field names from the pinned ICC Plus 2.10.7 TypeScript model. Use it when a feature is known conceptually but its exact JSON property name or type is uncertain.

```bash
iccplus-local reference fields project --contains customCSS --compact
iccplus-local reference fields choice --compact
iccplus-local reference fields choice --contains discount --compact
iccplus-local reference fields row --contains button --compact
iccplus-local reference fields point --contains icon --compact
iccplus-local reference fields score --contains removeSpace --compact
iccplus-local reference fields styling --style-group filter --contains visible --compact
```

The response includes the target version, source repository, pinned commit, and source file.

## Kinds

The catalog covers `project`, `choice`, `row`, `backpack_row`, `addon`, `selectable_addon`, `score`, `requirement`, `point`, `variable`, `group`, `global_requirement`, `word`, `row_design_group`, `choice_design_group`, `viewer_config`, `sound_effect`, `category`, `defaults`, and `styling`.

`choice` and `selectable_addon` include shared Choice-function fields. `styling` combines the native styling interfaces and supports `--style-group` filtering.

## How to use it

Discover the native field first, then use the owning public workflow:

- `template entity KIND` for an official default entity shape.
- `inspect` to see how an existing project uses a field.
- `structure` for Rows, Choices, Addons, IDs, text, and hierarchy.
- `rules` for Points, Scores, Requirements, Groups, costs, limits, activation, and gameplay effects.
- `style` for presentation and official Row/Choice Design Groups.
- `project validate` for the final Creator-complete check.

See `PATTERN_COOKBOOK.md`, `EFFECT_RECIPES.md`, and `ICCPLUS_FIELD_REFERENCE.md` for common combinations.

## Misses and typo recovery

When `--contains` finds no field, the response can include close native-name suggestions. Phase commands also check known native fields and reject likely typos before writing.

## Visual manifests

The `style` command accepts flat native styling keys or the grouped style forms documented by `reference fields styling`. For reusable styling, use top-level `design_groups` and assign them with `design_group` or `design_groups`. Manifest presets are authoring macros, not runtime Design Groups.
