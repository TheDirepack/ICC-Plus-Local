# Simulation coverage

The simulator is meant for logic testing, not pixel-perfect browser emulation.

## Modeled directly

The following behaviors were implemented against the ICC Plus 2.10.7 source baseline and updated for known 2.10.14 source changes:

- Clean initial point, variable, and word state.
- Choice and selectable-addon activations.
- ICC Plus multiple counters in the three established modes: signed variable counts, point-backed counters, and the source no-op behavior when `isSelectableMultiple` has no repeat mode.
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
- Runtime Row duplication with ICC Plus `/D#N` IDs, insertion order, score-runtime cleanup, group/design membership, and the previously verified Requirement/function suffix rules. Duplicated Rows persist through serialized continuation state.
- Transactional player actions with semantic failure codes.

## Player-view boundary

`view` is a gameplay representation, not DOM emulation. It intentionally omits all image fields and never loads image assets. It applies a no-leak player boundary. Selected entities hidden by Viewer filters are absent from `selected_ids`. Row Requirements and hidden Requirement definitions are not returned. Semantic errors use allowlisted player messages and never fall back to raw runtime messages. Failed `view --after` actions use the same sanitizer. Point-bar output does not expose `belowZeroNotAllowed`. Runtime hide-content codes that only affect Choice or Addon images are ignored as image state, while the Viewer's associated non-image `textIsRemoved` behavior is still modeled. Layout, CSS, responsive geometry, and visual styling beyond visibility filters are outside the runner.

`play` is the preferred continuing player loop. It performs one safe action, automatically resumes and atomically rewrites a machine-owned state file, and returns the current player view. `session --player-safe` provides the same output boundary for ordered multi-action batches. Both keep snapshots, runtime state, project fingerprints, raw event details, and internal status data out of player output.

For Python regression tests that only need Row gating, use `Simulator.row_visible(id)` or `Simulator.visible_row_ids()`. These helpers evaluate Row Requirements directly and do not construct the full player view, calculate Choice selection status, clone hypothetical runtime states, or build point previews. Use `player_view()` when the test needs the complete player-visible structure or selection availability. Full views use indexed Row/Choice and Choice/Addon relationships and reuse selection-status calculations within that one view; these caches never cross a state change or a later view. `visible_row_ids(include_backpack=True)` includes Backpack Rows; the default returns ordinary Rows only.

## Reported but not fully emulated

These fields are detected and surfaced because browser rendering, media, interactive dialogs, or mutable discount stacks make exact emulation more involved:

- General dynamic discount stacking (more than two sources), per-selection/competing discount-count allocation and repeated discounted purchases. The Revision 5 snapshot used for the original parity audit did not use these fields.
- Template and width changes.
- Point-bar and background changes.
- Scrolling.
- BGM and sound playback.
- Fade transitions and delays.
- Image upload dialogs.
- Confirmation dialogs.
- Custom text input dialogs.

They do not disappear from the project. The simulator lists them in `unsupported_effects` or validation diagnostics so tests can decide whether they matter.

## 2.10.16 source-parity boundary

The current release target is ICC Plus 2.10.16, source commit `2bba0cf9ebc2e54241c2390794e95e1c5091b293`. The 2.10.16 Viewer fixes Build Form restoration of missing force-selected targets when their provider permits ordinary deselection; Local mirrors that source-verified change and runs four explicit restore-case action traces. The previous 2.10.15 release addressed deployment/Neocities compatibility without changing its gameplay store, whereas 2.10.16 changes the Build Form restoration logic. The pinned Chromium differential now tests 99 gameplay cases (including 58 source-referenced dynamic-discount scenarios and four native Build Form restoration cases) plus 13 full-project-versus-sparse-project cases directly in the official Viewer. All 58 dynamic-discount cases compare **every action checkpoint** against Chromium: single-provider Choice/Row/Group targeting, arithmetic/rounding/floor/filter cases, two or three competing providers with compatible stacks/nonstackable offers/mixed precedence, and twelve one-or-two-use allocation/refund scenarios across direct Choice, Row and Group targets. An incorrect intermediate charge/refund therefore cannot be hidden by an equivalent final result. Every sparse case checks the initial state and **each action checkpoint**, not merely the final state. The expanded cases cover baseline/default projects, protected selections, Point costs and refunds, already-applied fixed discounts, row-cap replacement, multiple-selection counts, Requirement cleanup, and selectable Addons. They do not prove every omission, visual style, or dynamically recomputed discount is equivalent. Passing them does not validate the official Viewer distribution on every hosting environment, nor does the headless port replace upstream's newer site-deployment build.

## Historical 2.10.14 source-parity boundary

The 2.10.14 synchronization targeted ICC Plus 2.10.14 at upstream source commit `21d340238fa16f4e66a61727f797d334b0486fda`. The earlier 2.10.7 differential suite established the baseline. This update adds the `notDeselectedByReq` selection-protection flag, keeps newly live Score refund fields in sparse projects, and aligns active Addon visibility and result-row exclusions. The local simulation now models one non-repeatable discount provider targeting a deterministic fixed Score through direct Choice IDs, all Choices in a Row, or Choices in native Groups. It handles selection-time discounting, repricing an already-selected choice, and subsequent source/purchase removal. Up to three ordinary providers per deterministic Score are now supported for the source-verified fixed, non-negative **subtraction** stacking/competition case, with selection-order precedence and reprice/refund ledger updates. Mixed operators or per-source discount floors on a multi-provider target are deliberately excluded until their interactions have dedicated Viewer traces. It additionally supports one ordinary finite-use provider targeting Choices directly or via native Rows and Groups, for independent fixed-cost nonrepeatable purchases; purchase removal/reselection releases or reassigns the limited discount according to native allocation order. It still does **not** claim four-or-more-provider arbitration, multiple competing quota providers, per-selection quotas, repeatable discounted purchases, multi-Score quota targets, or browser-layout emulation. For a single deterministic Score imported with an already-applied discount but an empty `discounts` list, the Viewer clears the discount metadata after selection and refunds the *original* cost at deselection; the native simulator preserves this narrow source-verified quirk.

The pinned upstream Viewer differential harness checks default export and actual runtime state in Chromium, including targeted 2.10.14 cases. The 35-case 2.10.14 Chromium differential, default export, and TypeScript field/required-field checks passed in [GitHub Actions](https://github.com/TheDirepack/ICC-Plus-Local/actions/runs/40810229658). This verifies the enumerated cases only; browser layout, visual effects, dynamic discount stacks, and independent omission-probe cases remain outside this proof. The offline Python and CLI tests alone do not establish Viewer parity.

The historical Revision 5 project snapshot used none of the advanced mechanics marked unsupported above. That observation does not imply subsequent project versions avoid them.

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

The official 2.10.16 Viewer has a source-confirmed edge case where deselecting the strongest of three nonstackable subtraction providers leaves the purchase at its **original** price, even though two weaker providers remain active. Local mirrors this narrow active-discount/refund-state outcome, including removal of a weaker inactive provider and portable runtime-state export/import, rather than substituting a nominal next-best discount. Five additional official action traces test the state through unrelated selection, provider removals, reactivation and purchase refunds.

Review follow-up boundary (October 30, 2026): The `review_fractional_float_point_21016` case uses `allowFloat=True` and **is included** in official Chromium Viewer 2.10.16 action-trace coverage. Separately, Chromium demonstrated a fractional-Score quirk when the Point instead has `allowFloat=False`: for a raw Score of 8.9 and a +0.5 dynamic discount, Viewer initially charges 8 but later reprices to Point totals 41.9 and 42.9 (from 50), using the *unrounded* raw Score as a delta baseline. Local floors the base before fixed-cost repricing for internal consistency. That **integer-only Point variant** is tested in the local regression suite only, is excluded from official gameplay differential coverage, and is not claimed source-equivalent until an explicit per-Score upstream discount-state model exists. Fixed multi-Score Point-ID aggregation and float-enabled traces remain covered by the official Viewer.

The expanded sparse-equivalence suite also verifies a discount provider selected as a *different Choice* from an already-active target, then removed before a purchase refund. This explicitly exercises the native `selectUpdateScore` cross-Choice `isChangeDiscount`/`tmpDisScore` path as well as retaining the scratch fields in sparse authoring JSON. The separate pre-applied empty-list refund case is unchanged because it tests a distinct upstream refund quirk.
