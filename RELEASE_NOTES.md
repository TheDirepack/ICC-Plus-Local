## Unreleased

- Added `Simulator.row_visible()` and `Simulator.visible_row_ids()` for lightweight Row-gating checks. They evaluate Row Requirements directly without constructing `player_view()`, calculating Choice statuses, cloning hypothetical selection states, or generating point previews.
- Added focused regression coverage and documented when large test suites should use direct Row visibility queries instead of the full player-view path.

## 0.10.0rc15

- Made the sparse `project.json` representation the normal authoring format across generation, phased edits, low-level apply, hydration, formatting, exports, and Viewer packaging. `--not-sparse` / `--not_sparse` remains the explicit opt-out for materialized full-project JSON.
- Fixed the authoring round-trip exposed by the sparse-default rollout. Canonical sparse saves now retain Score `idx` because ICC Plus Local uses it as stable Score identity and hydration deliberately does not invent missing identities.
- Retained Sound Effect `name` in canonical sparse saves because it is a non-derivable authoring label even though pinned Viewer playback does not consume it.
- Updated sparse-serialization regressions so Viewer-only omissions cannot silently destroy state needed by later ICC Plus Local commands.
- Carried forward the expanded 2.10.7 Viewer omission audit and one-omission-at-a-time verification kit from the preceding sparse-runtime work. New omissions still require pinned-Viewer equivalence evidence and must also preserve the editable authoring round trip.
- Refreshed the README, sparse-serialization documentation, CYOA guide, ICC Plus Local skill, project function guide, package manifest, and release metadata for rc15.
- Kept the ICC Plus engine target at 2.10.7 and the pinned upstream source commit `1ea9db888cde2286d18d0d5de50933cb8773b739`.
- GitHub Actions remains the authoritative release gate. The candidate is not considered releasable until core runtime/validation tests, CLI contract tests, and checked-in examples all pass on the final release commit.

## 0.10.0rc14

- Introduced the sparse normal-project-save candidate: normal ICC Plus Local writes hydrate and complete-validate in memory, then save the pinned behavior-preserving sparse representation by default.
- Made `generate`, `build`, `structure`, `rules`, `style`, `apply`, and ordinary direct edits share the same sparse save path.
- Split normal sparse compatibility validation (`project validate`) from explicit Creator-complete validation (`project validate --complete`).
- Made sparse serialization the invariant for full-project JSON outputs unless `--not-sparse` / `--not_sparse` is supplied.
- Kept invalid sparse writes blocked because omission safety requires a complete source project.
- Made the compiler/native ownership boundary explicit. ICC Plus Local owns native compatibility, validation, serialization, local simulation, explicit native edits, and reference integrity; source-level semantic normalization remains a compiler responsibility.
- Locked native Row semantics with regression coverage: `allowedChoices: 0` means unlimited, and hiding a Row does not implicitly deselect already selected children.
- Corrected the ICC Plus 2.10.8 Addon caveat: the upstream change concerns selectable-Addon width handling through `addonWidth`, not Row selection-limit semantics.
- Split CI into core runtime/validation, CLI contract, and checked-in-example jobs.
- Added `iccplus-sparse` and `iccplus-omission-probe`, plus the generated omission-verification matrix for unresolved Viewer cases.
- Added a version-consistency regression covering package metadata and live documentation.

## 0.10.0rc13

- Added the compressed high-level CYOA skill set: `cyoa-plan`, `cyoa-review`, `cyoa-migrate`, `cyoa-develop`, `cyoa-ship`, and exceptional `cyoa-compress`.
- Kept `iccplus-local` as the single native ICC Plus 2 implementation skill and retired redundant wrapper skills.
- Added the complete current CYOA guide and legacy ICC migration reference under `docs/cyoa/`.
- Refreshed current documentation for the ICC Plus 2.10.7 command model while preserving historical verification evidence in its dedicated audit files.

## Earlier releases

Detailed historical implementation and audit evidence for rc12 and earlier remains available in the repository history and the versioned/historical audit documents under `docs/`. Current operating instructions are maintained in the unversioned documentation and skills rather than copied forward unchanged from older candidates.
