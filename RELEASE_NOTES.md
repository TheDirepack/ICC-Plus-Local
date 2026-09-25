## 0.10.0rc11

- Normalized the player-safe `play` view so visible Rows, direct Choices, and Addons are exposed as separate top-level entity lists instead of requiring agents to recover structure from nested data.
- Rows now expose ordered `choice_ids` plus per-Row selected/available/deselectable direct Choice IDs.
- Choices now expose `row_id`, visible-order `index`, and Addon membership; Addons expose `row_id`, `choice_id`, and visible-order `index`.
- Added ordered `row_ids`, `choice_ids`, `addon_ids`, `selectable_addon_ids`, and `informational_addon_ids` indexes.
- Split selection availability into explicit all-selection, direct-Choice, and selectable-Addon fields while retaining the historical `available_choice_ids` / `deselectable_choice_ids` compatibility aliases.
- Added `row_choices` and `choice_rows` player-safe audit expectations so tests can assert visible hierarchy without reading raw project JSON.
- Fixed ordinary non-selectable Addon parent resolution in the player view; visible informational Addons now appear alongside selectable Addons when Viewer rules expose them.
- The rc11 release gate ran the normal regression suite only. The compression suite was intentionally not rerun for this candidate.
- Added an ICC Plus Local agent skill and a dedicated `PLAY_STRUCTURE.md` reference so rc11's Row, Choice, and Addon hierarchy is documented in one place.

## 0.10.0rc10

- Hardened official-GUI result validation after auditing an external rc2 result bundle.
- Removed the standalone `cyoa-compress` package entry point; image compression remains automatic inside image assignment.
- Result validation now accepts JSON, directories, or ZIP bundles and verifies claimed artifact paths.
- Runtime pass/fail evidence now requires an official snapshot after every action plus a final snapshot; changed fields are required and reported values are compared with the packaged expectation.
- Creator and advanced pass/fail evidence must cover every prescribed step with structured checks. Partial execution must be blocked instead of passed.
- Added minimum returned-artifact requirements for export/screenshot-heavy verification cases.
- Added a permanent 32-case runtime replay regression that checks every intermediate state and final state.
- Confirmed the returned rc2 C01 official Creator export exactly matches the pinned 2.10.6 round-trip fixture.

# Release notes

## 0.10.0rc9

This release reorganizes the public CLI around workflows instead of implementation helpers.

- Reduced the canonical top-level surface to 11 commands: `reference`, `template`, `media`, `project`, `inspect`, `generate`, `build`, `structure`, `rules`, `style`, and `play`.
- Removed `creator`, `test`, `check`, `build-viewer`, `session`, `state-check`, `apply`, and other wrapper/helper names from the advertised surface while retaining compatibility aliases where practical.
- Moved entity defaults, style presets, and Creator design import/export under `template`.
- Moved images, crops, fonts, sound, and asset probing under `media`; image compression remains automatic.
- Moved formatting, separate-image export, fragment import/export, ID helpers, build summaries, and Build Form strings under `project`.
- Moved command discovery, capabilities, schemas, field/type references, parity, guides, symbols, and environment checks under `reference`.
- Normal `structure`, `rules`, and `style` edits validate automatically before writing; manual `check` is no longer part of the normal workflow.
- `play` now accepts multi-step player-safe audit requests with visible-state expectations, replacing the need for a public `test` namespace. Hidden and nonexistent guessed IDs remain indistinguishable.

## 0.10.0rc8

This release performs a second command-surface consolidation.

- Reduced the advertised top-level CLI from 47 commands to 29 without removing project capability.
- Added `creator` for Creator-only helpers such as style templates, design import/export, Row copy/sort, fonts, symbols, sound import, and ID utilities.
- Added `media` for image assignment, cropping, compression, and asset probing.
- Added `test` for deep simulator analysis: pair, matrix, graph, exploration, project analysis, and scenario execution.
- Old specialist top-level names remain parseable compatibility aliases but are now genuinely absent from normal `--help` output.
- `play` remains the normal player-safe progressive audit command; `test` is for deeper analysis rather than ordinary playthrough auditing.

## 0.10.0rc7


This candidate makes style bulk editing first-class and reduces the advertised command surface.

- `style` remains one command for one or many visual edits. One manifest can assign many distinct images through `items`, reuse a treatment with `refs`, or target a selector with `where` and an `expect` count.
- Added selector-backed style tests and multi-image batch tests. There is no separate style-bulk command.
- `inspect` now includes `visual` and `stats` query operations. Visual work queues, selector previews, search/list/show/get, identities, validation, and project stats all use one read-only interface.
- `play` no longer requires a state path. Without `--state` it is an ephemeral player-safe view/action command; with `--state` it resumes and saves progressive play.
- The advertised top-level CLI shrank from 74 commands to 47. Redundant read, one-off mutation, old visual, blank-project, and simple runtime names are hidden compatibility aliases rather than part of the LLM contract.
- Added `docs/COMMAND_SURFACE_AUDIT.md` documenting what was consolidated and why the remaining specialist commands stay separate.
- Final local regression: 293 normal tests passed. Compression tests passed 6 with 3 optional encoder-dependent skips.

## 0.10.0rc6

This candidate makes bulk phase authoring use the same operations as single edits and strengthens the player-safe simulator as an LLM audit tool.

- `structure` and `rules` no longer require separate phase-level `update_many` or `delete_many` verbs. `add`/`upsert` accept `values` for one entity or `items` for many entities of the same kind and parent.
- Phase `update` and `delete` accept one ref, an explicit refs list, or a `where` selector. Selector forms support `expect` and `allow_empty`. The phase layer expands these forms into the existing atomic operation engine.
- Bulk selector normalization automatically narrows a phase selector to the declared entity kind when the selector does not provide its own kind.
- Player view now includes `available_choice_ids` and `deselectable_choice_ids`, derived only from currently visible player-accessible entities.
- Added progressive simulator tests that verify Point balances, visible availability, unlocks, changing affordability, private continuation, and hidden-versus-nonexistent ID normalization.
- No hidden-content viewer option was added. `play` and `session --player-safe` remain player-observation-only interfaces. Internal snapshots remain available to regression code.
- Final local regression: 289 normal tests passed. Compression tests passed 6 with 3 optional encoder-dependent skips.

## 0.10.0rc5

This candidate splits LLM authoring into explicit structure, rules, and style phases while keeping `apply` as a low-level escape hatch.

- Added `structure PROJECT SCRIPT` with the `iccplus-structure-ops` format. It accepts Rows, Choices, Addons, IDs, text, ordering, moving, and cloning, and rejects rule and style fields.
- Added `rules PROJECT SCRIPT` with the `iccplus-rules-ops` format. It accepts Points, Requirements, Scores, Groups, gating, costs, effects, Variables, Words, and common gameplay fields, and rejects section text and style fields.
- Added `style PROJECT MANIFEST` as the canonical presentation command over the existing visual-manifest implementation.
- Added phase-specific schemas for structure and rules. `style-manifest` is a schema alias for the visual manifest.
- Added `iccplus-build` version 2. Every step declares `structure`, `rules`, `style`, or explicit `raw`. The build calls the same phase implementations used by the direct commands.
- Version 1 build manifests remain readable and are treated as legacy raw `iccplus-agent-ops` builds.
- Cross-phase field checks run before mutation. A structure script cannot silently add Scores or styling, and a rules script cannot rewrite titles or descriptive text.
- Added `docs/PHASED_AUTHORING.md` and replaced the main LLM workflow with blank creation followed by structure, rules, style, validation, and export.

## 0.10.0rc4

This candidate simplifies the project-authoring model and adds a repeatable build pipeline.

- `generate` now creates only the exact blank ICC Plus 2.10.6 Creator export. It no longer accepts a compact project fragment.
- All project content changes go through `apply` or the existing direct mutation commands.
- Added `build BUILD.json -o project.json`. A build starts from the blank Creator project and applies ordered strict `iccplus-agent-ops` files in memory.
- Build step paths are relative to the manifest and cannot escape its directory. Duplicate script paths are rejected.
- Build output is written only after all steps succeed and the final project validates.
- Build receipts contain per-script SHA-256 values, a build fingerprint, a final project fingerprint, step counts, summary, and validation.
- Added `build-manifest` schema, a complete two-step example, and build-system documentation.
- The canonical LLM workflow now has one write representation instead of separate generation and repair representations.
- JSON-only commands no longer require Pillow at process startup. Image cropping imports Pillow only when an image crop is requested.
- Local verification: 278 normal tests passed; compression tests passed 6 with 3 optional encoder-dependent skips. A clean-venv wheel smoke test passed for `generate`, `schema build-manifest`, `build`, and `check`.

## 0.10.0rc3

LLM and automation interface audit. Gameplay and ICC Plus project-format targets remain pinned to 2.10.6.

- Added `capabilities --brief` and section-scoped capability discovery so an agent does not need the full inventory for routine work.
- Added `schema list` and packaged protocol schemas for canonical agent operations, batched inspection, sessions, runtime state, generation, and visual manifests.
- Added read-only `inspect` batches for check, summary, IDs, list, search, show, pointer get, and selector match queries.
- Added the strict `iccplus-agent-ops` batch format. It rejects unknown operation keys and unknown native fields under `values`, while the older compatibility operation format remains available for deliberate future-field work.
- Canonical agent batches default to compact receipts instead of echoing complete edited entities. `--result-mode full` restores the diagnostic response.
- `describe` now has a semantic summary for every top-level command and can describe nested subcommands such as `describe style-template apply`.
- Project JSON writes now use same-directory temporary files plus atomic replacement.
- Added an explicit LLM automation audit, examples, and regression tests for the agent contract.
- The canonical Python automation example now resolves either the installed entry point or a source checkout and emits one valid JSON document.
- Final rc3 normal-suite count before packaging: 276 passed. Compression remains separate at 6 passed with 3 optional encoder-dependent skips.

## 0.10.0rc2

This candidate incorporates the usable evidence from the first official ICC Plus 2.10.6 browser run and repairs the external verification regimen before the runtime pass is repeated.

- Adds a permanent regression fixture from the returned official C01 Creator export. Creator-style formatting now reproduces the observed import and Save to Disk normalization for empty objects, `activated: [""]`, and default `addonJustify`.
- Uses the same Creator save normalization for Creator-format JSON, separate-image export, and viewer packaging.
- Aligns source-derived Creator factory defaults for Design Group names and Sound Effect pitch.
- Replaces the shared runtime execution fixture with 32 isolated R-case fixtures. Each case has its own SHA-256 while the combined runtime matrix remains available as a compact reference.
- Fixes the advanced Row-button fixture so the random Point button uses the native `sumaddon` branch and the weighted-random button contains real weighted Choices.
- Adds result provenance. Official pass/fail records must identify `official_gui` as their observation source and must match the packaged fixture path and hash.
- Splits result validation into structural validity and completion. Pending, blocked, or not-applicable mandatory cases make the run incomplete and return exit code 3 unless explicitly allowed.
- Updates the external-agent instructions so selectable Addons, Point Types, native Row buttons, Build Form observations, and normal Creator event handlers are tested correctly.
- Keeps Creator components, style presets, compact authoring helpers, and verification metadata outside native project JSON. The template-boundary regression remains mandatory.
- The first returned runtime run is not treated as complete upstream verification because its automation missed existing entity kinds, leaked state between cases, and reconstructed some Build Form observations from local state.
- Adds pinned runtime Row duplication, including `/D#N` identities, source-compatible Requirement/function suffix behavior, group/design membership updates, and portable continuation of dynamically duplicated Rows.
- Aligns Word Requirement factory output with the Creator placeholder used by `addNewRequired('word', ...)`.
- Expands template-boundary scans to all 32 isolated runtime fixtures and makes the GUI feature-to-test map explicit and self-checking.
- Tightens returned-result validation so 2.10.6, fixture hashes, official-GUI provenance, and actual observations/artifacts are required for accepted pass/fail evidence.
- Final rc2 local regimen before packaging: 260 normal tests passed; compression remained separate at 6 passed with 3 optional encoder-dependent skips; frozen default export remained 13,414 bytes with SHA-256 `35ba40a5e4a39b41c79d5e0f929404d9789d3173331059c9e635e72187c86faf`.

## 0.10.0rc1

This is the external-verification candidate for ICC Plus 2.10.6. It is not the post-audit parity release.

- Adds typed field metadata and generated schema/interface output for script authors and LLMs.
- Adds first-class structural authoring for reordering, moving, cloning, fragment import/export, Row bulk operations, design import/export, Creator style presets, title-based IDs, CSV export, fonts, sound-effect files, and related Creator workflows.
- Adds native Build Form string import/export with repeat counts, random Score results, random activation results, Variables, custom words, uploaded-image payloads, and Row-button random Point results.
- Adds browser-oriented packaging helpers for separate-image projects and official viewer templates.
- Adds the external verification kit with three project fixtures, 32 deterministic runtime cases, 12 Creator workflow cases, and 12 browser-heavy combined cases.
- Makes the Creator-template boundary a regression invariant. Authoring presets, compact effects, components, and verification metadata compile to native ICC Plus fields and are not serialized as tool-specific objects.
- Normal regression suite: 244 tests before final packaging checks. Compression tests remain a separate suite.
- Full official web GUI differential verification is intentionally deferred until this candidate is handed to the external testing agent.

## 0.9.5

This patch makes damaged continuation files recoverable and keeps failed state imports transactional.

- `state-check` now treats truncated or malformed JSON as an ordinary invalid-state result with exit code 2 instead of falling through to the generic CLI error path.
- `play` now returns a sanitized `state.invalid` result for a damaged saved state instead of exposing parser or import details through the generic error channel.
- `play --reset` deliberately skips loading the old state, so it can replace a truncated, malformed, or project-incompatible continuation file with a clean Viewer-style state.
- `import_state()` validates the saved seed and RNG state before replacing the simulator state. A failed import leaves the existing simulator and RNG untouched.
- Runtime-state seeds now require an actual JSON integer rather than accepting booleans through Python integer coercion.
- Added regression coverage for truncated JSON recovery and transactional import failures.
- Final normal-suite count before packaging: 185 tests. Compression remains a separate suite.

## 0.9.4

This patch hardens continuous sessions and makes the safe LM play loop shorter.

- Added `play PROJECT --state FILE`, a one-action player command that automatically resumes and rewrites its private state file and always returns a sanitized player view.
- Added `state-check PROJECT STATE` for read-only validation of portable runtime state against the project.
- Runtime-state import now rejects contradictory selection order, wrong Row counts, unknown activation IDs, wrong scalar types, non-finite numeric values, malformed ledgers, and other impossible continuation bookkeeping.
- `export_state()` checks the runner's own bookkeeping before writing a continuation file.
- Player-safe continuation files now use atomic replacement and owner-only permissions where supported instead of the general JSON writer.
- Added deterministic sequence tests across all 31 parity fixtures. They exercise select/deselect sequences, state invariants, and serialize/restore after every step.
- Fixed static validation of `activateThisChoice` and `deactivateThisChoice` so comma-separated target tokens remain literal, matching ICC Plus 2.10.6. Validation no longer trims a target such as `" a"` into `"a"` when the Viewer would not.
- Aligned static and runtime reporting for browser-only effects. `changePointBar`, `changeBackground`, `scrollToRow`, `scrollToObject`, and `isImageUpload` now use one shared effect set in tests so the two reports cannot silently drift again.
- Tightened `runtime-state.schema.json` to describe score and point-effect ledgers instead of accepting arbitrary objects.
- Final normal-suite count before packaging: 183 tests. Compression remains a separate suite.

## 0.9.3

This patch tightens the LM player boundary and makes continuous play safer by default when the new mode is used.

- Added `session --player-safe`. It returns sanitized action results and requested player views while omitting `snapshot`, `runtime_state`, the project fingerprint, and raw event details from stdout. Use it with `--state-out` and `--state-in` so continuation data stays in a machine-owned file.
- Player-safe status results omit Requirement traces, point previews, replacement candidates, unsupported-effect lists, and other internal fields.
- Hidden and nonexistent guessed action targets are normalized to the same `player.unavailable` result in player-safe sessions.
- `view --after` now sanitizes failed pre-actions instead of returning a raw runtime event outside the filtered view.
- Player semantic messages are now allowlisted. An unknown future semantic code gets a generic safe message instead of falling back to an internal runtime message.
- Player point-bar output no longer exposes the creator-only `belowZeroNotAllowed` configuration flag. Affordability still appears through the normal visible selection result.
- Fixed stale LM documentation that still said verbose player view returned raw Requirement traces.
- Added regression coverage for row-capacity message leakage, unknown semantic codes, safe state-file continuation, hidden-versus-missing target probing, snapshot rejection in player-safe mode, and point-bar configuration leakage.
- Normal suite now has 172 passing tests before packaging verification. Compression remains a separate suite.

## 0.9.2

This patch closes player-view information leaks found during a fresh 2.10.6 parity audit and expands the upstream differential suite.

- `view` now removes selected IDs for entities hidden by selected-state Viewer filters.
- Verbose view returns only Requirement text the real Viewer renders. Requirements with `showRequired: false` stay private, and Row Requirements are never emitted because the Viewer uses them only as visibility gates.
- Verbose semantic blockers keep stable error codes but no longer expose raw Requirement traces, forced-provider IDs, point previews, internal paths, or runtime hide-field names.
- Removed internal Row hide flags from player-facing output.
- Expanded the live source differential from 20 to 31 cases, adding ordinary score costs, below-zero blocking, one-based `multiplyByTimes`, selectable Addon parent behavior, forced non-clickable targets, `isAllowDeselect`, Requirement cleanup, Variable/Word changes, and the main Requirement types.
- Rechecked the field catalog directly against the pinned `types.ts`: all 18 entity catalogs and 12 styling groups match with zero missing or extra fields.
- Fixed stale LLM guidance that referred to the retired `iccplus_evaluate_requirements` command.
- Final local verification: 166 normal tests passed. Compression remains separate at 6 passed with 3 optional encoder-dependent skips.

## 0.9.1

This patch re-audits the 0.9 visual workflow and removes several ways an LLM could make silent or repetitive mistakes.

- Visual manifests reject unknown top-level, project, preset, default, and item keys instead of silently ignoring misspellings.
- One visual item can target an explicit `refs` array, which makes family-wide styling concise without broad mutation selectors. Duplicate targets in one manifest are rejected.
- Added `replace_styling` and `unset_styling` for deliberate cleanup of inherited or stale inline styles.
- `customCSSAppend` is idempotent when the same exact CSS block is applied again.
- `visual-audit --asset-root DIR --missing-assets` finds assigned local image paths whose files are missing. The report now labels image kind and reports full matched counts separately from a limited returned sample.
- `visual-audit --manifest-stub` emits a ready-to-fill manifest skeleton for the returned work queue.
- Apply reports include each target's resulting image path alongside source/credit records.
- Added release-version consistency tests and fixed the compression test that still expected 0.8.0.
- Updated current documentation to identify 0.9.1 as the active release while keeping the 0.8.0 parity audit as historical provenance.
- Final local verification: 161 normal tests passed; compression tests passed 6 with 3 encoder-dependent skips. The installed wheel reproduced the audited default export exactly.

## 0.9.0

This release makes image assignment and styling substantially easier for scripted and LLM authoring.

- Added `visual-audit` to return a compact image/style work queue with Row context, text excerpts, current images, templates, widths, styling groups, design groups, and optional local asset existence/size checks.
- Added `apply-visuals` and the `iccplus-visual-manifest` v1 authoring format. It supports reusable presets, per-item image assignment, template/width changes, grouped native styling, global project styling, custom CSS, and copying a proven visual treatment.
- Image source, credit, license, and crop notes can remain in the manifest and apply report without polluting ICC Plus project JSON with non-native metadata.
- Added `docs/VISUAL_WORKFLOW.md`, `schemas/visual-manifest.schema.json`, and `examples/visual_manifest.json`.
- Bumped the tool version to 0.9.0 so this visual-authoring release is unambiguous. Runtime compatibility remains pinned to ICC Plus 2.10.6.

## 0.8.0

The release label 0.8.0 was reused during the parity audit. The current post-audit build is identified by wheel SHA-256 `14631a9726d7035103e590572180050b3db6c385e046da0aaaf4ab04d96b7e02`; the matching source archive hash is recorded in `iccplus-local-v0.8.0-SHA256SUMS.txt`. Documentation that says only `0.8.0` without the audit context may refer to the older V8 artifact.

### 2.10.6 parity audit refresh

- Pinned the audit to upstream ICC Plus 2.10.6 commit `a420836248d32043ae45d03f1b93cdcb9e354663`.
- `new` now reproduces the ICC Plus Creator `Save to Disk` empty-project bytes, including compact JSON, no trailing newline, exact default fields/styling, source spelling quirks, and `activated:[""]`.
- Added a live online differential harness that builds the pinned Svelte Viewer, runs source-level gameplay fixtures in Chromium, compares runtime snapshots and the exact default export, and checks the local field catalog against upstream `types.ts`.
- Corrected Requirement and non-selectable Addon identity handling, creator factory defaults, selectable-Addon transition shape, Backpack-row defaults, and two omitted field-catalog entries.
- Corrected overlapping `selFromGroups`, point-comparison priority `0`, signed/point-backed/malformed repeat counters, per-repeat row-limit changes, row-cap replacement, JavaScript `/ON#` parsing, linked deactivation/self-deactivation, reset replay, selectable-Addon parent cleanup, and Viewer effect ordering.
- Fixed the Revision 5 economy preset interaction: old point-setting presets are now deactivated/reverted before the new preset sets Creation Points.
- Moved compression tests completely out of normal discovery. `python -m pytest` / `./run-tests` run 141 normal tests; `./run-compression-tests` is explicit.

This release turns the headless simulator into a safer player-facing gameplay test runner and includes a source-pinned ICC Plus 2.10.6 parity audit.

- Added `view PROJECT` and session `view` actions. Compact mode returns the visible gameplay surface; verbose mode adds visible titles, descriptions, Scores, Requirements, Addons, selection state, and semantic blockers.
- Hidden Rows, Choices, Addons, and gated point-bar entries are omitted from player view. Direct player actions cannot use hidden IDs as a bypass.
- Images are completely ignored by gameplay output: the runner does not load files/URLs, decode data URLs, inspect dimensions, or return image properties. Image-only hide flags are not retained as gameplay state.
- Added stable semantic failure codes for invalid player mutations. Failed select/deselect actions are transactional, including nested parent activation, points, Variables, Words, row counts, forced-provider bookkeeping, content hiding, and RNG state.
- Fixed selectable Addons under inactive `isNotSelectable` parents. The Addon may internally activate the parent exactly as the Viewer does; direct clicking of the parent remains blocked.
- Fixed forced activation of `isNotSelectable` targets. `isNotSelectable` blocks the forced target only when the activating Choice sets `isNotActiveUnselectable`.
- Split activation ownership from forced locking so `isAllowDeselect` targets remain player-deselectable while provider cleanup still works. Added coverage for an auto-active provider using this behavior.
- Fixed `multiplyByTimes` to use Viewer ordering: 1x, 2x, 3x, ... rather than starting at 2x.
- Clean sessions now apply `isAutoActive` defaults and preserve their forced/default semantics.
- Added Viewer-style Row/Choice/Add-on visibility filtering, `isContentHidden` gameplay effects, `showAllAddons`, point-bar gates, and live Word/Point/multi-select text replacement in verbose descriptions.
- Added `docs/GAMEPLAY_RUNNER.md` and expanded testing, LLM, CLI, and session documentation around player-surface testing.
- The final audited normal suite contains 141 non-compression tests; compression remains opt-in.

## 0.7.0

This release makes large LLM-authored edits safer and makes common ICC Plus Choice effects much shorter to express.

- Added `match PROJECT WHERE` to preview the exact structural selector used by bulk edits.
- Added exact bulk selectors for kind, ID, ID prefix, Row, parent, Group, title/text substring, path prefix, and Backpack scope.
- Added `expect` count assertions and `allow_empty` controls. A stale generated selector can fail the complete atomic batch instead of silently editing the wrong number of objects.
- Added the bulk `effects` operation, which applies one compact effect bundle to explicit targets or a selector.
- Added the same `effects` object to generated Choices and selectable Addons. It expands to ordinary native ICC Plus fields; there is no second runtime format.
- Added compact helpers for activation/deactivation, content hiding, Row-limit changes, Variables, Point transforms, Word changes, repeated selection, discounts, random activation, scrolling, templates, widths, SFX, delays, background and point-bar changes, confirmation, selection flags, Row duplication, Addon display, BGM, transitions, random weights, Backpack-button requirements, and default images.
- Compact effects reject conflicts with explicitly supplied native fields rather than choosing one silently.
- Strengthened the identity documentation: every authored identity-bearing entity is normalized and checked, including nested Requirements, non-selectable Addons, selectable Addons, and Score `idx` values. Reference fields such as Score `id` and runtime Discount `id` are not misclassified as new identities.
- Added generated-identity stress tests, bulk-selector atomicity tests, semantic-effect tests, selectable-Addon effect tests, and operation-result snapshot tests.
- Added `BULK_SELECTORS.md` and `EFFECTS_FORMAT.md`, plus new generation and bulk-edit examples.
- Renamed the compressor regression module so it runs under normal test discovery. The complete discovered suite now runs 94 tests, with 3 optional encoder integration tests skipped unless explicitly enabled.

## 0.6.0

This release folds general CYOA release tooling into the main CLI and removes more scripting friction.

- Integrated the existing `cyoa-compress` image compressor into `iccplus-local`. The same package now provides `compress`, `asset-probe`, `doctor`, and the compatibility `cyoa-compress` command.
- Directory image compression remains copy-based and rewrites local references when a converted image changes extension.
- Compression now requires at least 256 bytes and 2 percent savings by default before accepting a lossy conversion.
- Added `search PROJECT QUERY` for ID, title, debug-title, and text lookup with fuzzy fallback.
- Added `describe COMMAND` for machine-readable CLI grammar.
- Added `project` and `backpack_row` field-catalog kinds.
- `new` no longer replaces an implicit `project.json`; repeated implicit runs use numbered names.
- `generate` can omit `-o` and chooses a non-destructive output name.
- `scenario` input defaults to stdin.
- `session --state-in` now accepts inline JSON, `@file`, a file path, or stdin as documented.
- `apply` now accepts inline JSON/JSONL and `@file` in addition to ordinary files and stdin.
- Fixed long inline JSON being mistaken for a filesystem path.
- `show` gives close ID suggestions when a reference is not found.
- Compact output now uses minimal JSON separators.
- Corrected stale documentation that described the pre-0.5 invalid-write behavior.
- Merged the compressor regression suite into the main test suite.

## 0.5.0

This release makes the CLI shorter and safer for generated scripts.

- Validation-safe writes are now the default for generation, direct mutation, normalization, and successful atomic batches. Validation errors leave the target unchanged unless `--allow-invalid` is explicit.
- Added `check PROJECT` to combine project-shape, identity, summary, and static validation checks.
- Non-interactive stdout is compact JSON automatically. Interactive terminals use readable JSON. Added `--pretty` to force multiline output.
- Command-line usage and input errors are structured JSON on stderr.
- `generate` source and `apply` script input now default to stdin when omitted.
- Added repeatable `--field NAME=VALUE` for concise `add` and `update` commands. Plain text does not need JSON string quoting. Native field names used through `--field` are checked against the pinned catalog.
- `set` accepts plain text as well as JSON values.
- Atomic operation scripts accept a single operation object in addition to wrapped JSON, arrays, and JSONL.
- Added `ref` and `refs` aliases plus singular one-item forms for targets, members, rows, and content.
- `add`, `upsert`, `update`, and `update_many` may put native entity fields directly on the operation object. Inline field names are checked against the pinned catalog. The nested `values` form remains available for forward-compatible fields.
- Fixed `capabilities` with no output-format flag after the smart-output change.
- Expanded the suite to 66 passing tests.

## 0.4.0

Adds native-field discovery for scripted authoring.

- Added `fields KIND` for machine-readable discovery of native ICC Plus field names from the pinned 2.10.6 TypeScript model.
- Added `--contains` filtering so scripts can search feature families such as `discount`, `button`, `random`, `icon`, or `pointType`.
- Added styling discovery with `fields styling --style-group ...`.
- Choice and selectable-Addon catalogs include the shared optional Choice-function fields, not only fields present in default templates.
- Added `docs/FIELD_CATALOG.md` and linked field discovery from the CLI reference and main README.
- Expanded the suite to 52 passing tests.

## 0.3.1

Patch release for safer scripted project discovery.

- Added a shared ICC Plus project-shape guard. Existing-project commands now reject unrelated JSON before indexing or mutation.
- `summary`, `ids`, and `validate` return structured shape diagnostics for wrong-format input.
- Verified the guard against the current Revision 5 structured-source aggregate, which correctly reports missing `/rows` and non-array `/groups`.
- Added `--compact` to every JSON-producing command for a uniform scripting interface.
- Expanded the suite to 49 passing tests, including wrong-format and universal compact-output CLI tests.

## 0.3.0

This release makes the command line the supported scripted authoring interface.

- Added `generate` for complete project generation from compact ICC-shaped JSON.
- Added deterministic automatic identities for missing identity-bearing entities.
- Added a project-wide uniqueness check to every mutating CLI write path.
- Explicit duplicate IDs now fail instead of being silently changed.
- Added `ids` for identity audits and `template` for native entity starter shapes.
- Added atomic `apply` scripts in JSON, JSON array, or JSONL form.
- Added ID-based `upsert`, `update_many`, and `delete_many` operations.
- Added `require`, `exclude`, `score_many`, `group_members`, and `design_group_members` bulk helpers.
- Reconciles Group membership from either native representation during generation, so `Group.elements` and entity `groups` do not drift apart.
- Added `hidden_until` and `visible_if` generation shorthand for Rows and Choices.
- Added `gate` and `ungate` bulk operations for hiding existing content behind an option.
- Added `hide_contents` for ICC Plus's separate content-hiding feature.
- Added read-only `list` filters for Row, parent, Group, and ID prefix.
- Added validation warnings for duplicate mechanical Requirements, duplicate mechanical Scores, and repeated list references.
- Kept portable `session` state for playthroughs that continue across processes or LLM turns.
- Removed the extra `iccplus` console alias. The installed command is `iccplus-local`.
- Added detailed generation, identity, bulk-edit, effect, field-reference, scripting, testing, and session documentation.
- Expanded the test suite to 47 passing tests, including seven subprocess CLI integration tests.
- Fixed JSONL operation scripts from stdin and files so multi-line object streams no longer get mistaken for one JSON document.
- Added shared project-shape checks to `summary`, `ids`, and `validate`, so non-ICC-Plus JSON cannot appear to be an empty clean project.

- Added symmetric Group and design-group membership normalization, including Row, Backpack, and Group design membership, with safe duplicate removal for set-like membership arrays.
- Added regression coverage for reverse membership reconciliation and Backpack design groups.

## 0.2.0

Added portable runtime state, JSON session requests, project fingerprints, saved random state, continuous sessions, LLM-oriented docs, and session schemas.

## 0.1.0

Initial local authoring, validation, simulation, compatibility, exploration, and scenario-testing release.
