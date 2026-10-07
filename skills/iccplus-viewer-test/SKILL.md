# ICC Plus Viewer Test

Use this skill when the task is to test or audit an existing ICC Plus project from the player/Viewer side.

This distribution is intentionally **not** an authoring environment. Do not use it to create, edit, style, generate, package, or otherwise build a CYOA.

## Workflow

1. Read `../../VIEWER_TEST_README.md` and `../../docs/PLAY_STRUCTURE.md`.
2. Use `iccplus-viewer-test view PROJECT` to inspect the clean player-visible state.
3. Use `status` for one selectable entity, `row-visible` for cheap Row-gating assertions, and `scenario` for deterministic action sequences.
4. Keep the no-leak boundary: judge what a player can actually see and do, rather than using hidden Requirements as the answer.
5. For blind audits, follow `../../docs/cyoa/prompts/blind-playtest.md` before inspecting project internals elsewhere.
6. Treat browser-only layout, CSS, media, dialogs, animation, and network behavior as outside the local simulator unless separately verified in the official Viewer.

## Relevant references

- `../../COVERAGE.md`
- `../../docs/GAMEPLAY_RUNNER.md`
- `../../docs/PLAY_STRUCTURE.md`
- `../../docs/SESSION_PROTOCOL.md`
- `../../docs/TESTING.md`
- `../../docs/VISIBILITY_AND_HIDING.md`
- `../../docs/UPSTREAM_PARITY_AUDIT.md`
- `../../docs/EXTERNAL_UPSTREAM_VERIFICATION.md`
- `../../docs/cyoa/guide/02-creator-and-viewer.md`
- `../../docs/cyoa/guide/11-balance-and-playtesting.md`
- `../../docs/cyoa/guide/17-local-testing.md`
- `../../docs/cyoa/guide/18-continuing-playtests.md`
- `../../docs/cyoa/prompts/blind-playtest.md`
