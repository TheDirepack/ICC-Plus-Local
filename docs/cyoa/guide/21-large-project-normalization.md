# Large-project normalization and release compaction

This chapter covers compiler/build normalization for large source-driven ICC Plus 2 projects. It is not a description of transformations that ICC Plus Local should infer and apply to arbitrary native projects.

Keep the boundary explicit:

- the source compiler owns semantic normalization and release compaction;
- ICC Plus Local owns native ICC Plus validation, serialization, compatibility behavior, and local simulation;
- generated `project.json` is output, not a second authoring source.

See `../../COMPILER_BOUNDARY.md` for the ownership boundary.

## Normalize semantics before bytes

A compiler should simplify its semantic model before considering serialization tricks. A useful order is:

1. project-wide styling before repeated local styling;
2. reusable Design Groups before repeated private styling;
3. the deepest sufficient visibility gate instead of every ancestor gate;
4. a shared Row gate instead of the same hidden Requirement on every child when semantics are identical;
5. native Row selection limits when the source really means Pick 1 / Pick N;
6. one coherent Row instead of unnecessary one-card Rows when the layout and mechanics are compatible;
7. runtime Groups only when the native project actually consumes them;
8. deterministic compact runtime identities only after the semantic project is stable.

ICC Plus Local should not perform these rewrites on its own. It can validate the native project emitted by the compiler and exercise its behavior.

Every normalization pass needs regression tests. A smaller JSON file is not evidence that the project still behaves correctly.

## Styling normalization belongs in the compiler

For native ICC Plus authoring, the preferred scope is:

1. project styling;
2. Row/Choice Design Groups;
3. private Row exceptions;
4. private Choice exceptions;
5. custom CSS only when native ICC Plus styling cannot express the result.

A source compiler may use that ordering to remove duplicated author intent. When a semantic family is already represented by an ordinary ICC Plus Group, the compiler can link a Design Group through `Group.designGroups` instead of assigning the same Design Group directly to every member.

Do not copy a complete project styling object into every Design Group. A Design Group should contain only the properties it overrides.

This is a lowering decision. ICC Plus Local should apply and validate the native styling graph it receives rather than guessing which repeated styles are semantically equivalent.

## Visibility normalization belongs in the compiler

For progressive reveal, a hidden Row already hides its contained Choices. A source dependency chain such as:

```text
Species -> Head -> Mouth -> Mouth detail Row
```

usually means the compiler can gate the Mouth detail Row on `Mouth` alone if the source graph proves `Mouth` already implies the required ancestors.

Do not remove ancestor Requirements merely because they look repetitive in generated JSON. The compiler must prove they are redundant in the source dependency graph.

### Shared child gates

If every Choice in a Row has the same visibility Requirement and the player-facing semantics are identical, the compiler may promote that Requirement to the Row once.

Keep a Requirement on an individual Choice when:

- sibling Choices genuinely have different prerequisites;
- the card should remain visible while selection is unavailable;
- the Requirement is about legality rather than Row visibility;
- or the player needs a visible locked Choice rather than a hidden Row.

Regression tests should assert effective behavior, not merely the old physical storage location of a Requirement.

### Hidden Rows are not cleanup

Hiding a Row does not automatically deselect already selected children. A hidden selected Choice can remain active internally and may reappear if its Row becomes visible again.

Treat these as separate mechanics:

- **visibility** controls what the player sees;
- **availability/legality** controls what may be selected;
- **cleanup** controls what happens to an existing selection when a provider disappears.

If provider loss must invalidate child selections, the compiler must emit an explicit native cleanup mechanism and test it. ICC Plus Local should faithfully simulate the emitted native behavior rather than inventing cleanup from Row visibility.

## Native Row limits: compiler intent, local semantics

In ICC Plus, `allowedChoices == 0` means unlimited. A positive value is a Row maximum.

ICC Plus Local should preserve, validate, and simulate that native meaning. It should not infer that a Row was intended to be radio-style because of its title, layout, or sibling exclusions.

When the higher-level source says Pick 1 or Pick N, the compiler should emit the intended positive `allowedChoices` value where native Row limits are the correct mechanic.

For repeatable or generated Rows representing independent slots, use the maximum number of simultaneously valid slots. Do not collapse a multi-instance Row to 1 merely because each individual slot is single-choice.

If two axes need different limits, keep them separate. Merging a single-select state axis with an independent multi-select modifier axis can make either limit impossible to express correctly.

### ICC Plus 2.10.8 Addon changelog correction

Upstream 2.10.8 says “Change choices per row could not change addons per row.” The corresponding source diff changes width application: selectable Addons use `addonWidth`, while Rows and Choices use `objectWidth`.

That is a layout-width fix. It is not evidence that `allowedChoices` selection-cap behavior changed for selectable Addons.

Do not cite the 2.10.8 changelog entry as proof that Row selection limits can replace selectable-Addon radio/exclusion logic. Any such replacement needs direct target-Viewer evidence for the actual mechanic being changed.

## Merge Rows only in the compiler

A one-card Row has real layout and Creator-complete overhead, but physical Row structure can also carry meaning. Merge a one-card Row only when the compiler can prove that:

- the content belongs to the same player-facing question or tightly coupled section;
- the Rows have compatible effective visibility;
- no unique instruction or explanation is lost;
- the Rows do not require different `allowedChoices` values;
- neither Row has a distinct result/group/button/info role;
- template, width, styling, and generated-detail behavior remain sensible.

Do not merge merely because Rows are adjacent. Preserve a separate Row when its header, gate, layout role, result behavior, or selection axis is meaningful.

Keep source-owned remap information when tests or generated detail Rows refer to semantic Row identities. Tests should follow semantic ownership rather than assuming an old physical Row still exists.

ICC Plus Local should support the explicit native Row edits it is asked to perform. It should not auto-merge Rows as a size optimization.

## Keep authoring metadata out of the runtime Group graph

A semantic tag in YAML or another source format does not automatically need to become an ICC Plus runtime Group.

The compiler should emit a Group only when the native project consumes it for something such as:

- a Requirement;
- result/group Row behavior;
- Design Group inheritance;
- a discount or effect;
- activation/deactivation;
- or another verified group-aware mechanic.

Pruning a Group merely because nothing references its ID directly is unsafe if a reverse link or generated mechanic consumes it. Build a consumer graph and test the compacted artifact.

Keep useful authoring taxonomy in source even when its runtime copy is omitted.

ICC Plus Local should validate emitted Groups and references, not decide whether source taxonomy was intended to exist at runtime.

## Runtime ID compaction belongs in the compiler/release pipeline

Large generated projects may repeat IDs through Requirements, Groups, effects, and selection behavior. A source-driven release pipeline may keep readable semantic IDs for authoring while emitting shorter stable runtime IDs.

A safe model is:

- semantic source/test ID: `choice_species_regeneration`;
- stable runtime release ID: a deterministic short token such as `cA1b2C3d`;
- generated reversible ID map retained with release records.

A type prefix can make compact IDs easier to diagnose, for example `r` for Row, `c` for Choice, `a` for selectable Addon, and `g` for Group.

### IDs must be deterministic and stable

Never generate new random runtime IDs on every build. That breaks reproducibility, useful diffs, imported builds, and save compatibility.

The compaction algorithm, collision handling, and published mapping are part of the release contract. Changing them after release is an ID migration even when semantic source IDs remain unchanged.

### Remap every reference-bearing field

Compaction requires a complete identity/reference graph. The compiler must rewrite identities and every field that references them, including nested Requirements, Groups, effects, activation/deactivation strings, result/group links, Design Group links, Score/Point references where applicable, and serialized build-facing references.

A strong release gate is:

1. build the readable semantic native project;
2. compact identities deterministically;
3. validate the compact project with ICC Plus Local;
4. reverse the map into a comparison copy;
5. compare that copy field-for-field with the semantic native project;
6. run representative runtime regressions on the compact artifact or through an ID-aware harness;
7. retain the mapping with release records.

Do not use compact release JSON as the normal authoring master.

ICC Plus Local may provide reference-integrity validation and project serialization, but it should not invent compact IDs or decide which public identities can safely change.

## Creator-complete overhead is real

ICC Plus Creator-complete files contain many eager/default fields on every Row and Choice. After compiler-side deduplication, a large amount of remaining JSON may still be official native structure rather than duplicated author intent.

Do not strip Creator-required or Creator-eager fields merely to improve a byte-count metric. Creator compatibility is more important than an artificially small project file.

The correct optimization boundary is earlier: remove redundant semantic authoring data before generation, then let ICC Plus Local hydrate/validate the native result.

## Test normalization by behavior

Structural normalization often invalidates tests that assert where a rule is stored rather than what the player experiences.

Prefer assertions such as:

- the Row is hidden before the direct provider and visible after it;
- the effective Requirement still blocks or allows the intended Choice;
- selecting a second option in a max-1 Row follows target behavior;
- losing a provider performs the intended cleanup or deliberately preserves hidden state;
- merged content remains reachable and ordered;
- semantic IDs round-trip through runtime compaction.

Update stale structural assertions when the compiler intentionally changes physical layout. Do not weaken the mechanic merely to preserve an obsolete JSON shape assertion.

## Large regression suites

Very large Creator-complete projects can make simulator-heavy monolithic suites slow enough to hide useful results behind a timeout. Keep a complete release gate, but split it into bounded suites when needed.

Distinguish:

- native project failures;
- stale assertions after an intentional compiler transformation;
- tool/environment/import failures;
- simulator-performance or overall timeout failures.

Remove expensive duplicate scenarios only when equivalent coverage already exists elsewhere. Keep a representative regression for behavior that would otherwise become untested.

A timeout is not evidence of semantic failure, and a passing local simulator is not browser proof.

## Local simulation is not target-Viewer proof

ICC Plus Local is useful for deterministic native regression, but the official target Viewer remains authoritative for browser presentation and version-specific behavior that has not been source-differentially reproduced.

Keep release evidence explicit about what was checked locally and what was checked in the official Creator/Viewer. Do not turn local success into an unsupported browser-parity claim.

## Normalization checklist

Before accepting a compiler normalization pass:

- [ ] Authoritative source remains readable and canonical.
- [ ] ICC Plus Local was not made responsible for inferring source-level normalization intent.
- [ ] Styling uses the broadest correct native scope before private duplication.
- [ ] Redundant gates were removed only when the source dependency graph proves redundancy.
- [ ] Shared child gates were promoted only when player-facing semantics are preserved.
- [ ] Visibility and cleanup were tested separately.
- [ ] Pick 1 / Pick N source intent emits an intentional native `allowedChoices` value.
- [ ] Independent axes were not merged into a Row that cannot express their limits.
- [ ] Selectable-Addon behavior is justified by the actual target mechanic, not the misleading 2.10.8 changelog wording.
- [ ] Row merges preserve explanations, gates, layout, and limits.
- [ ] Runtime Groups have real native consumers.
- [ ] Compact IDs are deterministic, stable, and reversible if used.
- [ ] Every reference-bearing field participates in compaction/remapping.
- [ ] Compact and semantic projects compare equivalently after reverse mapping.
- [ ] Creator-complete validation passes.
- [ ] Representative local runtime and save/load paths pass.
- [ ] Test timeouts are distinguished from semantic failures.
- [ ] Official Viewer verification remains a separate release gate where required.
