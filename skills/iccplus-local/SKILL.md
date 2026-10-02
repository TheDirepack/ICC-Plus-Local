---
name: iccplus-local
description: Use when working with native ICC Plus 2 projects.
---

# ICC Plus Local

Use this as the one general ICC Plus Local skill. Do not treat the files under `functions/` as separate installed skills. They are focused operating guides that this skill routes to when a task needs that function.

Current tool version: `0.10.0rc13`.
Target ICC Plus version: `2.10.7`.

## How to use this skill

First identify the function the task needs. Read only the matching file or files under `functions/`, then perform the work. A task may need more than one function guide.

| Task | Function guide | Canonical command |
| --- | --- | --- |
| Discover commands, fields, schemas, types, guides, parity data, or symbols | `functions/reference.md` | `reference` |
| Read or search an existing project without changing it | `functions/inspect.md` | `inspect` |
| Create a new blank ICC Plus project | `functions/generate.md` | `generate` |
| Rebuild a project from an ordered build manifest | `functions/build.md` | `build` |
| Add, edit, move, clone, order, merge, or remove Rows, Choices, and Addons | `functions/structure.md` | `structure` |
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

For broad edits, prefer batched `items`, explicit `refs`, or selectors. Add `expect` when the number of matches matters.

Normal writes fill missing official Creator defaults and run complete-project validation before replacing the project. Do not add a separate validation pass after every write. Use `project validate` before final handoff/export of an externally supplied legacy project, and `project hydrate` when missing official baseline fields need repair.

Local and embedded images are compressed automatically when assigned. Do not add a manual compression step to ordinary authoring.

## Large-project normalization rules

For a compiler-driven or otherwise source-driven project, normalize the semantic model before trying to reduce raw JSON bytes. Read `../../docs/cyoa/guide/21-large-project-normalization.md` before a large structural or release-compaction pass.

Use these defaults unless the project has a tested reason not to:

- Keep readable semantic IDs in the authoritative source.
- Treat generated `project.json` as output, not a second editable master.
- Put ordinary presentation in project styling; use official Design Groups for reusable exceptions; use private styling only for real one-offs.
- Prefer linking a Design Group through an existing semantic ICC Group instead of repeating the Design Group ID on every member.
- Hide a branch at the deepest Row that owns the gate. A Mouth detail Row should normally require Mouth, not Mouth plus Head plus Species plus every ancestor.
- If every Choice in a multi-Choice Row has the same visibility Requirement, promote that Requirement to the Row once. Keep Choice-level gates only when choices inside the visible Row genuinely differ.
- Do not confuse visibility with cleanup. A Row becoming hidden does not prove already selected children were deselected.
- Set `allowedChoices` to the real maximum for Pick 1 / Pick N direct-Choice Rows. `0` means unlimited.
- Merge one-card Rows only when the neighboring Row has compatible visibility, selection limits, layout role, and explanatory text.
- Keep source-only semantic tags out of runtime Groups unless some runtime feature consumes the Group.
- If a release pipeline compacts runtime identities, make the mapping deterministic, stable, reversible, and complete. Never randomize public runtime IDs on every build.

### Target-version caveat: selectable Addons

The current tool target is ICC Plus 2.10.7. Do not assume Row choice limits can replace selectable-Addon radio/exclusion logic on this target. Upstream 2.10.8 specifically fixed an issue where changing choices per Row could not change Addons per Row. Keep a verified explicit Addon mechanism until the project target is upgraded and tested.

## Styling rule

Use the broadest native ICC Plus scope that fits. Start with project-wide styling, then use official Row/Choice Design Groups for reusable visual families. Link Design Groups through ordinary ICC Groups when Group membership itself defines the visual family. Use private Row styling only for a true one-Row exception, and private Choice styling only for a true one-Choice exception when neither project styling nor a Design Group fits. Do not duplicate the same inline styling across many Choices. Use custom CSS only when native ICC Plus styling cannot express the required presentation.

## Player-view rule

When using `play`, Rows, direct Choices, and Addons are separate entity types. The current player view exposes flat `rows`, `choices`, and `addons` lists plus explicit parent/child IDs. Do not reconstruct the hierarchy from the legacy nested compatibility field when the explicit links are available.

For normalized projects, test effective behavior rather than old physical storage. A gate promoted from every Choice to its Row is still the same player rule if the visible and selectable states match. Conversely, test cleanup separately because hidden selected state can persist.

Read `functions/play.md` before doing player simulation or play audits. The full data model is documented in `../../docs/PLAY_STRUCTURE.md`.

## Documentation

The function guides are short operating instructions. Use the complete documentation under `../../docs/` when a task needs field-level detail, schemas, recipes, coverage information, or release evidence.

Use `references/local-workflow-checklist.md` for a compact preflight and handoff checklist.

Useful starting documents include:

- `CLI_REFERENCE.md` for the command tree.
- `PLAY_STRUCTURE.md` for the current Row, Choice, and Addon player-view model.
- `GAMEPLAY_RUNNER.md` for play audits.
- `LLM_USAGE.md` for the broader agent workflow.
- `PHASED_AUTHORING.md` and `AUTHORING_SCRIPTS.md` for edits.
- `FIELD_CATALOG.md` and `ICCPLUS_FIELD_REFERENCE.md` for native fields.
- `cyoa/guide/21-large-project-normalization.md` for structural normalization and release compaction.

## Verification status

rc13 keeps the automated GitHub Actions regression gate and checks for the compressed CYOA skill/documentation package. Official Creator/Viewer browser verification remains a separate release gate, especially for rendering, selectable-Addon target-version behavior, and the fresh 2.10.7 browser round-trip.
