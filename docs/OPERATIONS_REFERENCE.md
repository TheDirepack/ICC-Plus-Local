# Operation reference

This document describes the underlying operation vocabulary used by phase scripts and retained compatibility paths. It is not a separate public workflow. New automation should execute operations through `structure`, `rules`, or `style`, using the schema returned by `reference schema` for that phase.

Phase writes run against a copy and replace the project only after operation checks and complete-project validation succeed.

## Short syntax

The common aliases are:

```text
ref         -> reference
refs        -> references
target      -> targets for one item
member      -> members for one item
row         -> rows for one item
content     -> contents for one item
```

A one-or-many field accepts either a string or an array.

For `add`, `upsert`, `update`, and `update_many`, native entity fields may be written directly on the operation:

```json
{"op":"update","ref":"perk_fast","title":"Fast","template":2}
```

Inline fields are checked against the pinned native field catalog. This catches common generated-key typos. The older nested form remains valid and is the escape hatch for intentional forward-compatible fields:

```json
{"op":"update","ref":"perk_fast","values":{"futureNativeField":true}}
```

Do not put the same field both inline and in `values`.

## `assert`

```json
{"op":"assert","ref":"row_perks","kind":"row"}
{"op":"assert","pointer":"/version","equals":"2.10.7"}
```

Use assertions before edits whose correctness depends on the project revision.

## `add`

```json
{"op":"add","kind":"choice","parent":"row_perks","id":"perk_fast","title":"Fast"}
```

Use `upsert` when rerunning the script should update the same ID.

## `upsert`

```json
{"op":"upsert","kind":"choice","parent":"row_perks","id":"perk_fast","title":"Fast"}
```

If the identity exists in the requested kind, the CLI deep-merges the fields. Otherwise it creates the entity under `parent`.

## `update`

```json
{"op":"update","ref":"perk_fast","kind":"choice","template":2,"unset":["temporaryField"]}
```

An update cannot change an entity identity. Use `rename`.

## `where`, `expect`, and `allow_empty`

Bulk operations can target an exact structural set with `where`. Preview the same selector first with an `inspect` match query.

```json
{
  "op": "update_many",
  "where": {"kind": "choice", "row": "row_magic", "id_prefix": "spell_"},
  "expect": 12,
  "template": 2
}
```

`expect` accepts an exact integer or `{ "min": N, "max": M }`. A mismatch aborts the complete atomic script. Empty matches are rejected unless `allow_empty` is true. See `BULK_SELECTORS.md`.

## `update_many`

```json
{"op":"update_many","refs":["perk_a","perk_b","perk_c"],"kind":"choice","objectWidth":"col-md-4"}
```

Every reference must resolve or the whole batch fails.

## `require` and `exclude`

```json
{"op":"require","source":"origin_mage","targets":["spell_a","spell_b"]}
{"op":"exclude","source":"origin_robot","target":"spell_a"}
```

These create simple ID Requirements. They are idempotent for the same source, target, and polarity.

## `gate` and `ungate`

```json
{"op":"gate","source":"origin_mage","targets":["row_magic","spell_a"]}
{"op":"ungate","source":"origin_mage","target":"spell_a"}
```

`gate` adds a simple Requirement and configures Choice visibility where needed. `hidden` and `required` default to `true`. `ungate` removes matching simple ID Requirements. `restore_visibility` defaults to `true`.

## `score_many`

```json
{"op":"score_many","point":"budget","value":2,"targets":["perk_a","perk_b"]}
```

For each target, the helper updates an existing simple unconditional Score for that Point Type or creates one.

## `group_members` and `design_group_members`

```json
{"op":"group_members","group":"group_fire","members":["spell_a","spell_b"]}
{"op":"design_group_members","group":"design_dark","member":"spell_a"}
```

Set `remove: true` to remove membership. The helper keeps the native forward and reverse membership fields synchronized.

## `effects`

Apply one compact Choice-function bundle to explicit Choices/selectable Addons or to a `where` selector.

```json
{
  "op": "effects",
  "where": {"kind": "choice", "row": "row_magic"},
  "expect": 8,
  "effects": {
    "sfx": {"select": "sfx_magic"},
    "confirm": true
  }
}
```

The compact effect keys are documented in `EFFECTS_FORMAT.md`. They expand into native ICC Plus properties.

## `hide_contents` and `clear_hide_contents`

```json
{"op":"hide_contents","source":"redaction_mode","row":"row_secret","contents":["title","image","text"]}
{"op":"clear_hide_contents","source":"redaction_mode"}
```

These write or remove ICC Plus `isContentHidden`, `hiddenContentsRow`, and `hiddenContentsType`.

## `delete` and `delete_many`

```json
{"op":"delete","ref":"old_perk","kind":"choice"}
{"op":"delete_many","refs":["old_a","old_b"],"kind":"choice"}
```

Deletion does not invent replacements for references elsewhere. Validation after the batch reports broken references.

## `rename`

```json
{"op":"rename","old":"old_id","new":"new_id"}
```

This rewrites known reference fields throughout the project. Use it instead of directly setting an `id` or Score `idx`.

## `set` and `remove`

```json
{"op":"set","pointer":"/viewerConfig/title","value":"My CYOA"}
{"op":"remove","pointer":"/temporaryField"}
```

These are raw JSON Pointer operations. The final identity and validation checks still run.

## `normalize`

```json
{"op":"normalize"}
```

This fills missing identities, rebuilds indexes, repairs known reverse membership mappings, and performs the normal normalization pass. Every batch performs a final normalization and identity check even when this operation is absent.

## Failure response

A failed phase operation reports the failing operation and writes nothing. Identity or complete-project validation failures also leave the original target unchanged. Compatibility-only raw paths may have different diagnostic detail and should not be the default for new automation.
