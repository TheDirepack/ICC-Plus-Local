# Troubleshooting and reference rules

## Start with the target version

Do not fix a current ICC Plus 2 project from memory of old ICC behavior.

Record the target Viewer version, reproduce the issue there, and query the current schema for the affected feature.

## Project will not validate

Check the exact validator output. Common causes include missing references, invalid field shapes, stale IDs, and patches that use a path that does not exist.

Use higher-level entity operations when available. For RFC 6902 patches, `replace` requires the path to exist. Use `add` for a missing field.

## Requirement looks correct but behaves incorrectly

Use `inspect` to locate the affected Choice and its authoring-side Requirement data. Reproduce the player path with `play`, using a private `--state` file when the transition spans several actions. If the exact current route for a deeper diagnostic is uncertain, discover it with `reference commands` rather than using a remembered compatibility alias. Then reproduce the same path in the target Viewer.

Inspect:

- Requirement attachment point.
- AND or OR logic.
- Hide behavior.
- Global Requirement nesting.
- State before and after selection.
- Forced Choices.
- Multi-select count.
- Variable update order.
- Score update order.

Runtime order can matter even when the static condition looks right.

## Choice does not deselect correctly

Check whether it is forced active, auto-active, inside a Row with selection rules, dependent on another multi-select Choice, or affected by a Button or function.

Test the target v2 release because several force-active, multi-select, and deselection bugs have been fixed during the 2.x line.

Do not add a workaround for a bug that is already fixed in the target Viewer.

## Scores are wrong

Check:

- Sign convention.
- Conditional Scores.
- Expressions.
- Multi-select multiplication.
- Discounts.
- Minimum or below-zero limits.
- Action order.
- Whether the target release recalculates the expression when the referenced state changes.

Test exact boundaries.

## Viewer layout breaks on phones

First use ICC Plus 2 responsive Choices Per Row controls. Then inspect custom CSS.

Common causes include fixed widths, long unbroken text, oversized images, portrait cards, and selectors that assume desktop DOM geometry.

## External font works locally but not after upload

Check the final URL for CORS errors and failed network requests. External CSS depends on host behavior.

## Backpack image looks wrong

Test the actual target v2 release. Current ICC Plus 2 preloads Backpack images and includes fixes for old download and downscale problems.

Inspect the configured Backpack Rows, card layout, image dimensions, and custom CSS before adding a preload workaround.

## Save appears missing after deployment

Confirm the player is using the same CYOA link. ICC Plus 2 build saves are stored per link.

## Large project is slow to edit

First separate Creator lag, Viewer lag, and slow scripted authoring. They can have different causes.

For Creator lag, disable image rendering in Edit Mode to test whether images dominate the cost. Reduce oversized embedded assets and unnecessary per-Choice overrides.

For Viewer lag, test a representative release build with and without heavy images or custom CSS before blaming the rule system. Then isolate unusually large Rows, deep requirement networks, or repeated dynamic work.

For scripted authoring, inspect batch size and selector breadth. Prefer bounded phase operations over thousands of tiny writes.

Change one suspected cost at a time and measure again. Do not simplify mechanics or visuals based only on a guess about the bottleneck.

## Schema and viewer disagree

Stop authoring the disputed feature through the stale schema. Sync or update the tool snapshot, or handle the field only through a verified route.

Unknown fields surviving a round trip does not prove the tool understands their semantics.

## Old project problem

If the file originated in old ICC or ICC Plus 1.x, do not expand this troubleshooting file with legacy behavior. Use `../legacy-icc-reference/legacy-icc-migration-reference.md`, migrate to a clean ICC Plus 2 target, then troubleshoot the target project here.