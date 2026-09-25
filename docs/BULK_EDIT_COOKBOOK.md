# Bulk edit cookbook

Bulk work uses the same public phase commands as one-item work. A phase script is atomic: if a target is wrong, an expectation fails, or final validation fails, the target project is not replaced.

## Inspect the targets first

Use one `inspect` request to list exact IDs or preview a selector:

```json
{
  "queries": [
    {"op":"list","kind":"choice","row":"row_perks"},
    {
      "op":"match",
      "where":{"kind":"choice","row":"row_magic","id_prefix":"spell_"},
      "expect":12
    }
  ]
}
```

```bash
iccplus-local inspect project.json @inspect.json
```

Keep the same selector and `expect` value in the write operation.

## Bulk structural changes

Use `structure` for titles, text, templates owned by structure, widths owned by structure, hierarchy, moves, clones, and deletion.

```json
{
  "format":"iccplus-structure-ops",
  "format_version":1,
  "operations":[
    {
      "op":"update",
      "where":{"kind":"choice","row":"row_magic","id_prefix":"spell_"},
      "expect":12,
      "values":{"objectWidth":"col-md-4"}
    }
  ]
}
```

```bash
iccplus-local structure project.json @structure.json
```

Use explicit `refs` when the set is irregular or deliberately hand-picked.

## Bulk rule changes

Use `rules` for Requirements, costs, Scores, Groups, gates, repeat behavior, and Choice effects.

```json
{
  "format":"iccplus-rules-ops",
  "format_version":1,
  "operations":[
    {
      "op":"effects",
      "where":{"kind":"choice","group":"group_fire"},
      "expect":{"min":1},
      "effects":{"sfx":{"select":"sfx_fire"},"delay":{"select":0.1}}
    }
  ]
}
```

Other useful rule operations include `require`, `exclude`, `gate`, `ungate`, `score_many`, and Group membership changes. Use `reference schema rules-ops` when the exact shape is uncertain.

## Reusable style changes

Use `style` for presentation. Do not copy one private `styling` object onto many entities. Define an official Row or Choice Design Group once and assign it by ID, or link it to an existing normal ICC Plus Group.

```json
{
  "format":"iccplus-visual-manifest",
  "format_version":1,
  "design_groups":{
    "magic-card":{
      "kind":"choice",
      "styling":{"text":{"objectTitleAlign":"center"}}
    }
  },
  "items":[
    {
      "where":{"kind":"choice","row":"row_magic"},
      "expect":12,
      "design_group":"magic-card"
    }
  ]
}
```

```bash
iccplus-local style project.json @style.json
```

## Deletes and ID changes

Use `structure` for structural deletion and ID migration. Inspect references first. Preserve stable public IDs unless a deliberate migration requires a rename.

## Safety rules

- Inspect before a broad write.
- Carry the expected match count into the mutation.
- Re-resolve a selector after an earlier change that can alter its membership.
- Prefer stable IDs over text matching.
- Treat an unexpected match count as a stopped operation.
- Read the write receipt. Normal writes hydrate safe missing Creator defaults and complete-validate before replacement.
- Use `project validate` for the final Creator-complete check, not after every ordinary phase write.
