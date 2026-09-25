# style

Read this file for presentation changes.

Use `style` for images, templates, widths, project styling, official ICC Plus Design Groups, and exceptional private Row/Choice styling.

```bash
iccplus-local style project.json @style.json
```

## Styling priority for new work

Use the broadest native ICC Plus scope that fits the design:

1. **Project styling** for the normal look of the whole CYOA.
2. **Row/Choice Design Groups** for a reusable visual family shared by multiple Rows or Choices.
3. **Private Row styling** only when one Row genuinely needs an exception.
4. **Private Choice styling** only when one Choice genuinely needs an exception and neither project styling nor a Choice Design Group can express it.
5. **Custom CSS** only for presentation the native ICC Plus styling fields cannot express.

Do not repeat the same `styling` object on many Choices. That creates private per-Choice styling and makes later changes harder. Create one Choice Design Group and assign it instead.

## Reusable Design Groups

Design Groups are the official ICC Plus reusable style system. Define them at the top level of the style manifest and assign them by ID:

```json
{
  "format": "iccplus-visual-manifest",
  "format_version": 1,
  "design_groups": {
    "species-card": {
      "kind": "choice",
      "name": "Species card",
      "styling": {
        "object": {
          "objectBorderIsOn": true,
          "objectBorderWidth": 2
        },
        "text": {
          "objectTitleAlign": "center"
        }
      }
    }
  },
  "items": [
    {
      "where": {"kind": "choice", "row": "species"},
      "expect": 8,
      "design_group": "species-card"
    }
  ]
}
```

Use `kind: "row"` for Row Design Groups. Existing Design Group IDs can also be assigned with `design_group` or `design_groups` without redefining them.

ICC Plus evaluates private Choice styling before Choice Design Groups, then private Row styling, then Row Design Groups, then project styling. Avoid private styling unless that precedence is actually needed for a one-off exception.

## Presets

Manifest `presets` are authoring macros for repeated template, width, image, or other edit values. They are not the ICC Plus reusable runtime style system. If a preset contains `styling` and is applied to several Choices, it copies that styling into each Choice privately.

For reusable styling, put the styling in `design_groups` and keep presets for non-style edit values such as template and width when useful.

## Normal style work

One style manifest can target one entity, explicit refs, or selector matches. Use `expect` when a selector should match a known number of entities.

Local and embedded images are compressed automatically when assigned. Do not add a separate compression command to ordinary style work.

Use `media` when the task is about importing, clearing, cropping, probing, or managing assets themselves. Use `template` for the Creator's built-in style presets or design-file import/export.

See `../../../docs/VISUAL_WORKFLOW.md`, `ASSET_COMPRESSION.md`, and `BULK_SELECTORS.md`.
