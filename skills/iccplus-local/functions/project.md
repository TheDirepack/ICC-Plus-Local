# project

Read this file for serialization, interchange, fragments, IDs, and build strings.

Canonical paths:

```text
project format
project validate [--compat]
project hydrate
project export
project fragment export|import
project ids export|from-titles
project build-summary
project build-string
```

Use `project validate` for the final Creator-complete check. It requires the full pinned official project skeleton, valid native field types, and Creator-eager entity fields. Use `--compat` only when inspecting legacy/sparse input that must remain untouched.

Use `project hydrate` to repair missing official project sections and safe eager entity defaults. Hydration preserves existing values, does not invent missing IDs, upgrades older supported projects to the pinned target, and never downgrades a future project version.

The other commands are interchange helpers. They are not alternate authoring paths.

Use `project format` when the task is formatting a complete project JSON. Use export and fragment operations when moving project data. Use ID helpers for ID interchange or derivation. Use build-summary and build-string for the corresponding ICC Plus serialization forms.

For content edits, use `structure`, `rules`, or `style` instead.

See `../../../docs/CLI_REFERENCE.md`, `ID_GUARANTEES.md`, and `BUILD_SYSTEM.md`.
