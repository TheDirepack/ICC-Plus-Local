# Sparse runtime serialization

ICC Plus Local targets ICC Plus 2.10.7 at upstream commit `1ea9db888cde2286d18d0d5de50933cb8773b739`.

Runtime `project.json` serialization should omit every field that is proven behavior-equivalent when absent in that pinned Viewer. This is the default runtime policy. It is not a generic "remove defaults" pass and it does not change source-level project intent.

Creator-complete authoring artifacts remain complete. Creator Save-to-Disk and Creator-compatible project exports preserve the native structure needed for Creator round-tripping. Runtime sparsification is applied when producing the player-facing Viewer payload or an explicit sparse runtime artifact.

## Automatic omissions

The serializer currently removes these classes of values by default:

- top-level values that exactly equal pinned `defaultApp`, except `version`;
- top-level runtime/legacy fields that the Viewer discards during load;
- stock `viewerConfig`, `styling`, and `backpack` only when the entire object or array exactly equals the pinned built-in value;
- the five explicitly reconstructed multi-choice styling members in a retained custom global `styling` object;
- Row and Choice `index`, which the Viewer rebuilds from array position;
- `isBackpack: true` on backpack Rows;
- Addon `template: 1`, derived `parentId`, and empty `requireds`;
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

These cases remain in the verification queue:

- individual members of a retained custom `viewerConfig`;
- private-style enable flags whose absence may cause the Viewer to infer a different style source;
- list-level filtering of `null` or empty-object entries;
- any Row, Choice, Addon, Requirement, Score, or styling field without an explicit loader reconstruction rule or equivalent pinned-Viewer proof.

Private-style enable-flag testing includes `privateMultiChoiceIsOn` as well as the filter, text, image, object, Row, Addon, and background flags exposed by the pinned 2.10.7 native types.

## Browser verification kit

Generate isolated baseline/candidate artifacts with:

```text
python -m iccplus_tools.omission_probe -o verification/sparse-omission
```

The generated directory contains a manifest plus one baseline/candidate pair per unresolved omission. Each candidate differs from its baseline by one omission. Load both files separately in the pinned Viewer and compare load success, rendering, style source, interaction behavior, counters/scores, and browser-console errors.

Load success alone is not enough to promote a rule. Add an omission to the default serializer only after the behavior controlled by that field is indistinguishable in the pinned Viewer.

The kit includes a private `unselFilterSatur: 1` negative control. Source inspection indicates that omission reconstructs `0`, so the explicit `1` should remain unless direct Viewer testing proves that difference irrelevant in the tested context.

## Version policy

Omission rules are native Viewer behavior and are pinned to the ICC Plus version and source commit. Re-audit the whitelist whenever the Viewer target changes. Do not carry omission rules forward to a new Viewer version by assumption.

## Compiler boundary

Sparse runtime serialization is not source normalization. The compiler remains responsible for semantic transformations such as Requirement hoisting, Row merging, taxonomy pruning, style-intent consolidation, Pick-N derivation, and runtime-ID compaction. ICC Plus Local only removes native serialized values whose omission has already been shown not to change the pinned Viewer's behavior.
