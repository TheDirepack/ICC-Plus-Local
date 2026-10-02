# Large-project normalization and release compaction

This chapter covers structural normalization for large ICC Plus 2 projects. The goal is not to remove mechanics. It is to express the same mechanics at the broadest correct scope, keep the authoring source readable, and avoid repeating data thousands of times in the generated project.

Treat these as compiler/build practices for source-driven projects. Do not hand-edit a generated `project.json` into a second source of truth.

## Normalize semantics before compressing bytes

Prefer changes that make the project model simpler before considering serialization tricks:

1. project-wide styling before local styling,
2. reusable Design Groups before private styling,
3. Row-level visibility before repeating the same hidden Requirement on every Choice,
4. the deepest direct gate instead of every ancestor gate,
5. Row selection limits before pairwise ordinary-Choice exclusion lists,
6. one coherent Row instead of unnecessary one-card Rows,
7. runtime Groups only when something consumes them,
8. compact runtime identities only after the semantic project is stable.

Every normalization pass needs regression tests. A smaller JSON file is not evidence that the project still behaves correctly.

## Styling: broadest native scope first

Use this order for ordinary work:

1. project styling,
2. Row/Choice Design Groups,
3. private Row exceptions,
4. private Choice exceptions,
5. custom CSS only when native ICC Plus styling cannot express the result.

When an ordinary ICC Plus Group already represents a semantic family, link its Design Group through `Group.designGroups` rather than assigning the same Design Group directly to every member. This lets current and future Group members inherit the reusable treatment and avoids repeated per-entity Design Group IDs.

Do not copy a complete project styling object into every Design Group. A Design Group should contain only the properties it actually overrides.

Private styling is appropriate for a genuine one-off. It is not a substitute for a design system.

## Visibility: put the gate as low in the tree as possible

For progressive-reveal projects, a hidden Row already hides the Choices it contains. The normal pattern is therefore:

```text
Species -> Head -> Mouth -> Mouth detail Row
```

The Mouth detail Row should normally require `Mouth`. It should not also require Head, Species, and every earlier navigation choice that was already necessary to make Mouth selectable.

The same rule applies to deeper branches: require the closest direct provider that fully implies the ancestors.

### Promote shared Choice gates to the Row

If every Choice in a multi-Choice Row has the same visibility Requirement, put that Requirement on the Row once and remove it from the children.

Keep a Requirement on an individual Choice when:

- Choices in the same visible Row genuinely have different prerequisites,
- the card should remain visible while selection is unavailable,
- the Requirement is about legality rather than Row visibility,
- or the player needs a visible locked Choice rather than a hidden Row.

Tests should reason about the **effective gate**: Row Requirements plus Choice Requirements. Do not require the same condition to be physically duplicated on every child merely because older output did so.

### Visibility is not cleanup

Hiding a Row does not mean already selected children are automatically deselected. A hidden selected Choice can remain active internally and may reappear if its Row becomes visible again.

If losing a provider must invalidate or remove an existing selection, encode and test cleanup separately. Do not depend on Row hiding to perform deselection.

This distinction is important:

- **visibility** controls what the player can see,
- **availability/legality** controls what may be selected,
- **cleanup** controls what happens to an existing selection when a provider disappears.

## Use native Row selection limits

`allowedChoices == 0` means unlimited. A positive value is a Row maximum.

For ordinary direct Choices:

- use `allowedChoices = 1` for a true radio-style Row,
- use the real finite maximum for Pick N Rows,
- keep 0 only when unlimited selection is intentional.

Do not leave a Row nominally unlimited while implementing “pick one” with every Choice listing all sibling IDs unless the target behavior genuinely needs custom replacement effects.

When a repeatable or generated Row represents several independent slots, set the Row maximum to the maximum number of simultaneously valid slots. Do not collapse a multi-instance Row to 1 just because each individual slot is single-choice.

If two different axes need different limits, keep or split them into separate Rows. Merging a single-select state axis with an independent multi-select modifier axis prevents the Row from expressing either limit cleanly.

### Selectable Addon warning for the 2.10.7 target

Do not assume ordinary Row choice limits correctly enforce selectable Addon radio sets in ICC Plus 2.10.7. Upstream 2.10.8 release notes explicitly include a fix for “Change choices per row could not change addons per row.”

Until the project target is upgraded and verified, keep an explicit, tested Addon exclusion/deactivation mechanism for Addon-only radio sets on 2.10.7. The Creator UI accepts Choice / Group IDs for deactivation, but group-based Addon deactivation should still be treated as target-Viewer behavior that needs a dedicated regression before replacing known-good explicit logic.

## Merge unnecessary one-card Rows conservatively

A one-card Row has real overhead in both layout and Creator-complete JSON. Merge it into a neighboring Row when all of these are true:

- the content belongs to the same player-facing question or tightly coupled section,
- the Rows have compatible effective visibility,
- the single-card Row has no unique instruction or explanation that would be lost,
- the Rows do not need different `allowedChoices` values,
- neither Row has a distinct result/group/button/info role,
- template, width, styling, and generated-detail behavior remain sensible after the merge.

Do not merge merely because two Rows are adjacent. Preserve a separate Row when its header is meaningful, its gate is different, its layout role matters, or combining the Rows would mix independent axes.

For compiler-driven projects, keep a source-owned merge/remap table when tests or generated detail Rows refer to semantic Row identities. Regression tests should follow semantic ownership rather than assuming an old physical Row still exists.

## Keep authoring metadata out of the runtime Group graph

A semantic tag in YAML or another source format does not automatically need to become an ICC Plus runtime Group.

Emit a Group only when the Viewer/runtime uses it for something such as:

- a Requirement,
- result/group Row behavior,
- Design Group inheritance,
- a discount or effect,
- activation/deactivation,
- or another verified group-aware mechanic.

Pruning a Group because “nothing references its ID” is not enough if a reverse link or generated mechanic consumes it. Build a consumer graph and test the compacted artifact.

Keep useful authoring tags in source even when their runtime copies are omitted.

## Separate semantic IDs from compact runtime IDs

Large generated projects may repeat IDs tens of thousands of times through Requirements, Groups, effects, and selection behavior. A source-driven project can keep readable semantic IDs for authoring and emit stable compact IDs for the release artifact.

A safe model is:

- semantic source/test build: `choice_species_regeneration`,
- runtime release ID: a deterministic short token such as `cA1b2C3d`,
- a generated reversible ID map alongside the release.

A type prefix can make compact IDs easier to diagnose, for example `r` for Row, `c` for Choice, `a` for selectable Addon, `g` for Group, and other distinct prefixes for other identity-bearing entities.

### Compact IDs must be deterministic

Do not generate new random IDs on every build. Randomizing release IDs breaks reproducibility, diffs, imported builds, and saved-build compatibility.

The compacting algorithm and its collision handling are part of the release contract. Once a runtime ID has been published, changing the algorithm or mapping is an ID migration even if semantic source IDs remain unchanged.

### Remap every reference-bearing field

Compaction must rewrite identities and every field that references them, including nested Requirements, Groups, effects, activation/deactivation strings, result/group links, Design Group links, Score/Point references where applicable, and any serialized build-facing references.

The safest release gate is:

1. build the readable semantic project,
2. compact identities deterministically,
3. validate the compact project,
4. reverse the map into a comparison copy,
5. compare that copy field-for-field with the semantic project,
6. run representative runtime regressions on the compact artifact or through an ID-aware harness,
7. ship the ID map with internal release records.

Do not use the compact release file as the normal authoring master. It is deliberately less readable.

## Creator-complete overhead is real

ICC Plus Creator-complete files contain many eager/default fields on every Row and Choice. After removing duplicated styles, gates, Groups, and long references, a large amount of remaining JSON may be required/default schema material rather than duplicated author intent.

Do not strip Creator-required or Creator-eager fields only to improve a byte-count metric. Creator compatibility is more important than an artificially small project file.

## Test normalization by behavior, not old physical placement

Structural normalization often invalidates tests that assert where a rule is stored rather than what the player experiences.

Prefer assertions such as:

- the Row is hidden before the direct provider and visible after it,
- the effective Requirement still blocks or allows the intended Choice,
- selecting a second option in a max-1 Row replaces/blocks according to target behavior,
- losing a provider performs the intended cleanup or deliberately preserves hidden state,
- merged content remains reachable and ordered,
- semantic IDs round-trip through runtime compaction.

Update stale tests when the implementation location intentionally changes. Do not weaken the mechanic merely to preserve an obsolete JSON shape assertion.

## Large regression suites

Very large Creator-complete projects can make simulator-heavy monolithic suites slow enough to hide useful results behind a timeout. Keep a complete release gate, but split it into bounded suites when needed.

Distinguish:

- project failures,
- stale assertions after an intentional structural change,
- tool/environment/import failures,
- and timeout/performance failures.

Remove expensive duplicate scenarios only when equivalent coverage already exists elsewhere. Keep a smaller representative regression for the behavior the removed scenario uniquely covered.

## Problems found during large-project normalization

The following are recurring failure modes worth checking explicitly:

- project-wide styling copied privately into hundreds or thousands of entities,
- direct Design Group IDs repeated on every member despite an existing semantic Group,
- ancestor navigation Requirements repeated at every descendant level,
- the same gate copied from a Row onto every Choice,
- `allowedChoices: 0` on Rows that are semantically Pick 1 or Pick N,
- pairwise sibling ID lists used where an ordinary Row maximum is sufficient,
- one-card Rows that add no gate, explanation, or layout value,
- unrelated axes merged into one Row even though they need different limits,
- semantic Groups emitted into runtime JSON with no runtime consumer,
- hidden selected Choices assumed to have been deselected,
- random runtime-ID compaction that changes every build,
- incomplete ID remapping that leaves dangling references,
- editing compact release JSON instead of the readable source,
- stripping Creator-complete defaults for size alone,
- trusting selectable-Addon Row limits on the 2.10.7 target without target-Viewer proof,
- treating local simulator success as official Viewer/browser verification,
- one monolithic regression command obscuring which expensive suite actually failed.

## Normalization checklist

Before accepting a large-project normalization pass:

- [ ] Authoritative source remains readable and canonical.
- [ ] Styling uses project scope and Design Groups before private styling.
- [ ] Hidden descendant Rows use the closest sufficient direct gate.
- [ ] Shared child gates were considered for Row promotion.
- [ ] Mixed-visibility Rows retained the necessary Choice-level gates.
- [ ] Visibility and deselection behavior were tested separately.
- [ ] Every Pick 1 / Pick N Row has an intentional `allowedChoices` value.
- [ ] Selectable Addon exclusivity matches the target Viewer version.
- [ ] One-card Row merges preserve explanations, gates, layout, and limits.
- [ ] Runtime Groups have real consumers.
- [ ] Compact IDs are deterministic and reversible if used.
- [ ] Compact and semantic projects compare equivalently after reverse mapping.
- [ ] Creator-complete validation passes.
- [ ] Representative runtime and save/load paths pass.
- [ ] Official Viewer testing remains a separate release gate.
