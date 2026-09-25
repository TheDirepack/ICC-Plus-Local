# Continuous headless play

Use a continuing local run when a mechanical playthrough must survive across tool calls or conversation turns.

## One player-facing surface

Current local play uses `play` as the normal player observation and action interface. The returned view is filtered to what the player can observe. Hidden entities and internal runtime bookkeeping stay outside the player-facing loop.

Use:

```bash
iccplus-local play project.json --state run.json --select choice_a
```

For several ordered actions in one call, pass a multi-step audit request:

```bash
iccplus-local play project.json @audit.json --state run.json
```

The audit can attach player-visible expectations to each action.

## Keep continuation state private

The `--state` file exists for continuation, not for player reasoning.

Do not read it into the LLM player context. Do not resume from a summary, selected-ID list, point totals, or a hand-built approximation.

A continuing run may need hidden effect ledgers, repeat counts, row-limit history, random state, and other information that is not visible in the player view.

## Agent loop

1. Start `play` with a private `--state` file and a player action.
2. Read only the sanitized action result and returned player-visible state.
3. Reuse the same state path on the next step.
4. Use a multi-step audit request when several actions belong to one deterministic regression.
5. Keep a separate human-readable action transcript when needed.

## Project revisions

Continuation state is tied to the project it came from. After mechanics are edited, start a new run unless cross-revision behavior is the subject of the test.

Do not carry a green continuation result across project or tool revisions.

## Long runs

For a long run, preserve:

- the private state file,
- the action transcript or player notes,
- the project revision or fingerprint,
- the local-tool release identity used for the run.

Do not keep an ever-growing internal event history unless the test requires it.

## Reproducing bugs

When a continuing run exposes a bug, keep the failing state for investigation and reduce the failure to the shortest player action sequence that still reproduces it. Add the reduced sequence to the regression set.

## Current-interface rule

Do not teach retired `session`, `view`, or `state-check` commands as the normal workflow. If a diagnostic operation outside `play` is required, discover its current supported route with `reference commands` or the packaged guide for the installed release.