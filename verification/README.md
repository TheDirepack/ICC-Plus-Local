# ICC Plus 2.10.6 external verification kit

This directory is the handoff for testing ICC Plus Local against the official ICC Plus 2.10.6 Creator and Viewer.

Start with `TEST_AGENT_PROMPT.md`. It is written so it can be pasted into another agent session. `OFFICIAL_GUI_TEST_PLAN.md` is the human-readable procedure. The three files under `fixtures/` are the only CYOA project files that need to be imported. Files under `expected/` are reference data and must not be imported as projects.

`expected/runtime_cases.json` contains the 32 deterministic runtime sequences and local expected values. `expected/creator_cases.json` contains Creator workflow tests. `expected/advanced_cases.json` contains the browser-heavy interaction tests. `expected/coverage_manifest.json` maps the audited Creator feature list to test groups. `expected/template_boundary.json` proves that no known ICC Plus Local template metadata is present in the generated project fixtures.

Copy `results_template/official_results.json` to a new results file. Fill one entry for every runtime, Creator, and advanced test ID. Add returned JSON, ZIPs, screenshots, or logs to a `returned_artifacts/` folder. Do not alter an exported file before returning it.

Run `python verification/scripts/verify_returned_results.py RESULTS.json` before handing the results back. That command checks that every required test ID has a status and that failures and blocked cases include notes.


## Race-capture ZIP differential (newer Viewer evidence)

The independent race-capture comparator is separate from the historical 2.10.6
Creator verification kit. It replays saved states against the current ICC Plus
Local simulator and compares recorded official Viewer rows, Build Form strings,
and—when the capture actually includes them—main Choice DOM cards.

```bash
python verification/scripts/check_race_capture_parity.py \
  --inputs final_outputs/RUN_ID/inputs.zip \
  --package-index final_outputs/RUN_ID/PACKAGE_INDEX.json \
  --require-choice-cards \
  --output final_outputs/RUN_ID/race_parity_report.json \
  final_outputs/RUN_ID/races-*.zip
```

The `--package-index` file is the **source-created Dev220 v3 inventory**: its
run/source pins, complete race-shard list, exact archive SHA-256s, and
race-to-part membership must match the supplied ZIPs. Without it, the tool
still reports any matching race observations, but `fully_verified` is **false**
because missing shards cannot be ruled out. It also verifies every consumed
ZIP member against that ZIP's internal manifest. A mismatch in archive
identity or completeness is an evidence error, **not** a gameplay failure.

`--require-choice-cards` marks older row-only captures incomplete instead of
misrepresenting them as complete Choice-card differentials. The complete-card
check requires a DOM inventory in *every* frame, and verifies Choice identity
together with the displayed Row. Dynamic Result/Group Row card inventories are
currently not modeled by this checker and remain **incomplete**, never silently
accepted or mislabeled as mismatches. Plain row-only comparisons remain useful
for the older 299-race capture set, but do not establish browser acceptance for
Dev220 or any newer project.

A fully verified race comparison is not a complete package-evidence audit,
visual/layout acceptance, Creator GUI test, or proof that the complete capture
run passed. For whole-bundle integrity including the regular capture shards,
run Dev220's `verify_evidence_bundle.py` on the same directory.
