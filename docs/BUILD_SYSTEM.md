# Build system

ICC Plus Local uses the official blank Creator export as the only starting point. `generate` creates that blank file. Authoring happens through edit tools.

```bash
iccplus-local generate -o project.json
iccplus-local structure project.json @10-structure.json
iccplus-local rules project.json @20-rules.json
iccplus-local style project.json @90-style.json
```

The phase split is part of the safety model. A phase command rejects fields and operations that belong to another phase.

## Structure phase

`structure` creates and organizes the visible content tree. Use it for Rows, Choices, Addons, IDs, titles, text, ordering, moving, and cloning.

A structure file uses `iccplus-structure-ops` version 1.

```json
{
  "format": "iccplus-structure-ops",
  "format_version": 1,
  "strict_fields": true,
  "operations": [
    {"op": "add", "kind": "row", "values": {"id": "row_origin", "title": "Origin"}},
    {"op": "add", "kind": "choice", "parent": "row_origin", "values": {"id": "origin_human", "title": "Human", "text": "Baseline."}}
  ]
}
```

The structure phase rejects gameplay fields such as `scores`, `requireds`, and `allowedChoices`. It also rejects style fields such as `image`, `template`, width, and `styling`.

## Rules phase

`rules` owns gameplay mechanics. Use it for Point Types, Scores, Requirements, selection limits, Groups, Variables, Words, gating, costs, and Choice effects.

A rules file uses `iccplus-rules-ops` version 1.

```json
{
  "format": "iccplus-rules-ops",
  "format_version": 1,
  "strict_fields": true,
  "operations": [
    {"op": "add", "kind": "point", "values": {"id": "budget", "name": "Budget", "startingSum": 10}},
    {"op": "update", "kind": "row", "ref": "row_origin", "values": {"allowedChoices": 1}},
    {"op": "score_many", "target": "origin_human", "point": "budget", "value": -2}
  ]
}
```

The rules phase rejects section title and text changes. It also rejects visual styling fields. Advanced native fields that are not part of the phase interface can still be written with low-level `apply` when needed.

## Style phase

`style` applies the existing `iccplus-visual-manifest` format. Use it for images, templates, widths, inline native styling, project styling, CSS, and reusable visual presets.

```json
{
  "format": "iccplus-visual-manifest",
  "format_version": 1,
  "items": [
    {"ref": "origin_human", "template": 2, "width": 4}
  ]
}
```

The style tool does not edit Requirements, Scores, or other mechanics.

## Repeatable builds

Version 2 build manifests declare every phase.

```json
{
  "format": "iccplus-build",
  "format_version": 2,
  "steps": [
    {"name": "sections", "phase": "structure", "script": "10-structure.json"},
    {"name": "mechanics", "phase": "rules", "script": "20-rules.json"},
    {"name": "presentation", "phase": "style", "script": "90-style.json"}
  ]
}
```

Run it with:

```bash
iccplus-local build project-src/iccplus.build.json -o build/project.json
```

The build starts from a new blank project in memory. It runs each phase in order, validates the final project, and writes the output only when the whole build succeeds.

A `raw` phase is available for an exceptional edit that needs canonical `iccplus-agent-ops`. Keep raw steps small and documented. They are an escape hatch, not the normal authoring path.

Version 1 manifests remain readable for compatibility. Every version 1 step is treated as a raw `iccplus-agent-ops` step.

## File rules

Step paths are relative to the manifest. Absolute paths and paths that escape the manifest directory are rejected. A script cannot appear twice in one manifest.

The build receipt records each step phase and SHA-256, the tool and ICC Plus versions, a build fingerprint, the final project fingerprint, a project summary, and final validation.

## Suggested source layout

```text
project-src/
  iccplus.build.json
  10-structure.json
  20-rules.json
  90-style.json
  99-raw-fix.json       # only when required
build/
  project.json
```

Keep files grouped by responsibility. Do not split them based on the order an LLM happened to make edits.
