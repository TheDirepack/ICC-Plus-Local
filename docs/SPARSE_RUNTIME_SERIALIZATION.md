# Sparse project serialization

ICC Plus Local targets ICC Plus 2.10.7 at upstream commit `1ea9db888cde2286d18d0d5de50933cb8773b739`.

Normal saved `project.json` serialization omits fields only when their absence is proven safe for both the pinned Viewer behavior and ICC Plus Local's authoring round trip. This is the default project-save policy as well as the Viewer-package policy. It is not a generic "remove defaults" pass and it does not change source-level project intent.

ICC Plus Local hydrates and validates a Creator-complete in-memory project before a normal valid write, then sparsifies the full-project JSON. This rule applies to every project-JSON-producing path: normal edits, generation/builds, `project hydrate`, formatting, separate-image exports, and Viewer packages. A command writes a materialized/non-sparse project only when that command explicitly receives `--not-sparse` (or `--not_sparse`).

A canonical sparse saved project must remain usable as an authoring artifact. Hydrating it back to the complete Creator shape must not require inventing stable entity identities or non-derivable authoring values. The current shared serializer therefore keeps some data that the Viewer alone could ignore or reconstruct. Score `idx` and Sound Effect `name` are the important examples: the Viewer does not need the serialized Score identity for player behavior and does not use the Sound Effect label for playback, but ICC Plus Local needs those values to preserve cross-command authoring semantics.

This means a normal saved project is expected to pass compatibility validation, not complete validation. Use `project validate` for the normal artifact and `project validate --complete` only when checking an explicitly materialized Creator-complete form.

The no-read rules below were checked against the pinned 2.10.7 Viewer source. The immediately following 2.10.8 upstream commit was also reviewed to make sure a field was not being classified as unused merely because its read path disappeared after 2.10.7; that commit changes the relevant Viewer store only for a Point legacy-version check and Addon width-stack handling.

## Automatic omissions

The serializer removes four broad classes of data: exact built-in defaults that the Viewer reconstructs, values the Viewer never consumes, values the loader deterministically rebuilds, and narrow legacy values whose modern replacement already preserves the same behavior. For normal saved project JSON, an omission must also preserve the authoring round trip.

### Exact or reconstructed defaults

- top-level values that exactly equal pinned `defaultApp`, except `version` and the separately handled special fields below;
- stock `viewerConfig`, `styling`, and `backpack` only when the entire object or array exactly equals the pinned built-in value;
- the five explicitly reconstructed multi-choice styling members in a retained custom global `styling` object;
- Row and Choice `index`, which the Viewer rebuilds from array position and which are not stable authoring identities;
- `isBackpack: true` on backpack Rows;
- Addon `template` when it is `0` or `1`, because missing/`0`/`1` all normalize to effective template `1` in the pinned Viewer;
- Addon derived `parentId` and empty `requireds`;
- Point `initValue` when it equals `startingSum`;
- Word `replaceText: ""`;
- Group `elements` and `rowElements` when they are empty, because the Viewer reconstructs both arrays during load;
- Design Group `activatedId`, `elements`, `backpackElements`, and `groupElements` when they equal the loader defaults;
- Choice `initMultipleTimesMinus` only when it equals the value the Viewer will derive;
- Choice `addonJustify` only when it equals the effective inherited project/default value;
- `Row.width: false`, because every Viewer use treats missing and `false` identically while `true` changes layout;
- `Addon.skipIndex: false`, because every Viewer use treats missing and `false` identically while `true` changes Addon indexing;
- object properties whose value is `null`, matching the proven object-property portion of the Viewer import cleanup;
- Row/Choice private-filter missing-value defaults only while `privateFilterIsOn` remains explicitly true. These use the Row/Choice private initializer's own values, not global styling defaults. Design Groups are excluded from this rule because their load path does not reconstruct those private-filter values the same way.

Score `idx` is intentionally not in this omission set. The pinned Viewer can assign a fresh internal score ID when it is absent, but ICC Plus Local treats `idx` as the stable Score identity used by authoring commands, validation, and later edits. Hydration does not invent missing entity identities, so canonical sparse project JSON retains it.

The private-filter distinction matters: the pinned global styling default for `unselFilterSatur` is `1`, while the private missing-field initializer uses `0`. An explicit private `unselFilterSatur: 1` therefore remains serialized.

### Viewer-discarded, Creator-only, or unread data

The following are removed regardless of whether they equal stock defaults, unless the authoring-round-trip rule requires retaining a value:

- top-level runtime/legacy fields in the Viewer's `keysToRemove` list;
- the Creator category table and per-entity `category` indices on Point Types, Variables, Words, Groups, Global Requirements, and Row/Choice Design Groups; these organize Creator dialogs and have no player-Viewer read path;
- Creator edit state: top-level `isEditModeOnAll`, Row `isEditModeOn` / `isSimpleEditMode` / `isRequirementOpen`, and Choice/Addon `isEditModeOn`;
- Creator temporary buffers `tmpRow`, `tmpChoice`, `tmpRequired`, `tmpScore`, `tmpAddon`, `tmpGroup`, and `tmpDesignGroup`;
- Creator-only autosave/confirmation state: `printThis`, `autoSaveIsOn`, `buildAutoSaveIsOn`, `buildAutoSaveInterval`, `checkDeleteRow`, `checkDeleteObject`, and `checkSelectAll`;
- Creator-only authoring UI preferences `compressImageAuto`, `useTextEditor`, `useChoiceEditBtn`, and `enableShortcut`;
- Creator construction defaults that have already been copied into created entities: Row/Choice/Addon default titles/text, Point/Requirement label defaults, Row/Choice/Addon template/width defaults, Row justify/allowed-choice defaults, and the default Addon/Score/Requirement creation toggles;
- Creator-facing entity labels that have no player read path and are not needed as local authoring handles: Group `name`, Row/Choice Design Group `name`, and Global Requirement `name`;
- Sound Effect authoring metadata `isDefault`, `onSelected`, `onDeselected`, and `groups`; runtime sound playback uses the Sound Effect ID, audio, volume, pitch, and requirements instead. Sound Effect `name` is retained because it is a non-derivable authoring label used by ICC Plus Local workflows;
- Requirement structural `id`, which has no Viewer read path;
- `Requirement.more: []`, because the point-comparison evaluator only iterates it when present and an empty list contributes no operation;
- Choice `selectedThisManyTimesProp`, Row `imageIsUrl`, and Point Type `imageIsURL`, which survive type/schema history but have no player Viewer read path;
- Score `type` and the unread Score scratch/history members `discountScoreCal`, `isChangeDiscount`, `discountNum`, `tmpDisScore`, `tmpDiscount`, `discountedFrom`, `dupTextA`, `dupTextB`, `discountTextA`, `discountTextB`, `notStackableDiscount`, and `mulValue`.

This group is intentionally source-driven. Adjacent similarly named fields remain when the Viewer actually consumes them or when ICC Plus Local needs them to preserve authoring state. For example, Score `discountScore`, `appliedDiscount`, and `removeSpace` affect rendering; Score `idx` is stable authoring identity; Sound Effect `name` is a non-derivable authoring label; `defaultChoiceMaxNum` is a runtime fallback for multiple-selection limits; `defaultAddonJustify` is a loader fallback for Choices; `orderOrReqText` / `defaultOrReq` and the selected-from equivalents affect displayed Requirement text; `rowIdLength` / `objectIdLength` are used if identities must be generated; and settings such as `cropperPosition`, `tooltipDelay`, `isPointerCursor`, `importedChoicesIsOpen`, `hideScoresUpdated`, and `useToolbarBtn` still have Viewer read paths.

### Conditional legacy normalization

- exact legacy-OR `orRequireds` payloads are removed when they equal what the pinned loader deterministically regenerates from `orRequired`, limited to the same Row/Choice/Score/Addon/Global-Requirement containers and one nested Requirement level that `initializeApp` migrates;
- legacy Choice/Selectable-Addon `sfxId` is removed only when every enabled SFX direction already has an explicit `sfxIdOnSelect` / `sfxIdOnDeselect`; otherwise it remains because the loader still needs it for backfill;
- legacy Addon `fadeTransitionIsOn` / `fadeTransitionTime` are removed because the pinned Addon load path never consumes them and selectable-Addon runtime transitions use the modern `isFadeTransition` plus separate in/out times;
- legacy Choice transition fields are removed when the loader migration would have no effect, or when `fadeInTransitionTime` and `fadeOutTransitionTime` already exactly equal the legacy `fadeTransitionTime`; they remain when the loader would overwrite different modern values.

The OR-Requirement rule is deliberately structural rather than a blanket empty-array rule. Sound Effect requirements, selectable-Addon Score requirements, deeper nesting, and any nonmatching `orRequireds` remain explicit because the pinned loader does not perform the same migration there. `orRequired` itself is not globally removable: Word Requirements use it directly and runtime Row duplication still traverses it when rewriting cloned IDs.

## Deliberately not automatic yet

The default serializer does not remove a field merely because the schema marks it optional, because it matches a Creator construction default, or because the Viewer can create a runtime substitute that would destroy authoring identity.

The unresolved set includes:

- individual members of a retained custom `viewerConfig`;
- individual stock-valued members of an otherwise custom global `styling` object, except the five source-proven members already listed above;
- private-style enable flags whose absence may cause the Viewer to infer a different style source;
- stock-valued private-style members whose absence may fall back to project/Design-Group styling, reconstruct a local default, or remain undefined; Design Group private-filter members remain explicit unless separately proven safe;
- guarded empty membership arrays whose known Viewer uses tolerate absence but which are not explicitly reconstructed during load: `Row.groups`, `Row.rowDesignGroups`, `Choice.groups`, `Choice.objectDesignGroups`, and `Group.designGroups`;
- list-level filtering of `null` or empty-object entries;
- Creator Save-to-Disk's empty `activated: [""]` representation versus omitting `activated` and taking the Viewer's built-in empty state;
- behavior-bearing runtime/default fields merely because a false/zero/empty value looks default-like; these require an exact missing-value equivalence proof before promotion;
- stable authoring identities and non-derivable authoring handles even when the pinned Viewer does not use their serialized values;
- any other Row, Choice, Addon, Requirement, Score, or styling field without an explicit loader reconstruction rule, a proven no-read Viewer boundary, or equivalent pinned-Viewer proof.

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
iccplus-omission-probe --category guarded-empty-membership -o verification/membership-arrays
iccplus-omission-probe --core-only -o verification/core-omissions
```

The generated `manifest.json` reports a case count and per-category counts. `results.json` is a matching test ledger with every case initially marked `untested`; record the Viewer build, browser, rendering/interaction/save-reload equivalence, console errors, and notes there. Valid statuses are `equivalent`, `behavior-change`, `load-failure`, and `needs-more-testing` in addition to `untested`.

The default exhaustive matrix covers:

- every member of a retained custom `viewerConfig`;
- every not-yet-proven stock-valued member of a retained custom global `styling` object;
- every applicable Row/Choice private-style enable flag, including `privateMultiChoiceIsOn`;
- every not-yet-proven member in the private filter, text, object-image, object, row-image, row, addon-image, addon, background, and multi-choice styling families;
- guarded empty membership arrays for `Row.groups`, `Row.rowDesignGroups`, `Choice.groups`, `Choice.objectDesignGroups`, and `Group.designGroups`;
- native-array `null` and empty-object cleanup using `mdObjects`;
- the empty `activated` build-state representation;
- a known private `unselFilterSatur: 1` negative control.

Ordinary omission candidates differ from their baseline by one removed field. The array-cleanup probes deliberately use a pre-import baseline containing the invalid member under test and a cleaned schema-valid control.

Load each pair separately in the pinned Viewer and compare load success, rendering, style source, interaction behavior, counters/scores, save/reload behavior where relevant, and browser-console errors. Load success alone is not enough to promote a rule.

When a case is confirmed behavior-equivalent, add a regression test and promote only that exact omission rule if it also preserves the authoring-round-trip contract for normal saved project JSON. When it changes behavior or loses stable authoring state, keep the field explicit and record the negative result so it is not repeatedly re-tested.

## Version policy

Omission rules are native Viewer behavior and are pinned to the ICC Plus version and source commit. Re-audit the whitelist whenever the Viewer target changes. Do not carry omission rules forward to a new Viewer version by assumption.

## Compiler boundary

Sparse project serialization is not source normalization. The compiler remains responsible for semantic transformations such as Requirement hoisting, Row merging, taxonomy pruning, style-intent consolidation, Pick-N derivation, and runtime-ID compaction. ICC Plus Local only removes native serialized values whose omission has already been shown not to change the pinned Viewer's behavior and, for normal saved project JSON, not to destroy the state needed for later authoring.
