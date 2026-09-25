# LLM visual authoring workflow

`iccplus-local` 0.10.0rc7 includes the compact visual audit and visual manifest introduced in 0.9.0. The tool writes ordinary ICC Plus 2.10.6 fields. The manifest is an authoring file, not a runtime format.

## Start with a small work queue

Use `inspect` with `op: "visual"` instead of loading the complete project when the task is to find art, inspect card geometry, or plan a style pass.

```json
{
  "op": "visual",
  "kind": "choice",
  "row": "row_race",
  "missing_images": true,
  "limit": 12,
  "manifest_stub": true
}
```

```bash
iccplus-local inspect project.json @visual-inspect.json
```

Each returned item has its stable reference, kind, Row context, title, current image, image kind, template, width, text length and excerpt, normal Group membership, inline style groups, and design-group membership. Set `style_values` only when actual inline style values are needed.

The visual report keeps the full match count separate from the number returned after `limit`. `manifest_stub` contains one target entry for every returned item.

## Audit local image references

Set `asset_root` in the same visual inspect query when image paths should resolve inside a release directory. Set `missing_assets` to return only broken assigned local paths. Remote URLs and embedded data images are classified but never fetched. `missing_assets` requires `asset_root`; `missing_images` instead finds cards with no assigned image.

## Keep image research in the manifest or source ledger

Record source data next to the image assignment when attribution, permission, or later replacement may matter. Useful fields include source URL, creator, license or permission, credit text, search terms, and crop notes.

`style` returns these records in `source_records`. Each record also contains the resulting image path. The tool does not add this metadata to `project.json` because ICC Plus 2.10.6 has no general native per-image attribution field.

## Reuse named visual presets

A preset can hold the ICC Plus fields that should remain identical across a card family:

```json
{
  "format": "iccplus-visual-manifest",
  "format_version": 1,
  "presets": {
    "portrait-card": {
      "template": 2,
      "width": "col-md-4",
      "styling": {
        "object_image": {
          "objectImageWidth": 100,
          "objectImgOverflowIsOn": true
        },
        "text": {
          "objectTitleAlign": "center"
        }
      }
    }
  },
  "items": [
    {
      "id": "choice_knight",
      "preset": "portrait-card",
      "image": "assets/knight.webp"
    }
  ]
}
```

Grouped styling uses the native groups exposed by `fields styling`:

```bash
iccplus-local reference fields styling --style-group object_image
iccplus-local reference fields styling --style-group text
iccplus-local reference fields styling --style-group object
```

The manifest rejects unknown keys and unknown styling fields. A misspelled `width`, preset key, project key, or native style field is an error instead of a silent no-op.

## Bulk style and image work

One style manifest is already a bulk edit. Put many distinct image assignments in `items` when every target has different art. For one treatment shared by several known cards, use `refs`:

```json
{
  "items": [
    {
      "refs": ["choice_a", "choice_b", "choice_c"],
      "preset": "portrait-card"
    }
  ]
}
```

For a deliberate broad treatment, use `where` with `expect` so the edit fails if the matched count changes:

```json
{
  "items": [
    {
      "where": {"kind":"choice","row":"row_race"},
      "expect": 8,
      "preset": "portrait-card"
    }
  ]
}
```

For individual art assignments, use one item per image inside the same manifest so source and crop notes remain unambiguous. A target may appear only once in a manifest.

## Copy a proven visual treatment

When one existing card already looks correct, copy its template, width, and inline styling:

```json
{
  "items": [
    {
      "id": "choice_b",
      "copy_from": "choice_a",
      "image": "assets/choice-b.webp"
    }
  ]
}
```

`copy_from` works only within the same visual family, such as Choice to Choice or Addon to Addon. It does not copy the source image unless `copy_image` is `true`.

If the source card is also changed earlier in the same manifest, a later `copy_from` sees that updated treatment. Use presets when order-independent reuse is clearer.

## Replace or remove stale inline styling

Normal preset and `copy_from` styling merges with existing inline styling. Use `replace_styling` when the target should start from a clean inline style object:

```json
{
  "id": "choice_b",
  "replace_styling": true,
  "preset": "portrait-card"
}
```

Use `unset_styling` to remove specific native style fields after copied or preset styling is applied:

```json
{
  "id": "choice_b",
  "preset": "portrait-card",
  "unset_styling": ["objectBorderIsOn"]
}
```

This makes cleanup explicit instead of relying on `null` values or hand-edited JSON.

## Apply project-wide styling carefully

The manifest can update the native project `styling` object and `customCSS`:

```json
{
  "project": {
    "styling": {
      "background": {
        "bgColorIsOn": true,
        "backgroundColor": "#10131AFF"
      }
    },
    "customCSSAppend": ".special-card { max-width: 60rem; }"
  },
  "items": []
}
```

`customCSSAppend` adds the exact block only when it is not already present, so rerunning the same manifest does not duplicate it. Use `customCSS` when the manifest should replace the complete project CSS string.

Prefer native ICC Plus design controls before custom CSS. Use CSS for a verified gap in the native controls.

## Dry-run before writing

```bash
iccplus-local style project.json visual_manifest.json --dry-run
```

The command reports project changes, changed IDs, normalization changes, and static validation. It writes nothing in dry-run mode.

Apply after review:

```bash
iccplus-local style project.json visual_manifest.json \
  --report-out visual_apply_report.json
```

Normal validation-safe write rules apply. If the input project already has known validation errors, fix them first when practical. Normal style writes validate before commit; validation failures leave the target unchanged.

## Keep the visual manifest

The manifest is useful after the first pass because it records image assignments, reusable presets, source records, and crop notes in a much smaller file than the complete project. Update it when art is replaced instead of rebuilding the visual plan from chat history.

## Verify in the real Viewer

The headless runner does not render images, CSS, layout, fonts, overlays, cropping, or responsive geometry. The visual `inspect` query checks configuration and local file presence only.

After a visual pass, test the real ICC Plus Viewer at phone, tablet, desktop, and wide desktop widths. Check the states the project actually uses, including selected, disabled, hidden, Addon, Backpack, point bar, menu, and dialog states.

## Recommended LLM loop

1. Run a narrow visual `inspect` query.
2. Generate a manifest stub when useful.
3. Find or prepare art and record its source data.
4. Calibrate a preset on representative cards.
5. Put all image assignments and shared `refs`/`where` treatments in one or more reviewable manifests.
6. Run `style --dry-run`.
7. Review the changed IDs and validation output.
8. Apply the manifest.
9. Run another visual `inspect` query with `asset_root` and `missing_assets`.
10. Compress assets after image choices and crops are stable.
11. Verify the rendered result in the real Viewer.

See `examples/visual_manifest.json` and `schemas/visual-manifest.schema.json`.
