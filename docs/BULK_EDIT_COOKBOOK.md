# Bulk edit cookbook

Use `iccplus-local apply` for generated edits. A batch is atomic.

## Input forms

A normal JSON script:

```json
{
  "format":"iccplus-ops",
  "format_version":1,
  "operations":[]
}
```

A single operation object and a bare JSON array are also accepted. JSONL may contain one operation per line. If the script argument is omitted, `apply` reads stdin.

## Query the exact target IDs first

```bash
iccplus-local list project.json choice --row row_perks
iccplus-local list project.json all --id-prefix perk_mobility_
```

Copy the intended IDs into the mutation script. This avoids a broad mutation rule changing newly added content on a later run.

## Preview a selector before a bulk edit

For a regular structural set, preview it with `match` and assert the count.

```bash
iccplus-local match project.json '{"kind":"choice","row":"row_magic","id_prefix":"spell_"}' --expect 12
```

Then use the same selector and count in the mutation.

```json
{
  "op": "update_many",
  "where": {"kind": "choice", "row": "row_magic", "id_prefix": "spell_"},
  "expect": 12,
  "template": 2
}
```

This is safer than copying a long ID list when membership is defined by the project structure. See `BULK_SELECTORS.md`.

## Apply one effect bundle to a structural set

```json
{
  "op": "effects",
  "where": {"kind": "choice", "group": "group_fire"},
  "expect": {"min": 1},
  "effects": {
    "sfx": {"select": "sfx_fire"},
    "delay": {"select": 0.1}
  }
}
```

See `EFFECTS_FORMAT.md` for the compact effect keys.

## Update many IDs

```json
{
  "op":"update_many",
  "refs":["perk_a","perk_b","perk_c"],
  "kind":"choice",
  "objectWidth":"col-md-4"
}
```

Every reference must resolve. A missing ID fails the whole batch.

## Add or update generated objects

`upsert` is useful for repeatable scripts:

```json
{
  "op":"upsert",
  "kind":"choice",
  "parent":"row_perks",
  "id":"perk_fast",
  "title":"Fast"
}
```

If `perk_fast` exists, it is updated. Otherwise it is created.

## Require one option for many targets

```json
{
  "op":"require",
  "source":"origin_human",
  "targets":["perk_a","perk_b","perk_c"]
}
```

The operation is idempotent. Re-running it does not add duplicate simple Requirements.

Use `exclude` for the inverse selection condition.

## Hide many things until an option is selected

```json
{
  "op":"gate",
  "source":"path_magic",
  "targets":["row_spells","spell_fire","spell_ice"]
}
```

Rows are hidden by their unmet Requirement. Choices also receive the local requirement visibility filter. Addons can be targets as well.

To keep a Choice visible but disabled, use `require` instead of `gate`.

Remove the simple gate later with:

```json
{
  "op":"ungate",
  "source":"path_magic",
  "targets":["row_spells","spell_fire","spell_ice"]
}
```

## Set one cost on many Choices

```json
{
  "op":"score_many",
  "targets":["perk_a","perk_b","perk_c"],
  "point":"budget",
  "value":2
}
```

The command updates an existing unconditional Score for that Point Type or creates one. It does not add a second duplicate Score each time the script runs.

## Put many Choices in a Group

```json
{
  "op":"group_members",
  "group":"group_weapons",
  "members":["sword","axe","bow"]
}
```

Rows can be members too. The helper updates `rowElements` for Rows and `elements` for Choices or selectable Addons, plus the entity-side `groups` array.

Set `remove: true` to remove those members.

## Put Rows or Choices in a design group

```json
{
  "op":"design_group_members",
  "group":"rowdesign_dark",
  "members":["row_magic","row_endings"]
}
```

For a Row design group, direct content members may be Rows or Backpack Rows. For a Choice design group, direct content members may be Choices. Either design-group kind may also include a normal Group through ICC Plus `designGroups`. The helper updates both native sides of the relationship. Set `remove: true` to remove membership.

## Hide parts of Choices in Rows

```json
{
  "op":"hide_contents",
  "source":"censor_details",
  "rows":["row_secret_items","row_secret_people"],
  "contents":["title","image","text","score","requirements"]
}
```

This configures the native ICC Plus content-hiding effect on the source Choice. It is not a prerequisite gate.

Use `clear_hide_contents` to remove the effect.

## Delete many objects

```json
{
  "op":"delete_many",
  "refs":["old_a","old_b","old_c"],
  "kind":"choice"
}
```

Deletion is still part of the transaction. If one reference is wrong, none are removed.

## Guard a generated patch

Put assertions before edits:

```json
{"op":"assert","pointer":"/version","equals":"2.10.6"}
{"op":"assert","reference":"row_perks","kind":"row"}
```

An assertion failure stops the batch without writing.

## Raw field edits

Use `update` by ID for ordinary object fields. Use `set` only when the target is a project field or another value without a useful ID.

```json
{
  "op":"update",
  "ref":"perk_a",
  "template":2,
  "objectWidth":"col-md-6"
}
```

```json
{
  "op":"set",
  "pointer":"/viewerConfig/title",
  "value":"New title"
}
```

Every completed batch fills missing nested IDs and rejects duplicate identities before writing.

## Keep Group and design-group membership synchronized

Use the membership operations instead of editing both sides manually:

```json
{"op":"group_members","group":"group_magic","members":["row_magic","spell_fire","spell_ice"]}
{"op":"design_group_members","group":"design_magic","members":["spell_fire","spell_ice","group_magic"]}
```

`group_members` accepts Rows, Choices, and selectable Addons. `design_group_members` accepts the entity type supported by that design group and can also attach a normal Group through its native `designGroups` field. Backpack members are placed in the native `backpackElements` array automatically.

`normalize` treats member-side lists as canonical, removes repeated membership IDs, and rebuilds the reverse `elements`, `rowElements`, `backpackElements`, and `groupElements` arrays. This keeps generated and manually edited projects from carrying two conflicting copies of the same relationship.


## Validation-safe writes

Normal phase writes validate the completed project before writing. A validation error returns exit code 2 and leaves the target unchanged. Inline native fields are checked against the pinned field catalog. Compatibility-only low-level operations remain available for exceptional migrations, but they are not the normal LLM authoring path.
