# ICC Plus local CLI

Version 0.10.0rc11 is a workflow-centered local authoring and testing tool for ICC Plus 2.10.6, pinned to source commit `a420836248d32043ae45d03f1b93cdcb9e354663`.

The canonical top-level interface is intentionally small:

```text
reference   discovery, schemas, fields, guides, parity
 template   entity defaults, style presets, Creator design templates
media       images, crops, fonts, sound, asset inspection
project     formatting, export/import, IDs, Build Form serialization
inspect     batched read-only project inspection
generate    exact blank Creator project
build       deterministic phased build
structure   Rows, Choices, Addons, text, IDs, ordering
rules       Points, Requirements, Scores, Groups, effects
style       images, templates, widths, styling
play        player-safe progressive testing and audit
```

Normal authoring is:

```bash
iccplus-local generate -o project.json
iccplus-local structure project.json @structure.json
iccplus-local rules project.json @rules.json
iccplus-local style project.json @style.json
iccplus-local play project.json
```

`structure`, `rules`, and `style` validate automatically before writing. A failed validation leaves the target unchanged. There is no separate validation step in the normal workflow.

## Bulk authoring

Single and bulk edits use the same phase commands. Structure/rules operations can use one object, `items`, explicit `refs`, or selectors as appropriate. Style manifests can contain many independent items and can target one ref, many refs, or a selector. Use `expect` on broad selectors so a generated edit fails instead of silently matching the wrong number of entities.

## Images

Image compression is automatic when local or embedded images are assigned. The LLM should not plan or run a separate compression pass.

```bash
iccplus-local media image import project.json choice_a image.png
iccplus-local media crop field project.json choice_a --aspect 16:9
```

## Player-safe testing

`play` is both the normal simulator and the audit surface. It only returns information the player can observe. Hidden and nonexistent guessed IDs are deliberately indistinguishable.

Single step:

```bash
iccplus-local play project.json --state run.json --select choice_a
```

Multi-step audit:

```bash
iccplus-local play project.json @audit.json --state run.json
```

Example audit request:

```json
{
  "steps": [
    {
      "select": "choice_a",
      "expect": {
        "points": {"budget": 7},
        "selected": ["choice_a"],
        "available": ["choice_b"],
        "hidden": ["secret_choice"]
      }
    }
  ]
}
```

Every step returns the sanitized action result and the player-visible view after that action. The view exposes Rows, direct Choices, and Addons separately, with explicit `choice_ids`, `row_id`, `addon_ids`, and parent links. Expectations can check visible Point balances, selected IDs, availability, deselectability, visibility, absence from the visible surface, Row-to-Choice membership, and Choice-to-Row parentage. New automation should treat the flat `rows`, `choices`, and `addons` lists as canonical and use the nested `rows[].choices` form only for compatibility. See `docs/PLAY_STRUCTURE.md` for the complete rc11 view contract.

## Templates and resources

All template-like operations are under `template`:

```bash
iccplus-local template entity choice
iccplus-local template style list
iccplus-local template style apply project.json 1
iccplus-local template design export project.json global -o design.json
```

Media resources are under `media`:

```bash
iccplus-local media image import project.json choice_a image.png
iccplus-local media font add project.json google "Roboto"
iccplus-local media sound import project.json click.wav
iccplus-local media probe image.png
```

## Project I/O

Project serialization and interchange live under `project`:

```bash
iccplus-local project format project.json --style creator -o project.creator.json
iccplus-local project export project.json -o project.zip
iccplus-local project fragment export project.json choice_a -o choice.json
iccplus-local project fragment import project.json choice @choice.json --parent row_a
iccplus-local project ids export project.json -o ids.csv
```

## Discovery

Use `reference` instead of guessing commands or fields:

```bash
iccplus-local reference commands
iccplus-local reference capabilities --brief
iccplus-local reference fields choice --details
iccplus-local reference schema structure-ops
iccplus-local reference guide automation
iccplus-local reference parity
```

`reference commands` returns the complete recursive canonical command tree.

## Compatibility

Older specialist command names remain parseable where practical so existing scripts do not break immediately, but they are hidden from normal help and are not part of the LLM-facing contract. New automation should use only the canonical interface above.

## Testing

From the source tree, the normal regression gate is:

```bash
python -m pytest -q
```

`./run-compression-tests` is a separate asset/compression suite, not part of the normal rc11 gate. It was intentionally not rerun for this candidate. Official Creator/Viewer browser verification remains a separate release gate.
