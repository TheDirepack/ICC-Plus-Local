# play

Read this file before player simulation, progressive playtesting, or player-visible audits.

`play` is the canonical player-safe runtime/testing command.

```bash
iccplus-local play project.json
iccplus-local play project.json --state run.json --select choice_a --compact
iccplus-local play project.json @audit.json --state run.json
```

Use compact views by default. Request verbose output only when visible titles, descriptions, Scores, Requirements, or fuller records are needed.

## Read the hierarchy directly

Rows, direct Choices, and Addons are separate entity types.

Use these top-level lists as the primary structure:

- `rows`
- `choices`
- `addons`
- `row_ids`
- `choice_ids`
- `addon_ids`

Rows expose ordered `choice_ids`. Choices expose `row_id`, visible-order `index`, and `addon_ids`. Addons expose `choice_id`, `row_id`, and visible-order `index`.

The older `rows[].choices` field remains for compatibility. Do not make an agent reconstruct hierarchy from it when the flat lists and explicit links are available.

## Keep Choice and Addon selection separate

Use:

- `available_direct_choice_ids`
- `deselectable_direct_choice_ids`
- `available_selectable_addon_ids`
- `deselectable_selectable_addon_ids`
- `available_selection_ids`
- `deselectable_selection_ids`

The older `available_choice_ids` and `deselectable_choice_ids` compatibility fields include selectable Addons as well as direct Choices.

## Continue sessions safely

Use `--state FILE` for continuation. Treat that state file as private runtime data. Do not inspect it to obtain information hidden from the player view.

Use `--reset` when a clean session is required.

For hierarchy-sensitive audits, assert `row_choices` and `choice_rows` in `expect` rather than rereading raw project JSON.

The full contract is in `../../../docs/PLAY_STRUCTURE.md`. Also read `GAMEPLAY_RUNNER.md` and `SESSION_PROTOCOL.md` for multi-step audits and saved-state behavior.
