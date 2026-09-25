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

Use `inspect` for several read-only queries in one process, or the smaller commands when one query is enough.

```bash
iccplus-local search build/project.json "Magic" --kind row
iccplus-local list build/project.json choice --row row_magic
iccplus-local show build/project.json choice_engineer
```

For a bulk selector, run `match` with `--expect`, then keep the same selector and expectation in the rules file.

## Low-level apply

Use generic `apply` only for an uncommon native field or a migration that does not fit a phase tool.

```bash
iccplus-local reference schema agent-operations
iccplus-local apply project.json @99-raw-fix.json
```

Keep durable raw edits in their own file so they can be reviewed and moved into a phase tool later.
