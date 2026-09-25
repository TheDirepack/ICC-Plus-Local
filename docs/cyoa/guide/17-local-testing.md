# Local headless testing

The local `iccplus-local` tool makes ICC Plus authoring and mechanical testing cheap to repeat. It does not replace the official Creator or Viewer. Browser presentation and any behavior outside verified local coverage still require official-tool testing.

## Discover the installed interface first

Do not copy command names from an old guide.

Use:

```bash
iccplus-local reference capabilities --brief
iccplus-local reference commands
```

Use `reference fields`, `reference schema`, `reference guide`, and `reference parity` when the exact shape or coverage is uncertain.

Older specialist command names may remain as compatibility aliases. They are not the normal LLM-facing interface.

## Inspect before changing

Use `inspect` for read-only project work. It can cover project shape, summaries, identities, search, exact targets, validation-oriented diagnostics, selectors, visual queues, and statistics through the current request format.

Inspect an unfamiliar project before mutation. If it is not Viewer-format ICC Plus project JSON, stop and locate the actual generated project or authoritative source.

For a project with a compiler, structured source, or phased build manifest, make changes there. Do not repair the generated `project.json` as a second authoring source.

## Normal writes complete the project automatically

`structure`, `rules`, and `style` fill missing official Creator defaults and run complete-project validation before replacing the project. A failed validation must leave the target unchanged. Generated and build outputs use the same complete-project boundary.

Use:

- `structure` for Rows, Choices, Addons, IDs, text, ordering, moves, and clones;
- `rules` for Points, Requirements, Scores, Groups, Variables, Words, and effects;
- `style` for images and presentation fields;
- `build` for a reproducible multi-phase build.

Use explicit refs or selectors with an expected match count for broad work. Use `--dry-run` where the current command supports it.

Do not add a separate routine validation command after every normal phase write. Use `project validate` for the final completeness check on an imported or externally supplied project. Use `project hydrate` when a legacy project is missing official baseline sections or safe Creator-eager defaults. Hydration must not invent missing IDs or downgrade a project from a newer ICC Plus version.

For read-only work on intentionally sparse legacy input, compatibility validation remains available. Do not treat compatibility mode as proof that a final generated project is Creator-complete.

## Player-safe testing

`play` is the normal local gameplay surface.

A clean view:

```bash
iccplus-local play project.json
```

A continuing action:

```bash
iccplus-local play project.json --state run.json --select choice_a
```

A multi-step audit:

```bash
iccplus-local play project.json @audit.json --state run.json
```

A multi-step request should state the actions and visible expectations after each step. Useful expectations include visible Point balances, selected IDs, available and deselectable Choices, visibility, and absence from the visible surface.

The player-facing loop must not receive hidden requirement definitions, internal provider IDs, raw runtime ledgers, or hidden selected IDs. Hidden and nonexistent guessed IDs should be indistinguishable.

## Persistent state

Keep a continuing run in the private `--state` file. Do not reconstruct later state from selected IDs or point totals. ICC Plus mechanics can depend on effect history, repeat counters, forced activation, row-limit changes, reversible point transforms, and random state.

After the project changes, start a new run unless cross-revision compatibility is the test.

If a continuation file is damaged or incompatible, use the current `play` and reference documentation to recover or reset it. Do not reach for a retired `state-check` workflow from memory.

## Regression design

For changed mechanics, test both successful and rejected paths. Include relevant boundaries such as exact cost, one short, requirement gain and loss, deselection, repeat-count changes, row capacity, forced activation cleanup, variable transitions, and restore-then-continue behavior.

A rejected action should be transactional. Record its semantic result and confirm no partial state remains.

When a long run finds a bug, reduce it to the shortest action sequence that still fails and keep that sequence as a regression.

## Advanced analysis

The public command surface can change. When pairwise, graph, exploration, or other deeper analysis is useful, discover the current supported path with `reference commands` or the packaged guides. Do not teach hidden compatibility aliases as permanent commands.

For any bounded analysis, record the bounds. Failure to reach a state inside a bound is not proof that the state is impossible.

## When local and official behavior disagree

Do not patch native project data merely to make the local runner agree with itself.

Reduce the mismatch to the smallest project and action sequence, verify the target Viewer behavior, inspect the relevant target source when needed, then fix the local runner or mark that behavior outside local coverage. Keep a regression for the reduced case.

For important point accounting, pair runtime tests with an independent expected-balance ledger. The second check should not call the same effect evaluator that produced the runtime result.

## What local testing does not prove

Local mechanical testing does not emulate DOM layout, responsive CSS, image rendering, animation, browser dialogs, network loading, or every official Viewer effect.

Use the official Viewer for those.

For source-parity claims, read the current package `COVERAGE.md`, package manifest, and `reference parity`. Keep tool version, source commit, hashes, and regression counts in release records rather than in general workflow instructions.

## Release use

Before release, keep reproducible tests for ordinary complete builds, budget boundaries, requirement-loss paths, important exclusions, saved-state continuation, and past mechanical bugs.

Official Creator and Viewer verification remains a separate release gate. Do not make local simulator success the only evidence for release parity.