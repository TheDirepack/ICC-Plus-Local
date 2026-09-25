# Skill revision notes

## 2026-09-25 rc12 documentation and GitHub sync

- Re-audited the compressed skill set against ICC Plus Local 0.10.0rc12 and ICC Plus 2.10.7.
- Removed stale current references to the retired `cyoa-look` wrapper and routed native implementation, styling, validation, and playtesting through `iccplus-local`.
- Updated migration and release guidance around `project hydrate`, `project validate`, official-default completion, and the current 2.10.7 target.
- Kept historical rc11 and 2.10.6 release notes as provenance rather than relabeling old evidence.
- Synced the reduced CYOA skill set and routing documentation to the GitHub repository.

## 2026-09-25 ICC Plus Local skill consolidation

- Retired `cyoa-create`, `cyoa-edit`, `cyoa-look`, and `cyoa-test` as installed skills.
- Routed native ICC Plus 2 creation, editing, visual/media work, validation, and mechanical playtesting through the single `iccplus-local` skill and its function guides.
- Kept `cyoa-plan`, `cyoa-review`, `cyoa-migrate`, `cyoa-develop`, and `cyoa-ship` because they add design, audit, legacy-conversion, coordination, or delivery work outside the CLI itself.
- Kept `cyoa-compress` only for exceptional external or legacy asset trees outside the normal media path.
- Updated routing rules so the retired wrapper names are not reintroduced.

## 2026-09-25 skill deduplication

- Removed the older duplicate `/CYOA/skills/unslop` copy.
- Kept `/skills/unslop` as the single canonical Unslop skill because it is shared across projects and is newer than the CYOA-local copy.
- Kept the CYOA lifecycle skills separate after checking the routing evals. Their plan, create, edit, look, review, test, migrate, ship, and multi-session coordination boundaries are intentional rather than duplicate skills.
- Updated the skill index and authoring standard so shared cross-project skills are referenced from `/skills/` instead of copied into `/CYOA/skills/`.

## 2026-09-20 lifecycle reorganization

- Reordered the active guide around the project lifecycle instead of historical addition order.
- Replaced fragile chapter-number shorthand with explicit filenames.
- Grouped the guide into foundation/workflow, design/content, ICC Plus implementation, and testing/release.
- Kept installable skills flat for discovery while ordering the skills README by lifecycle.
- Replaced the stale local-session checklist with `local-workflow-checklist.md` using the current `inspect`/phase/`play` workflow.


## 2026-09-20 documentation-memory pass

- Shortened every active skill description to a compact trigger phrase. Descriptions no longer carry neighboring-skill exclusions or mini-workflows.
- Tightened the local skill standard to prefer 4 to 10 words and under about 80 characters.
- Added selector safety, source-authority, generated-output, `/CYOA/tools/`, independent accounting, and local-versus-Viewer mismatch rules where repeated project work had needed extra lookup or correction.
- Added checklist items so those rules are verified during normal passes instead of living only in prose.
- Kept source-side inheritance and baseline/delta templates separate from player-visible ICC Plus mechanics.

## 2026-09-20 rc10 command-surface alignment

- Re-audited the active skills against the current `iccplus-local` 0.10.0rc10 package and its 11-command canonical workflow.
- Replaced old normal-workflow references to `check`, `validate`, `view`, `session`, `state-check`, `apply`, `visual-audit`, and `apply-visuals` with current `reference`, `inspect`, phase commands, `media`, and `play`.
- Made `cyoa-test` use player-safe `play` audits and runtime discovery for any deeper analysis instead of naming retired compatibility aliases.
- Made `cyoa-look` use `inspect`, `style`, and `media`, and documented automatic compression for normal local or embedded image assignment.
- Narrowed `cyoa-compress` to exceptional external or legacy asset trees so it no longer competes with the normal media workflow.
- Added the authoritative-source rule to create, edit, develop, and local-tool workflows. Generated `project.json` must not become a second authoring source when a compiler exists.
- Updated routing evals for the current boundaries.
- Historical sections below retain older command names as release provenance only. They are not current workflow instructions.

## 2026-09-20 skill-format and routing pass

- Audited the skill set against current OpenAI skill documentation and the open Agent Skills specification.
- Rewrote descriptions around trigger conditions and adjacent-skill boundaries.
- Standardized task skills around inputs, workflow, rules, outputs, final checks, and references where that shape fits.
- Removed fast-changing `iccplus-local` version, commit, artifact-hash, smoke-hash, and test-count pins from task skills.
- Reduced `iccplus-local` to command routing, write safety, identity rules, player-safe testing, and on-demand documentation links.
- Moved the long Viewer-parity regression list out of `cyoa-test` into `references/viewer-parity-regressions.md`.
- Replaced the non-standard `disable-model-invocation` field in `unslop` with OpenAI's `agents/openai.yaml` invocation policy.
- Added `SKILL-STANDARD.md` and `ROUTING-EVALS.md` so future edits have a stable format guide and routing test set.

## 2026-09-18 continuation recovery hardening

- Updated the active tool authority to `iccplus-local` 0.9.5. Wheel SHA-256 `ad66f70237e8fe48868747de21a66eeeaa9b8ae9dd4fbe6b21ae24e7d0dcfd89`; source ZIP SHA-256 `3da40e482ffd0555d7c1c341fea39b50f877e242c62c94032bfd3763776c15cf`.
- `state-check` now handles malformed and truncated JSON as a normal invalid-state result.
- `play` reports damaged saved state through a sanitized `state.invalid` result, and `play --reset` can replace the bad file without loading it first.
- Runtime-state import now validates seed and RNG data before committing any new simulator state. Failed imports leave the old session unchanged.
- Updated the normal local verification count to 185 tests. Compression remains separate.

## 2026-09-18 continuation-state hardening

- Updated the active tool authority to `iccplus-local` 0.9.4. Wheel SHA-256 `b58e4c2e33da7755f8df14e5ed116bdabbf5d93fa909eb83cc311837c7bbe5e5`; source ZIP SHA-256 `9afafbfdc453261eb30df59235c75a8831c292671e7e898fff9e4a98a66620f2`.
- Made `play PROJECT --state FILE` the default continuing LM player loop. It resumes state automatically, writes it back atomically, and never returns raw continuation state to the player.
- Added `state-check` plus strict runtime-state import/export checks for project maps, selected order, row counts, ledger references, finite numeric values, variable and word types, and project fingerprints.
- Made state-file writes atomic and owner-only where the platform supports POSIX permissions.
- Added deterministic multi-step serialize/restore regression coverage across all 31 parity fixtures.
- Fixed static validation so linked target tokens preserve ICC Plus 2.10.6 comma whitespace literally, and aligned browser-only effect reporting between static validation and runtime analysis.
- Updated the normal local verification count to 183 tests. Compression remains separate.

## 2026-09-18 player-session hardening

- Updated the active tool authority to `iccplus-local` 0.9.3. Wheel SHA-256 `3de3abefaf0328b72cb685ec046b54b99dfe3f345f4de83d8b7cd3c6f670dc2c`; source ZIP SHA-256 `b871aaa80b97158e9350c7ec84efb5b3256a75f34196a33f0445e1ea7deebba8`.
- Added `session --player-safe` guidance for LM playtesting. Continuation state stays in `--state-out` files rather than entering the player context.
- Documented that player-safe messages use an allowlist and that failed `view --after` actions are sanitized. Hidden and nonexistent guessed IDs are indistinguishable in player-safe output.
- Updated the normal local verification count to 172 tests. Compression remains separate at 6 passed with 3 optional encoder-dependent skips.

## 2026-09-18 player-view parity refresh

- Version 0.9.2 closed player-view information leaks while preserving the pinned ICC Plus 2.10.6 gameplay semantics.
- Clarified that `view` is the LM/player observation channel. `snapshot` and `runtime_state` contain internal state and must not drive player decisions.
- Documented the no-leak boundary for hidden selected IDs, Row Requirements, hidden Requirement definitions, raw traces, provider IDs, point previews, internal paths, runtime hide fields, and images.
- Replaced the retired `iccplus_evaluate_requirements` troubleshooting instruction with `status`, `view`, `session`, and `show`.
- Expanded the source differential fixture set to 31 cases and the normal local suite to 166 tests.

## 2026-09-18 visual workflow hardening

- Version 0.9.1 hardened the 0.9 visual workflow.
- Visual manifests reject unknown keys, unknown styling fields, duplicate targets, and conflicting image/clear-image instructions instead of silently ignoring them.
- Added explicit `refs` batches, `replace_styling`, `unset_styling`, idempotent `customCSSAppend`, `--manifest-stub`, `--style-values`, and `--missing-assets`.
- Updated `cyoa-look` to use compact visual queues, reusable presets, explicit family batches, source records, broken-asset checks, and real-Viewer verification.
- The current Revision 5 export was rechecked during that pass with 0 static validation errors and 0 warnings. The older eight-repeatable result remains historical parity-audit evidence.
- Local verification for that release was 161 normal tests plus 6 compression tests, with 3 optional encoder-dependent skips.
- Compression and live upstream differential tests remained separate from normal discovery.

## 2026-09-17

- Added `cyoa-develop` to coordinate long, multi-pass CYOA projects without replacing the narrower task skills.
- Added working-state, bounded-pass, calibration, source-status, local-check, and global-check rules for LLM-assisted work.
- Expanded `cyoa-plan` with premise focus, non-goals, a full section skeleton, coverage inventory, hidden-content discoverability, decision basis, consequence planning, and broader build sweeps.
- Expanded `cyoa-create` and `cyoa-edit` with drift checks, requirement-path audits, impact mapping, source-status preservation, and explicit working-state updates.
- Expanded `cyoa-look` with consistent card geometry, focal cropping, asset-source tracking, WCAG contrast, non-color cues, target-size checks, and text alternatives.
- Expanded `cyoa-review` with choice-basis, consequence, discoverability, reachability, source-discipline, terminology, accessibility, and static-edition checks.
- Expanded `cyoa-ship` with static-edition and final asset checks.
- Reviewed `cyoa-compress` and added guide routing, visual verification, reference checks, package testing, and before/after size recording.
- Folded reusable design lessons from the supplied CYOA 101 guide into the skills while leaving its old ICC-specific implementation advice out of current ICC Plus 2 rules.

## 2026-09-15

- Kept the existing plan, create, edit, look, ship, ICC Plus, and unslop separation.
- Added `cyoa-review` for structured design and implementation audits.
- Added `cyoa-migrate` for old ICC and ICC Plus 1.x ports.
- Made every task skill aware of the relevant `cyoa-guide/` files.
- Limited legacy guidance to the migration skill and separate legacy reference.
- Expanded `cyoa-plan` around format choice, section order, completion rules, sample builds, and test design.
- Updated creation and editing skills to distinguish design changes from implementation work.
- Kept ICC Plus 2 schema and target Viewer behavior as the engine authority.
- Applied the bundled `unslop` rules to new skill prose.