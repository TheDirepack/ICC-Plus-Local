# Sparse project serialization

ICC Plus Local targets ICC Plus 2.10.7 at upstream commit `1ea9db888cde2286d18d0d5de50933cb8773b739`.

Normal saved `project.json` serialization should omit every field that is proven behavior-equivalent when absent in that pinned Viewer. This is the default project-save policy as well as the Viewer-package policy. It is not a generic "remove defaults" pass and it does not change source-level project intent.

ICC Plus Local hydrates and validates a Creator-complete in-memory project before a normal valid write, then sparsifies the full-project JSON. This rule applies to every project-JSON-producing path: normal edits, generation/builds, `project hydrate`, formatting, separate-image exports, and Viewer packages. A command writes a materialized/non-sparse project only when that command explicitly receives `--not-sparse` (or `--not_sparse`).

This means a normal saved project is expected to pass compatibility validation, not complete validation. Use `project validate` for the normal artifact and `project validate --complete` only when checking an explicitly materialized Creator-complete form.

## Automatic omissions

The serializer currently removes these classes of values by default:

- top-level values that exactly equal pinned `defaultApp`, except `version`;
- top-level runtime/legacy fields that the Viewer discards during load;
- stock `viewerConfig`, `styling`, and `backpack` only when the entire object or array exactly equals the pinned built-in value;
- the five explicitly reconstructed multi-choice styling members in a retained custom global `styling` object;
- Row and Choice `index`, which the Viewer rebuilds from array position;
- `isBackpack: true` on backpack Rows;
- Addon `template` when it is `0` or `1`, because missing/`0`/`1` all normalize to effective template `1` in the pinned Viewer;
- Addon derived `parentId` and empty `requireds`;
- Point `initValue` when it equals `startingSum`;
- Word `replaceText: ""`;
- Design Group `activatedId`, `elements`, `backpackElements`, and `groupElements` when they equal the loader defaults;
- Choice `initMultipleTimesMinus` only when it equals the value the Viewer will derive;
- Choice `addonJustify` only when it equals the effective inherited project/default value;
- object properties whose value is `null`, matching the proven object-property portion of the Viewer import cleanup;
- private-filter missing-value defaults only while `privateFilterIsOn` remains explicitly true. These use the private initializer's own values, not global styling defaults.

The private-filter distinction matters: the pinned global styling default for `unselFilterSatur` is `1`, while the private missing-field initializer uses `0`. An explicit private `unselFilterSatur: 1` therefore remains serialized.

## Deliberately not automatic yet

The default serializer does not remove a field merely because the schema marks it optional or because it matches a Creator construction default.

The unresolved set includes:

- individual members of a retained custom `viewerConfig`;
- individual stock-valued members of an otherwise custom global `styling` object, except the five source-proven members already listed above;
- private-style enable flags whose absence may cause the Viewer to infer a different style source;
- stock-valued private-style members whose absence may fall back to project/Design-Group styling, reconstruct a local default, or remain undefined;
- list-level filtering of `null` or empty-object entries;
- Creator Save-to-Disk's empty `activated: [""]` representation versus omitting `activated` and taking the Viewer's built-in empty state;
- any other Row, Choice, Addon, Requirement, Score, or styling field without an explicit loader reconstruction rule or equivalent pinned-Viewer proof.

Fields already shown by source/schema behavior to be required or directly behavior-bearing are treated as unsafe rather than queued for redundant browser testing.

## Browser verification kit

Generate the exhaustive one-omission-at-a-time matrix with:

```text
iccplus-omission-probe -o verification/sparse-omission
```

The same generator is available as:

```text
python -m iccplus_tools.omission_probe -o verification/sparse-omission
```

For incremental testing, restrict output by exact case ID or manifest category:

```text
iccplus-omission-probe --case viewer-config-title -o verification/one-case
iccplus-omission-probe --category private-style-enable-inference -o verification/private-flags
iccplus-omission-probe --core-only -o verification/core-omissions
```

The generated `manifest.json` reports a case count and per-category counts. `results.json` is a matching test ledger with every case initially marked `untested`; record the Viewer build, browser, rendering/interaction/save-reload equivalence, console errors, and notes there. Valid statuses are `equivalent`, `behavior-change`, `load-failure`, and `needs-more-testing` in addition to `untested`.

The default exhaustive matrix covers:

- every member of a retained custom `viewerConfig`;
- every not-yet-proven stock-valued member of a retained custom global `styling` object;
- every applicable Row/Choice private-style enable flag, including `privateMultiChoiceIsOn`;
- every not-yet-proven member in the private filter, text, object-image, object, row-image, row, addon-image, addon, background, and multi-choice styling families;
- native-array `null` and empty-object cleanup using `mdObjects`;
- the empty `activated` build-state representation;
- a known private `unselFilterSatur: 1` negative control.

Ordinary omission candidates differ from their baseline by one removed field. The array-cleanup probes deliberately use a pre-import baseline containing the invalid member under test and a cleaned schema-valid control.

Load each pair separately in the pinned Viewer and compare load success, rendering, style source, interaction behavior, counters/scores, save/reload behavior where relevant, and browser-console errors. Load success alone is not enough to promote a rule.

When a case is confirmed behavior-equivalent, add a regression test and promote only that exact omission rule into the default serializer. When it changes behavior, keep the field explicit and record the negative result so it is not repeatedly re-tested.

## Version policy

Omission rules are native Viewer behavior and are pinned to the ICC Plus version and source commit. Re-audit the whitelist whenever the Viewer target changes. Do not carry omission rules forward to a new Viewer version by assumption.

## Compiler boundary

Sparse project serialization is not source normalization. The compiler remains responsible for semantic transformations such as Requirement hoisting, Row merging, taxonomy pruning, style-intent consolidation, Pick-N derivation, and runtime-ID compaction. ICC Plus Local only removes native serialized values whose omission has already been shown not to change the pinned Viewer's behavior.
