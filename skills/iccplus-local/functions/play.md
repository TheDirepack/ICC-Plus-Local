# play

Read this file before player simulation, continuation-state testing, or player-visible audits.

`play` exposes Rows, direct Choices, and Addons as separate player-safe entity lists with explicit parent/child links. Keep continuation state in a private state file.

For normalized projects, test **effective behavior**, not an obsolete physical JSON shape.

Examples:

- If a shared hide Requirement moved from every Choice to the Row, assert that the Row and its children are hidden before the provider and visible after it.
- If a Row now uses `allowedChoices = 1`, test selecting one option and then another at the target boundary instead of asserting sibling deactivation IDs exist.
- If Rows were merged, assert that the semantic choices remain reachable, ordered, and correctly limited instead of requiring the old Row ID.
- If runtime IDs were compacted, use the release mapping or an ID-aware test harness rather than hard-coding semantic IDs into the compact artifact.

## Visibility and cleanup are separate tests

A hidden Row can contain an internally selected Choice. Hiding a branch does not prove provider-loss cleanup occurred.

When provider loss matters, test both:

1. player visibility after the provider disappears;
2. whether the prior selection remains active, is rejected, or is cleaned up according to the intended mechanic.

Do not add duplicated Choice Requirements merely to make a test observe cleanup if the intended design is persistent hidden state.

## Large-suite practice

On very large projects, split simulator-heavy release checks into bounded suites when a monolithic run obscures failures behind a timeout. Keep complete coverage, but distinguish project failures from stale assertions, environment/import failures, and performance timeouts.

Reduce a long failing path to the shortest sequence that reproduces the behavior and keep that as the regression.

Read `../../../docs/PLAY_STRUCTURE.md`, `../../../docs/GAMEPLAY_RUNNER.md`, and `../../../docs/cyoa/guide/21-large-project-normalization.md` for the full model and normalization-specific testing rules.
