# Portable session protocol

The portable runtime state lets a headless ICC Plus run continue across processes, scripts, tool calls, or LLM turns.

## State versus snapshot

A snapshot is an internal inspection result. It can contain hidden engine state and optional next-choice validity information. It is not a player observation.

A runtime state is a continuation object. It includes hidden bookkeeping required to reverse or extend previous effects correctly.

Only `runtime_state` should be used to resume a run.

## State document

The top level contains:

- `format`: `iccplus-cyoa-runtime-state`;
- `format_version`: currently `1`;
- `tool_version`;
- `project_fingerprint`;
- `project_version` when present in the project;
- `seed`;
- `rng_state`;
- `runtime`.

The runtime object contains selections, points, variables, words, row counts, selection order, forced and non-locking activation-provider relationships, score ledgers, dynamic row-limit deltas, runtime hidden-content flags, `showAllAddons` state, and point-effect ledgers.

Event history is optional. It is not required for continuation and is excluded by default so long sessions do not grow without bound.

## Project fingerprint

The fingerprint is SHA-256 over canonical JSON for the full loaded project. A state normally loads only against the exact same project contents.

This is intentionally strict. A title change also changes the fingerprint. The local runner cannot know that a project edit is harmless to an already-running build.

For deliberate compatibility experiments, `--allow-project-mismatch` disables this check. Do not use it for ordinary play or regression testing.

## Random behavior

The Python random generator state is serialized. Given the same project and saved runtime state, later seeded random score operations continue the same random sequence as an uninterrupted run.

This does not make browser-only random effects fully simulated. Random forced-activation pools remain outside exact coverage in this release.

## CLI continuation

For LM player testing, use the one-action `play` command. It keeps continuation in a file and returns only the player-safe action result plus the current player view:

```bash
iccplus-local play project.json --state run.json --select a --compact
iccplus-local play project.json --state run.json --select c --compact
```

When `run.json` already exists, `play` resumes it automatically. The file is replaced atomically and uses owner-only permissions where supported. Do not read it into the LM context. If the file is damaged, `play` returns a sanitized `state.invalid` result and does not rewrite it. `play --reset` skips the old file and replaces it with a clean state.

For ordered multi-action batches or internal testing, ordinary `session` can return the full runtime state in stdout. `--state-in` may point to either a raw runtime-state document or a complete ordinary session response. In the second case the command extracts `runtime_state`. `session --player-safe` remains available when a caller needs a batched safe response.

Use `state-check project.json run.json` to verify a state without changing it. Import checks the project fingerprint, scalar types, finite numbers, selection order, Row counts, known activation IDs, variable activation consistency, and the internal ledgers needed for continuation.

## In-memory continuation

```python
sim = Simulator(project, seed=0)
sim.select("a")
state = sim.export_state()

resumed = Simulator.from_state(project, state)
resumed.select("b")
```

## Player-safe response

`--player-safe` is for an LM that should observe only what the player can use. It sanitizes select and deselect results, returns safe status data, and passes `view` results through the normal player boundary. It omits `snapshot`, `runtime_state`, `project_fingerprint`, and raw event details from stdout. A `snapshot` action is rejected in this mode.

Hidden and nonexistent guessed targets both return `player.unavailable`. This prevents ID probing from distinguishing hidden content from content that does not exist. Unknown future semantic codes receive a generic safe message rather than an internal runtime message.

Use `play --state FILE` or `session --state-out FILE` for continuation. The state file is machine-owned and may contain hidden mechanics. The LM should pass the path back to the tool, not read the file.

## Session response

The `session` command returns:

```json
{
  "ok": true,
  "project_fingerprint": "sha256:...",
  "results": [],
  "snapshot": {},
  "runtime_state": {}
}
```

`ok` becomes false when a requested select or deselect action returns an event with `ok: false`. The command stops at that action and exits with status 3. The rejected mutation is transactional, so `snapshot` and `runtime_state` contain the state from before that failed action. The event contains a stable semantic `code` and supporting details.

Malformed input, bad files, or invalid state documents used by normal commands exit with status 1 and print an error object to stderr. `state-check` instead returns a JSON validation report and exit status 2 for an invalid state.

## Save files

A state file is intended to be machine-owned. `play` and `session --state-out` use atomic replacement so an interrupted write is less likely to destroy the previous session. They also request mode `0600` where the operating system supports POSIX permissions. Store player notes separately. If human-readable notes are needed, keep the state filename or project fingerprint in the notes so the relationship is explicit.

## Player view inside a session

Add a `view` action when a script needs the current Viewer-like surface without starting another process:

```json
{
  "actions": [
    {"action": "select", "id": "origin_mage"},
    {"action": "view", "verbose": true}
  ]
}
```

The equivalent quick flag is `--verbose-view`. Images are never included. Hidden content is omitted.


In rc11, the safe view exposes `rows`, `choices`, and `addons` separately. Rows link to direct Choices through `choice_ids`; Choices link back through `row_id` and link to Addons through `addon_ids`; Addons expose `choice_id` and `row_id`. This same structure is returned whether continuation happens in one process or across saved state files. See `PLAY_STRUCTURE.md` for the complete field contract.
