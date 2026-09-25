# External upstream verification

Version 0.10.0rc7 is the current verification candidate for ICC Plus 2.10.6. It incorporates the usable evidence from the first official-browser run and repairs flaws in the first test package. It still does not claim complete official Viewer parity because the first runtime automation did not produce reliable observations for every case.

The target source commit is `a420836248d32043ae45d03f1b93cdcb9e354663`.

## What the first run proved

The returned C01 Creator export is now a permanent regression fixture. It confirmed these load and Save to Disk behaviors for the field-retention project:

- empty objects removed during project import do not reappear;
- an empty Build Form becomes `activated: [""]` on Save to Disk;
- an empty Choice `addonJustify` is initialized to the project default, which is `start` in the fixture;
- authoring-template and verification metadata did not appear in the official project export.

The returned Creator checkpoints also confirmed source-derived factory defaults used by rc2, including `Design Group N` naming and Sound Effect `pitch: 0`.

## Why the runtime pass must be repeated

Several first-run runtime failures were test-harness failures rather than official ICC Plus observations. The automation searched only some entity kinds, so it reported existing Point Type and selectable Addon IDs as missing. Later cases also carried state from earlier cases. Some Build Form values were reconstructed from local state instead of copied from the official Build Form.

Those results are retained as audit evidence, but they are not used to change Viewer semantics when they conflict with the pinned 2.10.6 source.

rc2 fixes the regimen by giving every R test its own fixture and SHA-256. A pass or failure is accepted as official evidence only when the result says `observation_source: official_gui` and uses the expected fixture hash.

## Fixture layout

`01_field_retention.json` tests every declared native field and Creator serialization. `02_runtime_matrix.json` remains a compact reference. The official runtime pass uses `runtime_cases/R01.json` through `runtime_cases/R32.json`. `03_advanced_interaction_export.json` covers browser-heavy combinations and has corrected native Row-button configurations.

The result validator distinguishes structural validity from completion. Pending, blocked, or not-applicable mandatory cases make `complete` false and normally return exit code 3.

## Evidence policy

The pinned source is authoritative when a browser automation result did not execute the normal GUI handler or did not actually observe the official Viewer. Exported Creator JSON and ZIP files are stronger evidence than a prose note. Official Build Form strings must be copied from the official Build Form itself.

Every confirmed difference becomes a local regression before the next candidate is packaged.
