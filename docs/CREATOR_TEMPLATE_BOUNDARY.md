# Creator templates do not belong in project JSON

ICC Plus Local has authoring conveniences such as compact effects, style presets, generated components, design files, and verification metadata. They exist to make a project easier to create. They are not a second project format.

The finished `project.json` must contain ordinary ICC Plus 2.10.7 data only. A style preset writes its native styling fields into `app.styling`. A compact effect writes the corresponding native Choice or selectable Addon fields. A reusable authoring component expands to native Rows, Choices, Addons, Scores, Requirements, and feature objects. Design import copies native styling fields into the selected ICC Plus object. None of these operations may add a serialized `styleTemplate`, `creatorComponent`, component definition, provenance record, or other ICC Plus Local object to the exported project.

This rule does not remove ICC Plus's own fields named `template`, `defaultTemplate`, `templateStack`, or related fields. Those are native ICC Plus fields and must remain exactly as the upstream format expects.

The external verification kit scans every main fixture and all 32 isolated runtime fixtures for known tool-only keys before packaging. `tests/test_external_verification_kit.py` repeats that check in the normal regression suite. The field-retention fixture also places every pinned native field in a real ICC Plus object shape so the official Creator can load and re-export it.

Verification sidecars live under `verification/expected/` and `verification/results_template/`. They may describe templates, test cases, expected values, source evidence, and hashes because they are not imported as CYOA projects.
