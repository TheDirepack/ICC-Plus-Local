# Official GUI test plan

## Setup

Use ICC Plus 2.10.6. Record the exact public page or pinned local build, browser name and version, and test dates. The target source commit is `a420836248d32043ae45d03f1b93cdcb9e354663`.

Create a working copy of `results_template/official_results.json` and a `returned_artifacts/` directory. Do not edit project fixtures by hand.

The verification kit contains three compact project families, plus isolated runtime copies:

- `01_field_retention.json` covers every declared native field at least once.
- `02_runtime_matrix.json` is a compact reference containing all runtime cases. Do not execute tests from it.
- `runtime_cases/R01.json` through `runtime_cases/R32.json` are the mandatory runtime execution fixtures.
- `03_advanced_interaction_export.json` combines browser-heavy features so advanced coverage stays compact.

Each isolated runtime fixture has its own SHA-256 in `expected/runtime_cases.json` and in the result template. This prevents state from one case from reaching another case.

## Phase 1. Creator serialization and authoring

Run C01 through C12 from `expected/creator_cases.json`.

C01 is the serialization gate. Load the field-retention fixture, make no edits, use Creator `Save to Disk`, and return the JSON unchanged. This case checks native load-time normalization as well as the rule that authoring templates never become project objects.

For C02, use normal Creator controls for Addon selectability and other toggles. Do not assign bound state directly. Normal Creator handlers may generate IDs or initialize fields.

For C03, open `Features`. The important 2.10.6 labels are:

- `Manage Points`
- `Manage Variables`
- `Manage Groups`
- `Words`
- `Manage Design Groups`
- `Manage Global Requirements`
- `Manage Sound Effects`

Each of the first six category-backed managers opens on a Categories screen. Click the large `Show All` tile to enter the actual entity manager. Do not treat the Categories screen itself as the manager. `Manage Design Groups` uses left/right arrows in the category header to switch Row and Choice Design Groups.

For C07, apply each of the eight Style Template buttons from a fresh reload. The expected output is native styling fields. The preset definition itself must not appear in project JSON.

For C11, also exercise `Symbols and Image Compression`, including `Clean All Private Styling`, `Compress All Images`, and one real image crop through the Creator image dialog.

For C12, return the raw Save to Disk JSON, separate-image ZIP, and playable viewer ZIP. If manual save slots/autosave are available, verify them as browser-storage behavior without treating their storage records as project JSON. Do not repack either archive.

## Phase 2. Runtime cases

For each R case, load the exact `fixture` named by `expected/runtime_cases.json`. Never continue from another R case.

Perform the listed actions in order. The action ID may be a Choice, selectable Addon, Point Type, Variable, or another native entity. Do not limit ID lookup to normal Choices.

Observe the official state before reading `expected`. For Build Form checks, open the official Build Form and copy the displayed string. Do not derive it from selected IDs or from local-tool output.

The expected record may contain values that the normal Viewer does not display directly. Record the observable official subset. Do not use a local tool result to fill an official field. If a required official observation cannot be obtained without mutating state, explain that limitation rather than guessing.

R32 is a reset-state case. Follow its case notes exactly. If the current official UI cannot produce the pre-reset Point mutation through normal controls, mark only that observation blocked and preserve the rest of the official reset evidence.

## Phase 3. Combined browser interactions

Run A01 through A12 from a fresh load of `03_advanced_interaction_export.json` for every case.

The Row-button fixture has three valid native button modes:

- `adv_button_var` toggles `adv_flag`.
- `adv_button_point` uses the `sumaddon` random Point branch on `adv_power`.
- `adv_button_choice` contains two weighted Choices with weights 1 and 9.

A02 and A04 require Build Form round trips. A03 and A11 need screenshots. A05 records timing/media behavior and browser errors separately. A12 returns official exports unchanged.

## Phase 4. Result validation

Every result entry records its fixture path, fixture SHA-256, status, observation source, structured observed data, notes, and artifacts.

A `pass` or `fail` counts as official evidence only when `observation_source` is `official_gui`. `local_tool` and `source_only` may be used for notes, but they cannot satisfy an official test. Runtime pass/fail entries must include one `observed.action_observations` snapshot after every prescribed action plus a non-empty final `observed.snapshot`; changed fields required by each case must be present. Creator and advanced pass/fail entries must include `observed.completed_steps` covering every prescribed step plus per-step `observed.checks`.

Do not mark a partially executed case as pass. If even one prescribed step cannot be completed through the normal GUI, mark the case blocked and explain the stopping point.

Return every file named in an entry's `artifacts` array. Artifact paths are validated against the returned directory or ZIP, so a missing claimed export or screenshot is a verification error. Fill `finished_at` when the run ends.

Run `verify_returned_results.py` against the whole returned directory or ZIP when possible. The report has separate `schema_ok` and `complete` fields. A run with blocked or pending cases is not complete even when its JSON is structurally valid.

Return the completed JSON and all artifacts without rewriting them.
