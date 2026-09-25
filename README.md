# ICC Plus Local

ICC Plus Local is a local command-line authoring and mechanical-testing tool for ICC Plus 2 projects. The current source in this repository is ICC Plus Local 0.10.0rc12, targeting ICC Plus 2.10.7 and pinned to upstream source commit `1ea9db888cde2286d18d0d5de50933cb8773b739`.

It is an independent local implementation. The official ICC Plus Creator and Viewer remain the authority for browser rendering and behavior outside the local tool's verified coverage.

## What is included

- The ICC Plus Local Python source, schemas, tests, verification fixtures, and package metadata at the repository root.
- `skills/iccplus-local/`, the single general ICC Plus Local Agent Skill.
- `skills/iccplus-local/functions/`, its focused guides for the 11 canonical command families.
- `docs/`, the current ICC Plus Local documentation from the active CYOA New toolset.
- `docs/cyoa/`, generic CYOA authoring, audit, and blind-playtest guidance.
- The files under `examples/` provide tested rc11 command, selector, session, and automation examples.
- `examples/simple-cyoa/` is a small phased CYOA with builder scripts and a player-safe smoke test.
- `examples/main-cyoa-development/` is a validated standalone excerpt derived from the current 6.6.11 main CYOA.

The older collection of separate CYOA lifecycle skills is not included. Their ICC Plus Local responsibilities were consolidated into the current `iccplus-local` skill and its function guides.

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

`structure`, `rules`, and `style` fill missing official Creator defaults and require complete-project validation before replacing the target project. For an imported legacy project, `project validate` reports final-artifact completeness and `project hydrate` repairs missing official sections without inventing IDs. For styling, prefer project-wide native styling and official Row/Choice Design Groups; private per-entity styling is for genuine one-off exceptions. Image compression is automatic when local or embedded images are assigned through the current media/style workflow.

## Agent skill

Start with [`skills/iccplus-local/SKILL.md`](skills/iccplus-local/SKILL.md). It is the only ICC Plus Local skill in this repository.

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

- [`docs/CLI_REFERENCE.md`](docs/CLI_REFERENCE.md) for the canonical command tree.
- [`docs/LLM_USAGE.md`](docs/LLM_USAGE.md) for the agent workflow.
- [`docs/PHASED_AUTHORING.md`](docs/PHASED_AUTHORING.md) and [`docs/AUTHORING_SCRIPTS.md`](docs/AUTHORING_SCRIPTS.md) for structured edits.
- [`docs/FIELD_CATALOG.md`](docs/FIELD_CATALOG.md) and [`docs/ICCPLUS_FIELD_REFERENCE.md`](docs/ICCPLUS_FIELD_REFERENCE.md) for native fields.
- [`docs/PLAY_STRUCTURE.md`](docs/PLAY_STRUCTURE.md) for the rc11 player-visible Row, Choice, and Addon model.
- [`docs/GAMEPLAY_RUNNER.md`](docs/GAMEPLAY_RUNNER.md) for progressive player-safe tests.
- [`docs/VISUAL_WORKFLOW.md`](docs/VISUAL_WORKFLOW.md) for images and presentation work.
- [`COVERAGE.md`](COVERAGE.md) for the local simulator boundary.

Historical per-version audit reports are intentionally not carried in the working documentation set. Release history remains in [`RELEASE_NOTES.md`](RELEASE_NOTES.md).

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

`examples/main-cyoa-development/` is derived from the in-development 6.6.11 main CYOA. It preserves seven real species-builder rows, 26 real Choices, current IDs, player-facing text, and the original row selection limits. Cross-section Requirements, Scores, Groups, and generated relationships are deliberately omitted so the excerpt remains standalone and reproducible.

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

The current repository passes the full rc11 normal regression suite: **312 tests passed**. `./examples/test_examples.sh` also passes and covers the command fixtures, both continuation-state requests, the simple CYOA, and the main-CYOA development excerpt.

Local mechanical tests do not replace final checks in the official Creator or Viewer for browser rendering, responsive layout, CSS, animation, dialogs, network-loaded assets, or behavior outside documented local coverage.

## License

See [`LICENSE`](LICENSE).
