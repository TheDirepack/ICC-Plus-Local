# Scripted authoring

ICC Plus Local starts from the blank Creator project and edits it in phases. There is no separate generation document for project content.

## Start a project

```bash
iccplus-local generate -o project.json
```

This writes the exact ICC Plus 2.10.7 blank Creator export and verifies it against complete-project validation.

## Add sections and content

Use `structure` for Rows, Choices, Addons, IDs, titles, text, ordering, moving, and cloning.

```json
{
  "format": "iccplus-structure-ops",
  "format_version": 1,
  "strict_fields": true,
  "operations": [
    {"op": "add", "kind": "row", "values": {"id": "row_origin", "title": "Origin"}},
    {"op": "add", "kind": "choice", "parent": "row_origin", "values": {"id": "origin_human", "title": "Human"}}
  ]
}
```

```bash
iccplus-local structure project.json @10-structure.json
```

## Add mechanics

Use `rules` for Points, Requirements, Scores, Groups, gating, costs, selection limits, Variables, Words, and effects.

```bash
iccplus-local rules project.json @20-rules.json
```

Prefer the rule helpers `require`, `exclude`, `gate`, `ungate`, `score_many`, `group_members`, and `effects` when they fit.

## Add presentation

Use `style` for images, templates, widths, native styling, CSS, and visual presets.

```bash
iccplus-local style project.json @90-style.json
```

## Build from multiple files

For a maintained project, keep one or more files per phase and a version 2 build manifest.

```bash
iccplus-local build project-src/iccplus.build.json -o build/project.json
```

`build` starts from a fresh blank project every time, calls the same structure, rules, and style implementations as the direct commands, fills any missing official project sections from the pinned Creator defaults, and refuses to write unless the result passes complete-project validation.

See `BUILD_SYSTEM.md` and `PHASED_AUTHORING.md`.

## Inspect before changing

Use `inspect` for read-only discovery. Put related queries in one request:

```json
{
  "queries": [
    {"op":"search","query":"Magic","kind":"row","limit":10},
    {"op":"show","ref":"choice_engineer","kind":"choice"},
    {"op":"match","where":{"kind":"choice","row":"row_magic"},"expect":{"min":1}}
  ]
}
```

```bash
iccplus-local inspect build/project.json @inspect.json
```

Keep the same selector and `expect` count in the following phase operation.

## Uncommon native fields

Do not switch to a hidden compatibility command because a field is uncommon. Discover it with `reference fields` and `reference schema`, then write it through `structure`, `rules`, or `style` according to its owner.

If a maintained build genuinely requires a compatibility-only raw step, isolate that step in the build source and document why no canonical phase can represent it. New one-off automation should stay on the public command tree.
