# style

Read this file for presentation changes.

Use `style` for images, templates, widths, card and Row presentation, and other visual styling handled by the style manifest.

```bash
iccplus-local style project.json @style.json
```

One style manifest can target one entity, explicit refs, or selector matches. Use `expect` when a selector should match a known number of entities.

Local and embedded images are compressed automatically when assigned. Do not add a separate compression command to ordinary style work.

Use `media` when the task is about importing, clearing, cropping, probing, or managing assets themselves. Use `template` when working with style presets or design import/export.

See `../../../docs/VISUAL_WORKFLOW.md`, `ASSET_COMPRESSION.md`, and `BULK_SELECTORS.md`.
