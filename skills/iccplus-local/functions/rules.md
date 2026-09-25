# rules

Read this file for gameplay logic and rule authoring.

Use `rules` for Points, Scores, Requirements, Groups, gates, choice limits, costs, activation behavior, effects, and related gameplay logic.

```bash
iccplus-local rules project.json @rules.json
```

Do not use `rules` to create or reorder Rows, Choices, or Addons. Use `structure` for hierarchy and `style` for presentation.

For many similar rule changes, use batched items, refs, or selectors. Add `expect` when the matched count matters. Normal writes validate automatically before replacement.

After meaningful rule changes, use `play` to verify player-visible behavior rather than relying only on raw JSON inspection.

See `../../../docs/REQUIREMENT_RECIPES.md`, `EFFECT_RECIPES.md`, `EFFECTS_FORMAT.md`, `OPERATIONS_REFERENCE.md`, and `PHASED_AUTHORING.md`.
