# Bulk selectors

Bulk selectors let a script target a structural set without copying a long list of IDs into every operation. The same selector syntax is used by `match` and by bulk mutation operations.

Selectors are deliberately predictable. They do not use fuzzy matching. `title_contains` and `text_contains` are literal case-insensitive substring filters. All other filters are exact.

## Preview before writing

Use `match` with the exact selector that the edit will use.

```bash
iccplus-local match project.json '{"kind":"choice","row":"row_magic","id_prefix":"spell_"}' --expect 12
```

The response contains the count plus each matching ID, kind, path, parent, and Row.

`--expect` accepts an exact integer or a JSON range.

```bash
iccplus-local match project.json @selector.json --expect 12
iccplus-local match project.json @selector.json --expect '{"min":10,"max":15}'
```

A failed expectation is an error. This is useful in generated scripts because a stale selector does not silently edit a different number of objects.

## Selector fields

A selector is a JSON object. The current fields are:

| Field | Meaning |
| --- | --- |
| `kind` | One exact entity kind. |
| `kinds` | Any of several exact entity kinds. |
| `id` | One exact identity. |
| `ids` | Any of several exact identities. |
| `id_prefix` | IDs beginning with this string. |
| `row` | Entities in one Row. The Row itself also matches. |
| `rows` | Entities in any listed Row. |
| `parent` | Direct children of one parent identity. |
| `parents` | Direct children of any listed parent. |
| `group` | Members of one Group. |
| `groups` | Members of any listed Group. |
| `title_contains` | Case-insensitive literal substring in the entity title. |
| `text_contains` | Case-insensitive literal substring in the main text field. |
| `path_prefix` | JSON Pointer-like indexed path prefix from the project index. |
| `backpack` | `true` for Backpack content, `false` for ordinary project content. |

Multiple fields are ANDed. Lists inside one field are ORed.

This selector finds Choices in one Row whose IDs start with `spell_`:

```json
{
  "kind": "choice",
  "row": "row_magic",
  "id_prefix": "spell_"
}
```

This selector finds either Choices or selectable Addons that belong to one Group:

```json
{
  "kinds": ["choice", "selectable_addon"],
  "group": "group_fire"
}
```

## Use the selector in an edit

The selector is copied unchanged into `where`.

```json
{
  "op": "update_many",
  "where": {
    "kind": "choice",
    "row": "row_magic",
    "id_prefix": "spell_"
  },
  "expect": 12,
  "template": 2
}
```

The `expect` field belongs to the operation, not the `where` object.

Bulk operations reject an empty target set by default. Use `"allow_empty": true` only when zero matches are an expected no-op.

## Operations that accept `where`

The current bulk operations that accept selectors are:

- `update_many`
- `require`
- `exclude`
- `gate`
- `ungate`
- `score_many`
- `group_members`
- `design_group_members`
- `effects`
- `delete_many`

Each operation can also accept its normal explicit IDs. If both explicit IDs and `where` are supplied, the CLI uses the union and removes repeated IDs before checking `expect`.

## Safe generated edit pattern

For LLM-written scripts, use this sequence:

```bash
iccplus-local match project.json @selector.json --expect 24
iccplus-local apply project.json @repair.json
```

The repair should repeat the selector and expected count:

```json
{
  "op": "effects",
  "where": {
    "kind": "choice",
    "row": "row_implants",
    "id_prefix": "implant_"
  },
  "expect": 24,
  "effects": {
    "confirm": true
  }
}
```

The preview is for inspection. The expectation inside the mutation is the actual safety check.

## When explicit IDs are better

Use explicit IDs when the set is small, irregular, or represents a deliberate hand-picked exception list.

Use a selector when the set follows a stable structural rule such as one Row, one ID prefix, one Group, or one parent Choice.

Do not use text matching as a substitute for stable IDs when the project already has a structural way to name the set. Text changes more often than IDs.

## Atomic behavior

`apply` runs the entire operation script on a copy. If a selector expectation fails, a target ID is ambiguous, a later operation fails, or the final identity check fails, the original project is not written.

This makes a generated script safe to rerun after checking why it failed.
