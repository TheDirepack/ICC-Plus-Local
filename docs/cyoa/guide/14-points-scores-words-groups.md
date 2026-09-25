# ICC Plus 2 Points, Scores, Words, and Groups

## Point Types

Use Point Types for numeric state the player or rules need to track.

Examples include currency, power, crew capacity, reputation, danger, or a hidden score used for results.

ICC Plus 2 supports integer and floating-point Point Types. Choose the type that matches the mechanic. Do not use floating point when the project only spends whole numbers.

## Starting values

A starting value should match the way the project explains the resource.

If the player starts with 20 points but must immediately spend 8 on a mandatory package, consider making that package free or starting with 12 usable points instead. The displayed economy should match the real decision space.

## Scores

Scores change Point Types.

Keep score direction consistent. Decide whether a positive displayed number means a gain or a cost and use one convention across the project unless a section has a clear reason to differ.

ICC Plus 2 has newer score controls, expressions, conditional behavior, and multi-select interactions. Query the target schema and test the target viewer before using a complex combination.

For ordinary Choice selection, linked activation/deactivation and Requirement cleanup run before point multiply/divide/set effects. Repeat-counter steps do not run those ordinary point transforms. A `belowZeroNotAllowed` affordability check occurs before a later set transform, so the set can leave the Point Type below zero without retroactively rejecting the selection.

## Formula use

Use expressions when they model a real relationship that would be hard to maintain as fixed values.

Do not replace a simple fixed cost with a formula. Formulas add another place for state order and recalculation bugs.

If a formula reads a Point Type that can change after selection, test whether the target viewer recalculates at the time the design expects.

## Minimums and maximums

If a Point Type must not cross a boundary, use supported engine controls where practical and test the boundary through every action that can change it.

A limit that works for normal Choice selection may still fail through a Row Button, function, or unusual score interaction in a specific release.

## Words

Words hold text that can be reused or changed. Use them for player names, chosen labels, dynamic terms, or repeated project text when the feature adds value.

Do not turn static prose into hundreds of Words merely to centralize text. Use them when the text needs runtime behavior or reuse that materially helps maintenance.

## Groups

Use Groups for behavior that targets a set of Rows or Choices.

Name Groups by purpose, not by an arbitrary number.

Examples:

- `group_fire_spells`
- `group_party_members`
- `group_selected_loadout`

Keep membership current when content moves or is cloned.

For `selFromGroups` Requirements, overlapping membership is counted per requested Group. A single selected Choice can therefore contribute more than once when it belongs to more than one Group in the Requirement.

## Design Groups

Use Design Groups for reusable native styling shared by Rows or Choices. Assign them directly when the visual family is explicit, or link a Design Group through a normal ICC Plus Group when membership in that Group should carry the style automatically.

Use the broadest native scope that fits the design. Put site-wide defaults in project styling, use Design Groups for reusable visual families, and reserve private Row or Choice styling for genuine one-off exceptions. Use custom CSS only when native ICC Plus styling cannot express the result.