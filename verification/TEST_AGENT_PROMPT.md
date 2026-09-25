# Prompt for the ICC Plus testing agent

You are testing ICC Plus Local 0.10.0rc11 against ICC Plus 2.10.6. Your job is to observe the official Creator and Viewer, not to infer what they should do from the local tool.

Read these files before starting:

- `OFFICIAL_GUI_TEST_PLAN.md`
- `expected/runtime_cases.json`
- `expected/creator_cases.json`
- `expected/advanced_cases.json`
- `expected/coverage_manifest.json`

Use `results_template/official_results.json` as the result file. Do not replace its fixture names or SHA-256 values.

## Runtime tests

R01 through R32 each have a separate fixture under `fixtures/runtime_cases/`. Use the fixture named in that test's `fixture` field. Do not use `02_runtime_matrix.json` to execute runtime tests. The matrix exists only as a compact reference.

For each R test:

1. Load that test's isolated fixture in ICC Plus 2.10.6.
2. Confirm the file name and SHA-256 recorded in the result template.
3. Perform only the listed actions.
4. Observe the official GUI before looking at `expected`.
5. Record the official Build Form string only by opening ICC Plus Build Form and copying its text. Do not construct the string from selected IDs and do not use ICC Plus Local to produce the official observation.
6. Record Point values, Variables, Words, selected state, repeat counts, Row counts, and Requirement outcomes only when the official GUI exposes them. If a value cannot be observed without changing state, say so in `notes`.
7. Set `observation_source` to `official_gui` for any `pass` or `fail` result.

Selectable Addons and Point Types are valid test targets. Do not search only normal Choice IDs. The exact IDs for each case are in that case record and in its isolated fixture.

## Creator tests

Run C01 through C12 from `expected/creator_cases.json`. Preserve every requested export byte-for-byte. Feature management is under the Creator's `Features` dialog. The pinned 2.10.6 labels include `Manage Points`, `Manage Variables`, `Manage Groups`, `Manage Backpack and Choice Import`, `Manage Defaults`, `Style Template`, `Words`, `Symbols and Image Compression`, `ID / Name List`, `Manage Design Groups`, `Manage Global Requirements`, and `Manage Sound Effects`.

When a test asks you to enable a control such as selectable Addon, use the normal Creator control and allow its click/change handler to run. Do not set the bound checkbox value directly through DOM or framework internals. For example, enabling a selectable Addon normally generates its Addon ID.

## Advanced tests

Run A01 through A12 from a fresh reload of `fixtures/03_advanced_interaction_export.json` for each case. Row buttons are real Viewer actions. `adv_button_var`, `adv_button_point`, and `adv_button_choice` are configured as native ICC Plus button Rows. Use their visible button controls in the official Viewer.

A02 and A04 require a real Build Form round trip. Copy the official Build Form text, reload the fixture, paste that exact string back into Build Form, and observe the restored state.

A03 and A11 should include screenshots. A12 should return the official ZIP files unchanged.


## Structured evidence format

A prose note is not enough for `pass` or `fail`. The verifier checks structured official-GUI evidence.

For every runtime R case marked `pass` or `fail`, record the state after **every** prescribed action plus the final state:

```json
{
  "action_observations": [
    {
      "step": 1,
      "snapshot": {
        "entities": {"some_id": {"active": true, "multiple": 0}},
        "points": {"point_id": 7},
        "build_string": "some_id"
      }
    }
  ],
  "snapshot": {
    "entities": {"some_id": {"active": true, "multiple": 0}},
    "points": {"point_id": 7},
    "build_string": "some_id"
  }
}
```

`action_observations` must contain exactly one entry for every prescribed action, in order. A case with no actions uses `[]`. Each action snapshot must include the values that visibly changed because of that action; the verifier knows which changed fields are required for each fixture. This matters for cases where the final state alone is ambiguous after a toggle, deselect, or reset. The final `snapshot` must also contain concrete official Viewer/Build Form values. Include only values you genuinely observe. Local-simulator output belongs in notes or a separate diagnostic file and does not count as official evidence.

For every Creator or advanced C/A case marked `pass` or `fail`, fill:

```json
{
  "completed_steps": [1, 2, 3],
  "checks": [
    {"step": 1, "status": "pass", "evidence": "What was actually seen in the GUI"},
    {"step": 2, "status": "pass", "values": {"example": "observed value"}},
    {"step": 3, "status": "pass", "artifact": "returned_artifacts/example.json"}
  ]
}
```

Every prescribed step must be represented. A case cannot be `pass` when any step was skipped, incomplete, blocked, or failed. Use `blocked` for the case instead. Any artifact path named in `artifacts` or a check must be returned in the same result bundle.

## Evidence rules

Creator components, style presets, compact authoring helpers, and verification metadata are authoring inputs only. If tool-specific template or verification objects appear in exported `project.json`, mark the case failed and preserve that export.

Do not normalize JSON, sort keys, reformat files, unpack and repack ZIPs, or repair negative fixtures. Do not use a local simulator observation as the official result. If browser automation cannot perform a normal GUI action, mark the test blocked and explain what control could not be operated.

Before returning the results, put `official_results.json` and every returned artifact under one directory, or ZIP that directory unchanged, then run one of:

`python verification/scripts/verify_returned_results.py path/to/result-directory`

`python verification/scripts/verify_returned_results.py path/to/results.zip`

A standalone JSON is accepted too, but any artifact it names must exist relative to that JSON file.

A structurally valid but incomplete run now exits with code 3 and lists every pending, blocked, or not-applicable case. Return a code-3 run only if you genuinely could not complete those cases. Return the completed result JSON, all requested exports, screenshots, and browser logs.
