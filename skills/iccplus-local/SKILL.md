---
name: iccplus-local
description: Use when working with native ICC Plus 2 projects.
---

# ICC Plus Local

Use this as the one general ICC Plus Local skill. Do not treat the files under `functions/` as separate installed skills. They are focused operating guides that this skill routes to when a task needs that function.

Current tool version: `0.10.0rc15`.
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

Normal writes fill missing official Creator defaults, run complete-project validation in memory, and then save the pinned sparse project representation. Do not add a separate validation pass after every write. Use `project validate` for the normal saved artifact and `project validate --complete` for the materialized Creator shape. `project hydrate` still writes sparse by default; add `--not-sparse` only when you need that materialized shape on disk.

Sparse saved projects must remain authoring-round-trip safe. Never omit a stable identity or non-derivable authoring value merely because the Viewer can ignore or regenerate an internal equivalent. In particular, Score `idx` and Sound Effect `name` remain in canonical sparse saves because later ICC Plus Local commands and hydration cannot safely invent them.

Local and embedded images are compressed automatically when assigned. Do not add a manual compression step to ordinary authoring.

## Compiler boundary

ICC Plus Local is the native ICC Plus compatibility, validation, serialization, and local-runtime layer. It should reproduce native behavior and validate native projects without guessing higher-level author intent.

Read `../../docs/COMPILER_BOUNDARY.md` before changing large-project normalization behavior.

The source compiler or lowering layer owns transformations that require semantic knowledge not present in arbitrary ICC Plus JSON. In particular, ICC Plus Local must not silently:

- remove redundant ancestor Requirements;
- promote identical Choice gates to a Row;
- deduplicate project styling into Design Groups;
- decide that source taxonomy should or should not become runtime Groups;
- merge one-card Rows or unrelated axes;
- infer Pick 1 / Pick N intent from presentation;
- compact public runtime IDs or remap a project's identity graph.

ICC Plus Local may validate the native output of those transformations. It may also report native facts such as `allowedChoices: 0` meaning unlimited, dangling references, malformed Requirements, or Creator-incomplete structure. The compiler decides how to fix source-level redundancy or layout.

## Native semantic rules relevant to compilers

A Row becoming hidden does not prove that selected children were deselected. Visibility and cleanup are separate mechanics. If provider loss should invalidate a child selection, the compiler must emit and test an explicit native cleanup mechanism.

`allowedChoices: 0` means unlimited. ICC Plus Local preserves and simulates that meaning. A source compiler that knows a Row is Pick 1 or Pick N should emit the real positive maximum instead of expecting the local runtime to infer intent.

Creator-complete fields remain part of native compatibility and are materialized for validation and explicit Creator operations. Normal saved project JSON may omit only fields covered by the pinned Viewer behavior-equivalence serializer and the authoring-round-trip contract. The compiler should still remove duplicated author intent before generation rather than using serialization omissions as a substitute for semantic normalization.

### ICC Plus 2.10.8 Addon changelog correction

Upstream 2.10.8 says “Change choices per row could not change addons per row.” The corresponding source change updates width application so selectable Addons use `addonWidth` while Rows and Choices use `objectWidth`. It is a layout-width fix, not evidence of a change to `allowedChoices` selection limits.

Do not use that changelog entry as justification for replacing tested selectable-Addon exclusion logic with Row selection limits. Such a replacement requires direct target-Viewer evidence for the actual mechanic.

## Styling rule

Use the broadest native ICC Plus scope that fits when directly authoring a native project: project-wide styling, then official Row/Choice Design Groups for reusable visual families, then private Row/Choice exceptions. Link Design Groups through ordinary ICC Groups when Group membership itself defines the visual family. Use custom CSS only when native ICC Plus styling cannot express the required presentation.

For source-driven projects, deciding when to consolidate repeated style intent is a compiler responsibility. ICC Plus Local only applies and validates the native styling operations it is given.

## Player-view rule

When using `play`, Rows, direct Choices, and Addons are separate entity types. The current player view exposes flat `rows`, `choices`, and `addons` lists plus explicit parent/child IDs. Do not reconstruct the hierarchy from the legacy nested compatibility field when the explicit links are available.

Test effective behavior rather than assuming a particular source-level transformation. Test cleanup separately because hidden selected state can persist.

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
- `COMPILER_BOUNDARY.md` for the boundary between native ICC Plus behavior and source-level lowering/normalization.
- `SPARSE_RUNTIME_SERIALIZATION.md` for sparse-save omissions and the authoring-round-trip invariant.
- `cyoa/guide/21-large-project-normalization.md` for compiler/build normalization guidance.

## Verification status

rc15 keeps the automated GitHub Actions regression gate and checks for the compressed CYOA skill/documentation package. Local simulation is not browser proof. Official Creator/Viewer verification remains a separate release gate for rendering, browser-only behavior, and target-version details that are not covered by source-derived local parity.
