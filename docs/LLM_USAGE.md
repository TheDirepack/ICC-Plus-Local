# LLM usage

## Skill routing

Use `../../skills/iccplus-local/SKILL.md` as the single general ICC Plus Local skill. It routes the task to one or more focused guides under `../../skills/iccplus-local/functions/`. The function guides are not standalone installed skills. Read only the guide or guides needed for the current operation.

Use the smallest workflow possible.

1. `generate` for a new blank project.
2. `inspect` to understand an existing project.
3. `structure`, `rules`, and `style` for edits.
4. `play` to audit the resulting player-visible behavior.
5. `project` only for serialization/export/interchange.

## Discovery

Do not guess commands or fields.

```bash
iccplus-local reference commands
iccplus-local reference capabilities --brief
iccplus-local reference fields choice --details
iccplus-local reference schema structure-ops
```

## Editing

Single and bulk edits use the same phase commands. Prefer `items`, `refs`, and `where` selectors over issuing many one-object commands. Use `expect` when selector cardinality matters.

Normal edits validate automatically before write. Do not plan a separate validation command after each edit.

## Style and images

Use one style manifest for one or many changes. Follow the native ICC Plus styling hierarchy instead of copying private style onto many entities:

1. project `styling` for the CYOA-wide default,
2. official Row/Choice Design Groups for reusable visual families,
3. private Row styling for a one-Row exception,
4. private Choice styling only for a one-Choice exception when no reusable scope fits,
5. custom CSS only when native styling fields cannot express the result.

The `style` manifest exposes reusable Design Groups directly through top-level `design_groups` and per-item `design_group` / `design_groups`. Prefer that path whenever two or more Rows or Choices should share styling.

Manifest `presets` are authoring macros, not ICC Plus runtime Design Groups. Do not put shared styling in a preset merely to copy it into many Choices.

Local and embedded images are compressed automatically when assigned. Do not ask the model to choose whether to compress them.

## Testing

`play` is the only canonical runtime/testing surface. Use direct action flags for one step or a JSON request for a full progressive audit. The response is player-safe: hidden content and runtime internals are omitted.

Keep `--state FILE` private. The LLM should reason from the returned player view, not from the serialized runtime state.


### Reading the rc11 player structure

Use compact player views by default. Read `rows`, `choices`, and `addons` as separate entity lists. A Row's `choice_ids` gives its visible direct Choices. Each Choice has `row_id` plus `addon_ids`. Each Addon has both `choice_id` and `row_id`.

Do not infer direct-Choice availability from the historical `available_choice_ids` name when Addons exist. That compatibility field includes selectable Addons. Use `available_direct_choice_ids` for direct Choices and `available_selectable_addon_ids` for selectable Addons.

When an audit depends on hierarchy, assert `row_choices` and `choice_rows` rather than rereading raw project JSON. See `PLAY_STRUCTURE.md` for the complete view contract.

## Namespaces

- `template`: entity defaults, style presets, design files
- `media`: images, crops, fonts, sound, asset probing
- `project`: formatting, export, fragments, IDs, Build Form serialization
- `reference`: commands, capabilities, schemas, fields, types, guides, parity, symbols

Compatibility aliases are for old scripts only and should not be emitted by new automation.
