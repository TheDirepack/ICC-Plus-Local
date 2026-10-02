# rules

Read this file before changing Points, Scores, Requirements, Groups, selection limits, costs, activation, deactivation, or gameplay effects in a native ICC Plus project.

Use `rules` for explicit mechanics edits. Keep structure in `structure` and presentation in `style`.

## Native Requirement semantics

Requirements may live on Rows, Choices, Addons, and other native entities. ICC Plus Local should preserve and evaluate the Requirements it is given.

For source-driven projects, decisions such as removing ancestor gates or promoting identical Choice Requirements to a Row belong in the source compiler, because they require proof that the higher-level dependency graph preserves semantics. ICC Plus Local should not infer those rewrites from generated JSON.

Visibility is not cleanup. Hiding a Row does not prove previously selected children were deselected. If provider loss must remove or invalidate selected children, encode and test that transition explicitly.

## Row selection limits

`allowedChoices == 0` is unlimited. A positive value is the native Row maximum.

ICC Plus Local preserves and simulates that meaning. It does not infer Pick 1 / Pick N intent from titles, layout, or sibling exclusions. A source compiler that knows the intended cardinality should emit the correct native maximum.

Do not combine independent axes into one Row when they need different maxima unless that structure is an explicit design choice made outside ICC Plus Local.

## Selectable Addons

Do not treat ICC Plus 2.10.8's “Change choices per row could not change addons per row” changelog entry as evidence about `allowedChoices`. The corresponding upstream source change is width handling: selectable Addons use `addonWidth`, while Rows and Choices use `objectWidth`.

Any change from explicit selectable-Addon radio/exclusion logic to another native mechanic needs direct target-Viewer evidence for that mechanic.

## Groups

ICC Plus Local creates, edits, validates, and evaluates native Groups when explicitly requested. Deciding that source taxonomy should be omitted from the runtime Group graph is a compiler/lowering decision, not an automatic `rules` cleanup.

After rules edits, use `play` to test passing and failing paths, provider loss, row-cap replacement, save/load, and cleanup behavior.

Read `../../../docs/COMPILER_BOUNDARY.md` for the source/compiler ownership boundary and `../../../docs/cyoa/guide/21-large-project-normalization.md` for compiler-side normalization guidance.
