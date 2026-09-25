# Simulation coverage

The simulator is meant for logic testing, not pixel-perfect browser emulation.

## Modeled directly

The following behaviors are implemented from the ICC Plus 2.10.7 source model and viewer logic:

- Clean initial point, variable, and word state.
- Choice and selectable-addon activations.
- ICC Plus multiple counters in all three 2.10.7 modes: signed variable counts, point-backed counters, and the source no-op behavior when `isSelectableMultiple` has no repeat mode.
- `id` requirements, including `/ON#N` counts.
- `points` requirements.
- `pointCompare` arithmetic.
- `or` requirements.
- `selFromGroups`, `selFromRows`, and `selFromWhole`.
- Global requirements through `gid`, with cycle protection.
- `word` requirements.
- Nested `requireds` as prerequisites for a requirement.
- Score costs, including score-level requirements.
- Expression scores using point placeholders.
- Seeded random score values.
- Random forced activation pools, including per-repeat chosen-target bookkeeping and native Build Form serialization.
- Existing applied discount values stored on a score.
- `belowZeroNotAllowed` selection blocking.
- Row `allowedChoices` and replacement of a deselectable active choice.
- `isCountDisabled` and selectable-addon `countAsChoice`.
- Selectable Addons causing their parent Choice to be internally selected, including `isNotSelectable` container parents, plus `deselectParent` and parent `deselectWhenNoAddon` cleanup.
- `selectOnce` ordinary deselection blocking.
- Variable changes through `isChangeVariables`, `changedVariables`, and `changeType`.
- Direct `activateOtherChoice` and `deactivateOtherChoice` targets, including literal comma parsing, group targets, `/ON#N` counts, self-deactivation ordering, and forced-target protection. Forced `isNotSelectable` targets follow `isNotActiveUnselectable`, and `isAllowDeselect` keeps the target unlocked.
- Cleanup of active choices whose requirements become false after another selection.
- Dynamic row limits through `addToAllowChoice`.
- Point multiply, divide, and set effects for ordinary LIFO usage, in Viewer selection order after linked activation/deactivation and requirement cleanup.
- Word changes using `textfieldIsOn`, `wordChangeSelect`, and `wordChangeDeselect` when no interactive prompt is needed.
- `isAutoActive` clean-session defaults plus reset replay of simple `notDeselectedByClean` selections and Point Type `initValue`.
- One-based `multiplyByTimes` costs (1x, 2x, 3x, ...).
- Row-Requirement visibility gating, Choice visibility filters, Addon reveal/removal rules, point-bar activation gates, `showAllAddons`, and non-image `isContentHidden` effects.
- Viewer-style text replacement for Word placeholder IDs, including Point Type and multi-select Choice aliases.
- Native Row-button execution for variable toggles, weighted/unweighted random Choice activation, and random Point changes, including Build Form row-button records.
- Runtime Row duplication with ICC Plus `/D#N` IDs, insertion order, score-runtime cleanup, group/design membership, and the pinned 2.10.7 Requirement/function suffix rules. Duplicated Rows persist through serialized continuation state.
- Transactional player actions with semantic failure codes.

## Player-view boundary

`view` is a gameplay representation, not DOM emulation. It intentionally omits all image fields and never loads image assets. It applies a no-leak player boundary. Selected entities hidden by Viewer filters are absent from `selected_ids`. Row Requirements and hidden Requirement definitions are not returned. Semantic errors use allowlisted player messages and never fall back to raw runtime messages. Failed `view --after` actions use the same sanitizer. Point-bar output does not expose `belowZeroNotAllowed`. Runtime hide-content codes that only affect Choice or Addon images are ignored as image state, while the Viewer's associated non-image `textIsRemoved` behavior is still modeled. Layout, CSS, responsive geometry, and visual styling beyond visibility filters are outside the runner.

`play` is the preferred continuing player loop. It performs one safe action, automatically resumes and atomically rewrites a machine-owned state file, and returns the current player view. `session --player-safe` provides the same output boundary for ordered multi-action batches. Both keep snapshots, runtime state, project fingerprints, raw event details, and internal status data out of player output.

## Reported but not fully emulated

These fields are detected and surfaced because browser rendering, media, interactive dialogs, or mutable discount stacks make exact emulation more involved:

- Full dynamic discount stacking and discount-count rules. The Revision 5 snapshot used for the original parity audit did not use these fields.
- Template and width changes.
- Point-bar and background changes.
- Scrolling.
- BGM and sound playback.
- Fade transitions and delays.
- Image upload dialogs.
- Confirmation dialogs.
- Custom text input dialogs.

They do not disappear from the project. The simulator lists them in `unsupported_effects` or validation diagnostics so tests can decide whether they matter.

## 2.10.7 source-parity boundary

The parity suite is pinned to ICC Plus 2.10.7 commit `1ea9db888cde2286d18d0d5de50933cb8773b739`. The 2.10.7 runtime diff is narrow: Score display adds optional `removeSpace`, autocomplete selection cleanup changes, and modern projects no longer receive the legacy Point Type hidden-flag migration on load. Existing source-parity cases preserve the unchanged behavioral quirks that still apply, including overlapping Group counts, JavaScript `parseInt` prefixes, literal comma target parsing, malformed repeat counters doing nothing, and the saved-empty-project `activated:[""]` value.

The Revision 5 snapshot used for the original parity audit used none of the advanced mechanics listed above. That observation is historical project evidence, not a claim about every later project revision. These mechanics remain outside the exact gameplay-parity claim unless separately verified.

## Determinism

Random score behavior uses a seeded Python random generator. The default seed is `0`. Pass another seed to the CLI or `Simulator` when testing random branches.

The `explore` command is bounded by state count and depth. A choice in `unreached_choice_ids` means it was not reached within those bounds. It is not a mathematical proof that the choice can never be reached.

## Compatibility meaning

A pair can produce several different outcomes:

- `coexist`: both choices remain active.
- Displacement: the second choice can be selected, but the first is removed because of a row cap, a changed requirement, or a deactivate effect.
- Blocked: the second choice cannot be selected in that state.
- Order-dependent: changing selection order changes which choice survives.

This distinction matches ICC Plus better than treating every conflict as a simple boolean exclusion.

## Portable session state

The current runtime can serialize and restore the headless state. The state contains the hidden ledgers needed to continue correctly after a process boundary. Import rejects contradictory continuation bookkeeping such as selected-order mismatches, wrong Row counts, unknown activation IDs, malformed ledgers, invalid scalar types, and non-finite numbers. Export also checks the live state before writing it.

The normal regression suite runs deterministic action sequences across all 32 source-parity fixtures. After every step it checks runtime invariants, serializes the state, restores it, and compares the externally relevant snapshot. Separate tests cover score reversal and seeded random continuation.

The state is tied to a SHA-256 fingerprint of the base project JSON. Normal loading rejects a mismatch. Runtime-created duplicate Rows are stored separately as validated `dynamic_rows` and reconstructed before the remaining state is accepted. This is a safety check, not a migration system for live player saves between project revisions.

Event history is optional and excluded by default. It is not required to continue the simulation.
