# template

Read this file when working with defaults, style presets, or design files.

Canonical paths:

```text
template entity KIND
template style list|show|apply
template design export|import
```

Use entity templates to inspect or create canonical entity defaults. Creator style templates are built-in design presets that can seed a design, but they are not the preferred mechanism for maintaining a reusable style family inside a project. For reusable project styling, use `style` with official Row/Choice Design Groups. Use design export/import when the task is about moving ICC Plus design configuration rather than editing normal project content.

Do not use `template` as a substitute for structural, rule, or normal style authoring. Use `structure`, `rules`, or `style` for those changes.

See `../../../docs/CLI_REFERENCE.md`, `CREATOR_TEMPLATE_BOUNDARY.md`, and `VISUAL_WORKFLOW.md`.
