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

## Prefer native style scopes

Use the broadest native ICC Plus scope that fits the design.

1. Project `styling` is the default look for the whole CYOA.
2. Official Row/Choice Design Groups are the normal reusable style mechanism.
3. Private Row styling is for a genuine one-Row exception.
4. Private Choice styling is for a genuine one-Choice exception when no reusable scope fits.
5. Custom CSS is for gaps in the native styling system.

The official Viewer checks private Choice styling before Choice Design Groups, then private Row styling, then Row Design Groups, and finally project styling. Because private styling wins, unnecessary per-Choice styling can silently prevent later Design Group changes from taking effect.

## Reuse official Design Groups

Define reusable styling once under `design_groups`. The object key is the Design Group ID:

```json
{
  "format": "iccplus-visual-manifest",
  "format_version": 1,
  "design_groups": {
    "portrait-card": {
      "kind": "choice",
      "name": "Portrait card",
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
      "where": {"kind": "choice", "row": "row_race"},
      "expect": 8,
      "design_group": "portrait-card"
    }
  ]
}
```

Use `kind: "row"` for reusable Row treatments. Use `design_groups` on an item when several Design Groups should apply. Existing project Design Groups can be assigned without redefining them.

When an existing normal ICC Plus Group already defines the family, link the Design Group to that Group instead of enumerating every Choice:

```json
{
  "design_groups": {
    "element-card": {
      "kind": "choice",
      "groups": ["elements"],
      "styling": {
        "text": {"objectTitleAlign": "center"}
      }
    }
  },
  "items": []
}
```

This uses the official `Group.designGroups` / Design Group `groupElements` relationship. Future Choices added to the normal Group inherit the reusable style automatically.

The style command keeps both sides of the official Creator relationship synchronized: the Row/Choice receives the Design Group ID, and the Design Group receives the Row/Choice ID in its member list.

Grouped styling uses the native groups exposed by `reference fields styling`:

```bash
iccplus-local reference fields styling --style-group object_image
iccplus-local reference fields styling --style-group text
iccplus-local reference fields styling --style-group object
```

The manifest rejects unknown keys and unknown styling fields instead of silently ignoring them.

## Use presets for authoring macros, not shared runtime styling

A manifest `preset` is copied into every target. That is useful for repeated non-style edit values such as template or width:

```json
{
  "presets": {
    "portrait-layout": {
      "template": 2,
      "width": "col-md-4"
    }
  },
  "items": [
    {
      "where": {"kind": "choice", "row": "row_race"},
      "expect": 8,
      "preset": "portrait-layout",
      "design_group": "portrait-card"
    }
  ]
}
```

Do not put a shared `styling` block in a preset merely to duplicate it across many Choices. Put that styling in a Design Group instead.

## Bulk style and image work

One style manifest is already a bulk edit. Put many distinct image assignments in `items` when every target has different art. For one reusable treatment shared by many known Rows or Choices, assign one Design Group with `refs` or a selector:

```json
{
  "items": [
    {
      "refs": ["choice_a", "choice_b", "choice_c"],
      "design_group": "portrait-card"
    }
  ]
}
```

For a deliberate broad treatment, use `where` with `expect` so the edit fails if the matched count changes.

For individual art assignments, use one item per image inside the same manifest so source and crop notes remain unambiguous. A target may appear only once in a manifest.

## Private inline styling is an exception

The item-level `styling`, `copy_from`, `replace_styling`, and `unset_styling` controls operate on private per-target styling. Use them only when a Row or Choice genuinely needs a unique treatment that should override reusable Design Groups.

For example, a single plot-critical Choice can have a one-off border:

```json
{
  "items": [
    {
      "id": "choice_unique",
      "styling": {
        "object": {
          "objectBorderIsOn": true,
          "objectBorderWidth": 4
        }
      }
    }
  ]
}
```

If the same treatment appears on a second target, promote it to a Design Group rather than copying the private styling again.

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
