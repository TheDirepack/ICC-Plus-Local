# rules

Read this file before changing Points, Scores, Requirements, Groups, selection limits, costs, activation, deactivation, or gameplay effects.

Use `rules` for mechanics. Keep structure in `structure` and presentation in `style`.

## Requirement placement

Encode the rule at the broadest correct runtime scope, but no broader.

- If a hidden Row owns a branch, gate the Row instead of copying the same hide Requirement onto every child.
- Use the closest direct provider that fully implies its ancestors. A Mouth detail Row should normally require Mouth, not Mouth + Head + Species.
- If every Choice in a multi-Choice Row has the same visibility Requirement, promote it to the Row once.
- Keep Choice-level Requirements when Choices inside the same visible Row genuinely differ, when a locked card must stay visible, or when the condition is Choice legality rather than Row visibility.

Visibility is not cleanup. Hiding a Row does not prove previously selected children were deselected. If provider loss must remove or invalidate selected children, encode and test that transition separately.

## Row selection limits

`allowedChoices == 0` is unlimited. Use a positive maximum whenever the Row is semantically Pick 1 / Pick N.

For ordinary direct Choices, prefer the native Row maximum over pairwise sibling exclusion lists when the target behavior matches. For generated multi-instance Rows, set the maximum to the number of simultaneously valid instances rather than forcing the whole Row to one.

Do not combine independent axes into one Row when they require different maxima.

### Selectable Addon caveat on 2.10.7

The current target is ICC Plus 2.10.7. Do not assume Row choice limits can replace selectable-Addon radio logic on this target. Upstream 2.10.8 specifically fixed an issue where changing choices per Row could not change Addons per Row. Keep explicit tested Addon exclusion/deactivation until the target is upgraded and verified.

## Groups

Use runtime Groups when a runtime feature consumes them. Source-only semantic tags do not need runtime Group objects. Before pruning a Group, check Requirements, result/group Rows, Design Group inheritance, discounts/effects, activation/deactivation, and other reverse consumers.

After rule normalization, use `play` to test passing and failing paths, provider loss, row-cap replacement, save/load, and cleanup behavior. Read `../../../docs/cyoa/guide/21-large-project-normalization.md` for the full normalization rules.
