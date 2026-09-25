---
name: iccplus-local
description: Use when authoring, inspecting, testing, auditing, exporting, or otherwise working with ICC Plus 2.10.6 CYOA projects through ICC Plus Local 0.10.0rc11. This is the single general skill. Read the matching function guide under functions/ for the operation being performed.
---

# ICC Plus Local

Use this as the one general ICC Plus Local skill. Do not treat the files under `functions/` as separate installed skills. They are focused operating guides that this skill routes to when a task needs that function.

Current tool version: `0.10.0rc11`.
Target ICC Plus version: `2.10.6`.

## How to use this skill

First identify the function the task needs. Read only the matching file or files under `functions/`, then perform the work. A task may need more than one function guide.

| Task | Function guide | Canonical command |
| --- | --- | --- |
| Discover commands, fields, schemas, types, guides, parity data, or symbols | `functions/reference.md` | `reference` |
| Read or search an existing project without changing it | `functions/inspect.md` | `inspect` |
| Create a new blank ICC Plus project | `functions/generate.md` | `generate` |
| Rebuild a project from an ordered build manifest | `functions/build.md` | `build` |
| Add, edit, move, clone, order, or remove Rows, Choices, and Addons | `functions/structure.md` | `structure` |
| Change Points, Scores, Requirements, Groups, limits, costs, activation, or gameplay logic | `functions/rules.md` | `rules` |
| Change styling, widths, templates, images, or presentation | `functions/style.md` | `style` |
| Playtest, continue a player session, or audit player-visible behavior | `functions/play.md` | `play` |
| Work with entity defaults, style presets, or design import/export | `functions/template.md` | `template` |
| Import, clear, crop, inspect, or manage images, fonts, or sounds | `functions/media.md` | `media` |
| Format, export, fragment, serialize, or work with IDs/build strings | `functions/project.md` | `project` |

For example, a task that adds Choices with Requirements and then tests them should read `structure.md`, `rules.md`, and `play.md`. A task that only searches the project should read `inspect.md` and nothing else unless discovery is needed.

## General rules

Use only the canonical top-level commands for new work: `reference`, `template`, `media`, `project`, `inspect`, `generate`, `build`, `structure`, `rules`, `style`, and `play`. Hidden compatibility aliases exist for older scripts, but new automation should not emit them.

Inspect before editing an unfamiliar project. Use `reference` when the tool or schema is unclear rather than guessing field names or command shapes.

Keep phase boundaries clear. Structure changes belong in `structure`, gameplay logic belongs in `rules`, and presentation belongs in `style`. Use `project` only for interchange and serialization work.

Normal writes validate before replacing the project. Do not add a separate validation pass after every write unless the task calls for one or a function guide says it is needed.

For broad edits, prefer batched `items`, explicit `refs`, or selectors. Add `expect` when the number of matches matters.

Local and embedded images are compressed automatically when assigned. Do not add a manual compression step to ordinary authoring.

## Player-view rule

When using `play`, Rows, direct Choices, and Addons are separate entity types. The rc11 player view exposes flat `rows`, `choices`, and `addons` lists plus explicit parent/child IDs. Do not reconstruct the hierarchy from the legacy nested compatibility field when the explicit links are available.

Read `functions/play.md` before doing player simulation or play audits. The full data model is documented in `../../docs/PLAY_STRUCTURE.md`.

## Documentation

The function guides are short operating instructions. Use the complete documentation under `../../docs/` when a task needs field-level detail, schemas, recipes, coverage information, or release evidence.

Useful starting documents include:

- `CLI_REFERENCE.md` for the command tree.
- `PLAY_STRUCTURE.md` for the rc11 Row, Choice, and Addon player-view model.
- `GAMEPLAY_RUNNER.md` for play audits.
- `LLM_USAGE.md` for the broader agent workflow.
- `PHASED_AUTHORING.md` and `AUTHORING_SCRIPTS.md` for edits.
- `FIELD_CATALOG.md` and `ICCPLUS_FIELD_REFERENCE.md` for native fields.

## Verification status

The rc11 normal regression suite is `312 passed`. Compression tests were intentionally skipped for this rc11 documentation/skill update. Installed-wheel smoke testing passed against the active CYOA. Official Creator/Viewer browser verification remains a separate release gate.
