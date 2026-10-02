# ICC Plus Local 0.10.0rc14 handoff

The engine target remains ICC Plus 2.10.7, pinned to upstream commit `1ea9db888cde2286d18d0d5de50933cb8773b739`.

Use the workflow-centered ICC Plus Local interface:

```text
generate -> structure -> rules -> style -> play
```

Use `inspect` for read-only project discovery. Use `reference commands` for the complete command tree, `reference fields` for native fields, and `reference schema` for machine-readable contracts. Template operations live under `template`, media under `media`, and project validation, hydration, serialization, import, and export under `project`.

Normal project writes hydrate official Creator defaults and require complete-project validation in memory, then save the proven-safe sparse representation. Use `project validate` for the normal sparse/compatibility check and `project validate --complete` when you explicitly need to check the full Creator shape. `project hydrate` reconstructs that shape in memory without inventing missing IDs but still saves sparse unless `--not-sparse` is supplied.

For styling, use project styling first, then official Row/Choice Design Groups. Use private Row or Choice styling only for genuine one-off exceptions. Use custom CSS only when native ICC Plus styling cannot express the result.

`play` is the player-safe simulator and audit interface. It exposes visible Rows, direct Choices, and Addons as separate structures with explicit parent/child links. Keep continuation state private with `--state FILE`.

## Runtime release serialization

Every full-project JSON output uses the pinned behavior-preserving sparse serializer by default. Formatting, hydration, separate-image exports, and Viewer packages are also sparse unless the producing command explicitly uses `--not-sparse`. `iccplus-sparse` can write the sparse artifact directly, and `iccplus-omission-probe` generates isolated Viewer tests for fields whose omission is not yet proven safe. Read `docs/SPARSE_RUNTIME_SERIALIZATION.md` before extending the omission set.

Sparse runtime serialization is a native ICC Plus serialization concern. Source semantic normalization—Requirement hoisting, Row merging, taxonomy pruning, style-intent consolidation, Pick-N inference, and deterministic runtime-ID remapping—belongs in the source compiler/lowering layer. Read `docs/COMPILER_BOUNDARY.md`.

## CYOA skill routing

Use `skills/iccplus-local/SKILL.md` for native ICC Plus 2 creation, editing, styling, media work, validation, building, serialization, and mechanical playtesting.

Use the retained high-level skills only when the task adds work outside the CLI:

- `cyoa-plan` for design and major redesign.
- `cyoa-review` for design, balance, content, and implementation audits.
- `cyoa-migrate` for legacy ICC or ICC Plus 1.x conversion.
- `cyoa-develop` for long multi-pass or multi-session coordination.
- `cyoa-ship` for final packaging and release QA.
- `cyoa-compress` only for an exceptional external or legacy asset tree outside the normal media workflow.

The retired wrappers `cyoa-create`, `cyoa-edit`, `cyoa-look`, and `cyoa-test` must not be reintroduced.

Start CYOA documentation at `docs/cyoa/guide/00-index.md`. For the current player hierarchy, read `docs/PLAY_STRUCTURE.md`; `docs/GAMEPLAY_RUNNER.md` covers progressive play audits.
