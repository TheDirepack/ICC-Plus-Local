# ICC Plus 2.10.6 external verification kit

This directory is the handoff for testing ICC Plus Local against the official ICC Plus 2.10.6 Creator and Viewer.

Start with `TEST_AGENT_PROMPT.md`. It is written so it can be pasted into another agent session. `OFFICIAL_GUI_TEST_PLAN.md` is the human-readable procedure. The three files under `fixtures/` are the only CYOA project files that need to be imported. Files under `expected/` are reference data and must not be imported as projects.

`expected/runtime_cases.json` contains the 32 deterministic runtime sequences and local expected values. `expected/creator_cases.json` contains Creator workflow tests. `expected/advanced_cases.json` contains the browser-heavy interaction tests. `expected/coverage_manifest.json` maps the audited Creator feature list to test groups. `expected/template_boundary.json` proves that no known ICC Plus Local template metadata is present in the generated project fixtures.

Copy `results_template/official_results.json` to a new results file. Fill one entry for every runtime, Creator, and advanced test ID. Add returned JSON, ZIPs, screenshots, or logs to a `returned_artifacts/` folder. Do not alter an exported file before returning it.

Run `python verification/scripts/verify_returned_results.py RESULTS.json` before handing the results back. That command checks that every required test ID has a status and that failures and blocked cases include notes.
