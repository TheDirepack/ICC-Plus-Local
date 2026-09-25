# Native field catalog

`iccplus-local fields` exposes the native field names from the pinned ICC Plus 2.10.6 TypeScript model. It is intended for LLM and script discovery when a feature is known conceptually but its exact JSON property name is not.

```bash
iccplus-local reference fields project --contains customCSS --compact
iccplus-local reference fields choice --compact
iccplus-local reference fields choice --contains discount --compact
iccplus-local reference fields row --contains button --compact
iccplus-local reference fields point --contains icon --compact
iccplus-local reference fields styling --style-group filter --contains visible --compact
```

The output includes the target version, repository, commit, and source file.

## Kinds

The catalog covers `project`, `choice`, `row`, `backpack_row`, `addon`, `selectable_addon`, `score`, `requirement`, `point`, `variable`, `group`, `global_requirement`, `word`, `row_design_group`, `choice_design_group`, `viewer_config`, `sound_effect`, `category`, `defaults`, and `styling`.

`project` covers top-level `App` and default-setting field names. `backpack_row` is an alias for the native Row field set.

`choice` and `selectable_addon` include the shared `ChoiceFunc` fields so feature flags such as discounts, force activation, point multiplication, Variables, BGM, delayed selection, and content hiding can be discovered even though those fields are optional and do not all appear in a default template.

`styling` combines the native styling interfaces. `--style-group` can limit it to `filter`, `text`, `object_image`, `row_image`, `addon_image`, `background`, `object`, `row`, `addon`, `multi_choice`, `point_bar`, or `backpack`.

## How to use it

Use `fields` to discover names, then one of these:

- `template KIND` for the default native object shape;
- `show PROJECT ID` to inspect how an existing project uses the field;
- `docs/PATTERN_COOKBOOK.md` for common multi-field mechanics;
- `docs/EFFECT_RECIPES.md` for Choice effects;
- `docs/ICCPLUS_FIELD_REFERENCE.md` for authoring notes.

The catalog deliberately lists native names rather than inventing friendly aliases for every ICC Plus feature. High-frequency structure has concise helpers such as `costs`, `requires`, `hidden_until`, `gate`, and `score_many`. Common Choice-function bundles also have the `effects` format described in `EFFECTS_FORMAT.md`. Any feature not covered by a convenience layer can be written directly with the native fields discovered here.

## Misses and typo recovery

When `--contains` finds no field, the JSON response includes a `suggestions` array with close native names when useful. Direct `--field` edits and inline operation fields use the same catalog to reject likely typos before a write.

## Visual manifests

`apply-visuals` accepts styling either as flat native keys or grouped by the same `--style-group` names exposed by `fields styling`. The tool validates and flattens those groups into ICC Plus's native `styling` object. This gives an LLM readable group boundaries without creating alternate runtime fields.
