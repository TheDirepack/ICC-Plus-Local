# structure

Read this file for structural authoring.

Use `structure` for Rows, Choices, Addons, IDs, titles, text, order, moves, clones, and other hierarchy changes.

```bash
iccplus-local structure project.json @structure.json
```

Keep gameplay logic out of this phase. Requirements, Scores, Points, Groups, limits, costs, and activation behavior belong in `rules`. Presentation belongs in `style`.

For broad changes, use one operation with `items`, explicit `refs`, or selectors instead of many single-entity calls. Add `expect` when selector cardinality matters. Normal writes validate before replacing the project.

Preserve stable IDs unless the task explicitly requires an ID change. When moving Choices or Addons, verify the intended parent and visible order.

See `../../../docs/PHASED_AUTHORING.md`, `AUTHORING_SCRIPTS.md`, `ENTITY_FORMATS.md`, `ID_GUARANTEES.md`, and `BULK_EDIT_COOKBOOK.md`.
