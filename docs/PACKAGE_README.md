# ICC Plus Local CLI

Version 0.10.0rc14 targets ICC Plus 2.10.7 and pins official ICC Plus Svelte commit `1ea9db888cde2286d18d0d5de50933cb8773b739`.

The canonical top-level interface has 11 commands:

```text
reference   discovery, schemas, fields, guides, parity
template    entity defaults, style presets, Creator design templates
media       images, crops, fonts, sound, asset inspection
project     validation, hydration, formatting, export/import, IDs, Build Form serialization
inspect     batched read-only project inspection
generate    exact blank Creator project
build       deterministic phased build
structure   Rows, Choices, Addons, text, IDs, ordering
rules       Points, Requirements, Scores, Groups, effects
style       images, templates, widths, styling
play        player-safe progressive testing and audit
```

A normal authoring flow is:

```bash
iccplus-local generate -o project.json
iccplus-local structure project.json @structure.json
iccplus-local rules project.json @rules.json
iccplus-local style project.json @style.json
iccplus-local play project.json
iccplus-local project validate project.json
iccplus-local project validate project.json --complete   # only for explicit Creator-complete artifacts
```

Normal `generate`, `build`, `structure`, `rules`, `style`, `apply`, and direct-edit writes hydrate missing official Creator defaults, require complete-project validation in memory, and then save the pinned sparse representation. Use `project hydrate` when you explicitly need a complete Creator artifact. Hydration preserves existing values, does not invent missing entity IDs, and does not downgrade a future project version.

Bulk edits use `items`, explicit `refs`, or selectors with `expect`. Preview selectors through `inspect` before broad writes.

For styling, prefer project-wide native styling, then official Row/Choice Design Groups. Private Row or Choice styling is for one-off exceptions. Use custom CSS only when native styling cannot express the result. Local and embedded image assignment handles compression automatically.

`play` is the canonical runtime/testing interface. It exposes visible Rows, direct Choices, and Addons separately with explicit parent/child links. Use `--state FILE` for private continuation state. See `PLAY_STRUCTURE.md` and `GAMEPLAY_RUNNER.md`.

## Runtime release serialization

Every full-project JSON output uses behavior-preserving sparse serialization by default, including hydrated/formatted JSON, separate-image export packages, and Viewer packages. Use `--not-sparse` only when a materialized project is explicitly required. The omission rules are pinned to ICC Plus 2.10.7 rather than inferred from schema optionality or Creator factory defaults.

Use `iccplus-sparse PROJECT -o runtime-project.json` when a standalone player runtime artifact is needed. Use `iccplus-omission-probe -o verification/sparse-omission` to generate isolated browser test cases for omission candidates that have not yet been proven safe. See `SPARSE_RUNTIME_SERIALIZATION.md` and `COMPILER_BOUNDARY.md`.

## CYOA skills

`skills/iccplus-local/SKILL.md` is the single native ICC Plus 2 implementation skill. The repository also includes the high-level `cyoa-plan`, `cyoa-review`, `cyoa-migrate`, `cyoa-develop`, `cyoa-ship`, and exceptional `cyoa-compress` skills.

The old `cyoa-create`, `cyoa-edit`, `cyoa-look`, and `cyoa-test` wrappers are intentionally absent. Their implementation work is covered by ICC Plus Local.

The complete CYOA guide lives under `docs/cyoa/guide/`.

## Testing

Run:

```bash
python -m pytest -q tests cli_tests
./examples/test_examples.sh
```

GitHub Actions runs the core suite, CLI contract, and checked-in examples as separate jobs so failures remain attributable. Pushes to `main` also build the wheel, source ZIP, and SHA-256 file.

Official Creator/Viewer browser verification remains a separate release gate for rendering and browser-only behavior.
