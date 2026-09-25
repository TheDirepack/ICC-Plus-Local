# Command-line scripting

The canonical automation path is JSON-first. Use `inspect` for batched reads. Use `structure`, `rules`, and `style` for writes. Captured normal output is compact JSON by default.

```bash
iccplus-local reference capabilities --brief
iccplus-local reference schema list
iccplus-local reference schema structure-ops
iccplus-local reference schema rules-ops
iccplus-local reference schema style-manifest
```

## Create and edit

```bash
iccplus-local generate -o project.json
iccplus-local structure project.json @10-structure.json
iccplus-local rules project.json @20-rules.json
iccplus-local style project.json @90-style.json
```

Each phase command validates its own smaller input contract and rejects fields owned by another phase.

## Repeatable source tree

```bash
iccplus-local build project-src/iccplus.build.json -o build/project.json
```

Use an `iccplus-build` version 2 manifest. Every step declares `structure`, `rules`, `style`, or explicit `raw`. Build output is written only after every step and final validation succeed.

## Preflight and inspection

```bash
iccplus-local inspect project.json @inspect.json
```

Normal writes validate automatically. Use an `inspect` query with `op: "check"` when you specifically need a read-only validation report, and `op: "ids"` for the identity inventory.

## Preview a bulk selector

Put a `match` query in the same `inspect` request used for other discovery. Keep the same `expect` count in the following phase operation. A stale selector then fails before writing.

## Uncommon fields

Use `reference fields` and the phase schemas before assuming a native field needs a compatibility path. New automation should write through `structure`, `rules`, or `style`. Hidden compatibility aliases are for old scripts and are not part of the current contract.

A failed atomic phase operation writes nothing. Malformed input returns exit code 1. Validation failure returns exit code 2.

## Continuous session files

```bash
iccplus-local play project.json @audit.json --state .state/build-a.json
iccplus-local play project.json --state .state/build-a.json --select perk_x
```

For an LLM acting as a player, prefer `play`. It keeps private continuation state out of the model-facing response.

## Images

Image optimization is automatic when local or embedded images are assigned through `style` or `media`. Scripts do not run a separate compression pass.

## CI gate

```bash
iccplus-local play project.json @tests/core-paths.json --state .state/core-paths.json
iccplus-local play project.json @tests/boundaries.json --state .state/boundaries.json
```

## Exit codes

- `0` means success.
- `1` means malformed input, usage, bad file, or another command/input error.
- `2` means static validation or preflight failed.
- `3` means a runtime action or scenario assertion failed.
- `4` means an accepted atomic phase or generic operation failed. No partial batch is written.

## Machine-readable files

- `schemas/build-manifest.schema.json`
- `schemas/structure-operation-script.schema.json`
- `schemas/rules-operation-script.schema.json`
- `schemas/visual-manifest.schema.json`
- `schemas/agent-operation-script.schema.json`
- `schemas/inspect-request.schema.json`
- `schemas/operation-script.schema.json`
- `schemas/session-request.schema.json`
- `schemas/runtime-state.schema.json`
- `tool.schema.json`
