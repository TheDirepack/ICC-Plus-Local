# ICC Plus Local

**Version 0.10.0rc15**

ICC Plus Local is a local command-line authoring and mechanical-testing tool for ICC Plus 2 projects. The current source in this repository is ICC Plus Local 0.10.0rc15, targeting ICC Plus 2.10.7 and pinned to upstream source commit `1ea9db888cde2286d18d0d5de50933cb8773b739`.

It is an independent local implementation. The official ICC Plus Creator and Viewer remain the authority for browser rendering and behavior outside the local tool's verified coverage.

## What is included

- The ICC Plus Local Python source, schemas, tests, verification fixtures, and package metadata at the repository root.
- `skills/iccplus-local/`, the single native ICC Plus 2 implementation skill.
- `skills/iccplus-local/functions/`, focused guides for the 11 canonical command families.
- `skills/cyoa-plan/`, `cyoa-review/`, `cyoa-migrate/`, `cyoa-develop/`, `cyoa-ship/`, and `cyoa-compress/`, the retained high-level CYOA skills whose work is not replaced by the CLI.
- `docs/`, the current ICC Plus Local documentation.
- `docs/cyoa/guide/`, the complete generic CYOA design, authoring, testing, and release guide.
- `docs/cyoa/legacy/`, the legacy ICC migration reference used by `cyoa-migrate`.
- `docs/cyoa/`, generic audit rules, authoring rules, skill usage, and playtest prompts.
- The files under `examples/` provide tested command, selector, continuation-state, and automation examples.
- `examples/simple-cyoa/` is a small phased CYOA with builder scripts and a player-safe smoke test.
- `examples/main-cyoa-development/` is a validated standalone excerpt derived from the current 6.6.11 main CYOA.

The old wrapper skills `cyoa-create`, `cyoa-edit`, `cyoa-look`, and `cyoa-test` are intentionally absent. Native ICC Plus 2 creation, editing, styling, media work, validation, and mechanical playtesting are consolidated into `iccplus-local`. Planning, review, migration, long-project coordination, release work, and exceptional external compression remain separate because they add work outside the CLI itself.

## Quick start

Discover the installed command surface before scripting against it:

```bash
python -m iccplus_tools reference capabilities --brief
python -m iccplus_tools reference commands
```

A normal authoring flow is:

```bash
python -m iccplus_tools generate -o project.json
python -m iccplus_tools structure project.json @structure.json
python -m iccplus_tools rules project.json @rules.json
python -m iccplus_tools style project.json @style.json
python -m iccplus_tools play project.json
```

`generate`, `build`, `structure`, `rules`, `style`, `apply`, and ordinary direct edits use the normal sparse saved-project form. Before every valid write, ICC Plus Local hydrates a complete in-memory project and requires complete-project validation. It then omits only fields that are safe under the pinned 2.10.7 Viewer rules and the authoring-round-trip contract. Stable identities and non-derivable authoring values remain serialized when later commands need them. In particular, canonical sparse saves retain Score `idx` and Sound Effect `name`.

`project validate` checks the normal sparse/compatible form, while `project validate --complete` checks a materialized full shape. Every full-project JSON write remains sparse unless that specific command is given `--not-sparse` (the alias `--not_sparse` is also accepted). For styling, prefer project-wide native styling and official Row/Choice Design Groups; private per-entity styling is for genuine one-off exceptions. Image compression is automatic when local or embedded images are assigned through the current media/style workflow.

Every full-project JSON output uses the same pinned sparse serializer by default, including normal saves, hydration output, formatting, separate-image export packages, and Viewer packages. A materialized/non-sparse project is written only when the producing command is given `--not-sparse` (or `--not_sparse`). `iccplus-sparse` writes the same sparse representation directly, while `iccplus-omission-probe` generates isolated pinned-Viewer verification cases for omissions that are not yet proven safe.

## Agent skill

For native ICC Plus 2 project work, start with [`skills/iccplus-local/SKILL.md`](skills/iccplus-local/SKILL.md). It is the single implementation skill. Use the retained high-level CYOA skills only for planning, review, migration, long-project coordination, final release work, or exceptional external compression.

The skill routes the task to one or more files under `skills/iccplus-local/functions/`:

| Task | Guide | Command |
| --- | --- | --- |
| Discover commands, fields, schemas, types, guides, parity data, or symbols | `reference.md` | `reference` |
| Inspect or search an existing project | `inspect.md` | `inspect` |
| Create a blank project | `generate.md` | `generate` |
| Rebuild from an ordered manifest | `build.md` | `build` |
| Edit Rows, Choices, Addons, text, IDs, or ordering | `structure.md` | `structure` |
| Edit Points, Scores, Requirements, Groups, costs, limits, or effects | `rules.md` | `rules` |
| Edit presentation, templates, widths, or images | `style.md` | `style` |
| Playtest or audit player-visible behavior | `play.md` | `play` |
| Work with entity or design templates | `template.md` | `template` |
| Work with images, crops, fonts, sounds, or asset inspection | `media.md` | `media` |
| Format, export, fragment, serialize, or work with IDs | `project.md` | `project` |

The function files are reference material for the one skill. They are not separate installed skills.

## Documentation

Start with these files when more detail is needed:

- [`docs/cyoa/guide/00-index.md`](docs/cyoa/guide/00-index.md) for the full CYOA design and implementation guide.
- [`docs/cyoa/skills-usage.md`](docs/cyoa/skills-usage.md) for the compressed skill-routing model.
- [`docs/CLI_REFERENCE.md`](docs/CLI_REFERENCE.md) for the canonical command tree.
- [`docs/LLM_USAGE.md`](docs/LLM_USAGE.md) for the agent workflow.
- [`docs/PHASED_AUTHORING.md`](docs/PHASED_AUTHORING.md) and [`docs/AUTHORING_SCRIPTS.md`](docs/AUTHORING_SCRIPTS.md) for structured edits.
- [`docs/FIELD_CATALOG.md`](docs/FIELD_CATALOG.md) and [`docs/ICCPLUS_FIELD_REFERENCE.md`](docs/ICCPLUS_FIELD_REFERENCE.md) for native fields.
- [`docs/PLAY_STRUCTURE.md`](docs/PLAY_STRUCTURE.md) for the current player-visible Row, Choice, and Addon model.
- [`docs/GAMEPLAY_RUNNER.md`](docs/GAMEPLAY_RUNNER.md) for progressive player-safe tests.
- [`docs/VISUAL_WORKFLOW.md`](docs/VISUAL_WORKFLOW.md) for images and presentation work.
- [`docs/COMPILER_BOUNDARY.md`](docs/COMPILER_BOUNDARY.md) for the source-compiler versus ICC Plus Local ownership boundary.
- [`docs/SPARSE_RUNTIME_SERIALIZATION.md`](docs/SPARSE_RUNTIME_SERIALIZATION.md) for the default sparse-save policy, authoring-round-trip invariant, and browser-verification queue.
- [`COVERAGE.md`](COVERAGE.md) for the local simulator boundary.

Historical per-version audit reports are retained as evidence and labeled by the version they audited. Current workflow instructions live in the non-historical docs and [`RELEASE_NOTES.md`](RELEASE_NOTES.md).

## Examples

Run every checked-in example from the repository root:

```bash
./examples/test_examples.sh
```

The command fixtures directly under `examples/` cover `inspect`, `structure`, `rules`, `style`, `play`, bounded selectors, private continuation state, and a Python subprocess client. Edit examples use `--dry-run` where appropriate.

### Simple CYOA

The small example under `examples/simple-cyoa/` shows a reproducible phased build rather than a project-specific compiler.

```bash
cd examples/simple-cyoa
./build.sh
```

Or:

```bash
python build.py
```

The scripts build `build/project.json` from the phase files in `project-src/` and run the player-safe test in `tests/playtest.json`.

### Main CYOA development excerpt

`examples/main-cyoa-development/` is an earlier development excerpt derived from the 6.6.11 main CYOA. It preserves seven real species-builder rows, 26 real Choices, current IDs, player-facing text, and the original row selection limits. Cross-section Requirements, Scores, Groups, and generated relationships are deliberately omitted so the excerpt remains standalone and reproducible.

```bash
cd examples/main-cyoa-development
./build.sh
```

## Reference projects

ICC Plus Local was developed with these public projects and sources as references:

- [ICC Plus](https://github.com/wahaha303/ICCPlus), the official deployment and distribution repository.
- [ICC Plus 2 source](https://github.com/wahaha303/ICC-Plus-Svelte), the official Creator and Viewer source repository.
- [ICCPlus-MCP](https://github.com/TheDirepack/ICCPlus-MCP), a schema-aware MCP implementation for agent-driven ICC Plus work.
- [AVIF CYOA Compressor](https://github.com/blathers16/avif-cyoa-compressor), a public image-compression reference used while developing the compression workflow.
- [Agregen's CYOA Compressor](https://agregen.gitlab.io/cyoa-compressor/README.html), another workflow reference for CYOA asset compression.
- [Interactive CYOA Tutorial](https://github.com/upasadena/interactive-cyoa-tutorial), a useful legacy ICC reference. It is not the authority for ICC Plus 2 behavior.

For prose cleanup, the recommended external companion is the [Unslop skill](https://github.com/backnotprop/pstack/tree/main/skills/unslop). Unslop is not bundled in this repository.

## Verification

rc15 keeps the ICC Plus 2.10.7 engine target and pinned source commit unchanged. It includes the expanded sparse omission audit and makes sparse JSON the normal project representation while preserving authoring identities and labels needed across commands. The GitHub Actions workflow is authoritative for the current candidate; browser-only omission cases remain separate pinned-Viewer verification work until promoted by evidence.

Local mechanical tests do not replace final checks in the official Creator or Viewer for browser rendering, responsive layout, CSS, animation, dialogs, network-loaded assets, or behavior outside documented local coverage.

## License

See [`LICENSE`](LICENSE).