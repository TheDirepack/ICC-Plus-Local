# ICC Plus 2.10.6 parity audit

This audit records the source-parity work completed on the post-fix `iccplus-local` 0.8.0 line against official ICC Plus Svelte commit `a420836248d32043ae45d03f1b93cdcb9e354663` (ICC Plus 2.10.6). Current 0.9.x releases carry these gameplay semantics forward.

The 0.8.0 parity audit had a duplicate-version artifact problem, so its hashes remain historical provenance. Do not use those hashes to identify a current 0.9.x release.


## 0.9.2 re-audit

The 0.9.2 pass rechecked the pinned 2.10.6 source and focused on two gaps in the 0.9.1 release: the strength of the live differential suite and information leakage from the LM-facing player view.

- The field catalog was parsed against the pinned `ICCPlus/src/lib/store/types.ts`. All 18 entity catalogs and all 12 styling groups match with zero missing or extra fields.
- The live differential fixture set grew from 20 to 31 cases. New coverage includes ordinary score costs, below-zero rejection, one-based `multiplyByTimes`, selectable Addon parent activation and cleanup, forced non-clickable targets, `isAllowDeselect`, Requirement-loss cleanup, Variable/Word changes, and the main Requirement types.
- The player view now follows the Viewer display boundary more strictly. Selected entities hidden by selected-state filters do not appear in `selected_ids`. Row Requirements are never returned. Requirements with `showRequired: false` remain private. Verbose semantic blockers expose stable codes without raw traces, provider IDs, point previews, internal paths, or runtime hide-field names.
- The live browser differential remains the final executable source comparison. It requires a local Git checkout plus npm and Chromium, or network access for the harness to clone the pinned commit.

## What is required to match

For the project snapshot used in this audit, project JSON structure, creator defaults, save/export defaults, Requirement evaluation, point costs, repeat counters, selectable Addons, row limits, linked activation/deactivation, point modifiers, reset behavior, and player-facing mutation/error behavior were treated as compatibility-sensitive.

The brand-new project exported by `iccplus-local new` is required to match the ICC Plus Creator `Save to Disk` data byte-for-byte. ICC Plus first assigns `app.activated = getSelectedObjectId().split(',')`; an empty build therefore exports `"activated":[""]`. The local exporter preserves that source quirk, compact JSON separators, source field order, source spelling quirks, and the lack of a trailing newline.

The exact audited default export is 13,414 bytes with SHA-256 `35ba40a5e4a39b41c79d5e0f929404d9789d3173331059c9e635e72187c86faf`.

Browser presentation is not part of the headless runner. CSS/layout, image rendering/upload dialogs, audio, scrolling, fades, and other presentation-only behavior remain Viewer responsibilities. Advanced gameplay fields outside the audit snapshot are listed in `COVERAGE.md` rather than being silently treated as exact.

## Confirmed parity fixes from this pass

- Overlapping `selFromGroups` memberships count once per requested Group, not once per unique Choice ID.
- Point-comparison priority `0` is preserved instead of being coerced to priority `1`.
- Repeatables distinguish ICC Plus's variable-count mode, point-backed mode, and malformed no-mode behavior. Malformed counters are a Viewer no-op.
- Variable repeat counters support negative counts and the correct row-occupancy transition through zero.
- `addToAllowChoice` runs on each repeat increment/decrement. Point multiply/divide/set functions do not run on repeat-counter steps.
- Full-row replacement removes every positive repeat count from the displaced Choice. A negative repeat count cannot free row capacity through the Viewer loop.
- `/ON#` values use JavaScript-style numeric-prefix parsing. Comma-separated target IDs are parsed literally without trimming whitespace.
- Linked deactivation handles direct IDs, Groups, explicit repeat counts, forced-target protection, and deferred self-deactivation in Viewer order.
- Selectable Addons can activate their parent and can deselect the parent via `deselectParent` or `deselectWhenNoAddon`.
- Reset restores Point Types from `initValue`, clears runtime state, applies `isAutoActive`, and replays simple `notDeselectedByClean` selections.
- Ordinary point modifiers run after linked activation/deactivation and Requirement cleanup, matching `selectObject`. This fixes mutually exclusive point-setting presets.
- Ordinary Requirements and non-selectable Addons retain the empty structural `id` used by the Creator; they are not assigned invented project identities.
- Creator defaults for Rows, Backpack Rows, Choices, Addons, selectable-Addon conversion, Scores, Requirements, Point Types, Groups, Variables, Words, and global Requirements are source-derived.
- The field catalog matches the pinned `types.ts`, including `isSelectable` on ordinary Addons and inherited `defaultWidth` on selectable Addons.

## Revision 5 integration result at audit time

The September 18 parity-audit snapshot exposed eight malformed repeatables. Each set `isSelectableMultiple` without either `isMultipleUseVariable` or `multipleScoreId`, so the ICC Plus 2.10.6 counter was a Viewer no-op. That finding drove the stricter validation rule and regression tests.

The affected IDs in that historical snapshot were:

- `choice_race_multiple_breast_pairs`
- `choice_race_multi_segment_taur`
- `choice_race_engineered_aptitude`
- `choice_race_high_acuity_vision`
- `choice_race_innate_skill_package`
- `choice_race_power_immunity`
- `choice_race_selected_domain_resistance`
- `choice_race_selected_source_resistance`

Do not use this section as live project status. Re-run `iccplus-local validate` on the current export. The current Revision 5 export checked during the 0.9.1 re-audit validates with 0 errors and 0 warnings.

The audit also exercised the five economy presets as an integration sequence. Their Creation Point results were Standard 290, Generous 370, Tight 220, Mythic 500, and Cheat 1,000,000, with only the latest preset active. A normal 1-point selectable Addon changed 290 to 289 and restored 290 on deselection.

## 0.9.3 player-output hardening

Version 0.9.3 does not change the pinned gameplay semantics described above. It tightens what the local runner exposes to an LM acting as a player. Semantic errors now use allowlisted messages, failed `view --after` actions are sanitized, hidden and nonexistent guessed IDs are indistinguishable in player-safe output, and `session --player-safe` can keep continuation state in a file instead of stdout. These changes are covered by the normal regression suite.

## Tests

Normal local tests:

```bash
./run-tests
```

Compression tests are deliberately separate:

```bash
./run-compression-tests
```

Live source differential, on a machine with Git/npm/Chromium and network access:

```bash
./run-upstream-parity-tests
```

The live harness clones the official repository, checks out the exact commit above, verifies the local field catalog against the real `types.ts`, replaces the Viewer root with a test harness, builds the actual Svelte source, runs it in headless Chromium, and compares its state snapshots and default export with the Python implementation. This environment blocks direct GitHub cloning, so the online harness itself was prepared and syntax-checked here but cannot be executed here without an existing upstream checkout.

## 0.10.0rc2 verification boundary

Version 0.10.0rc2 broadens scripting and test coverage but does not claim that the official web GUI differential has already passed. It is the candidate to be tested against ICC Plus 2.10.6.

The candidate ships a full native-field retention fixture, a compact combined runtime reference, 32 isolated runtime execution fixtures, and one combined project for browser-heavy interactions and export behavior. Creator workflow tests cover the audited Creator components and their project-changing actions. Browser-only controls are listed separately rather than counted as JSON authoring parity.

The first returned browser package produced one strong Creator serialization artifact and several unreliable runtime observations. The C01 Save to Disk export is now a permanent regression. It confirmed empty-object pruning, `activated:[""]`, default `addonJustify`, and the absence of tool-only authoring-template metadata. Runtime results from that pass are not accepted as complete differential evidence because entity lookup skipped native kinds, state leaked between cases, and some Build Form values came from local state instead of the official UI.

rc2 therefore uses an isolated file and SHA-256 for every R case. The result validator accepts pass/fail only with 2.10.6, the expected fixture hash, `official_gui` provenance, and actual evidence. The current local checks prove source-derived field coverage, CLI behavior, deterministic headless behavior, runtime Row duplication, frozen default export bytes, exact reproduction of the accepted C01 Creator round-trip object, and the absence of known tool-only template metadata in every generated execution fixture. They do not replace the second official Creator/Viewer pass.


## 0.10.0rc3 automation boundary

0.10.0rc3 changes the agent-facing scripting interface and write reliability. It does not intentionally change the pinned ICC Plus gameplay semantics or Creator JSON target. The official 2.10.6 web-GUI differential is still required before a final parity claim.
